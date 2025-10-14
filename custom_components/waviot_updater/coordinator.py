# coordinator.py
import aiohttp
import logging
from datetime import datetime, timedelta, timezone
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.dt import as_local, utcnow
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

CHANNEL_ID = "electro_ac_p_lsum_t1"

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem and energy data for the last 30 days."""

    def __init__(self, hass, api_key: str, modem_id: str):
        self.hass = hass
        self.api_key = api_key
        self.modem_id = modem_id
        self.data: dict = {}
        super().__init__(
            hass,
            _LOGGER,
            name=f"WAVIoT Modem {modem_id}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch modem info and channel readings safely."""
        # ensure data is a dict
        if self.data is None:
            self.data = {}

        async with aiohttp.ClientSession() as session:
            # --- Modem info ---
            try:
                # correct endpoint for modem info (confirmed)
                url = f"{BASE_URL}modem/info/?id={self.modem_id.lower()}&key={self.api_key}"
                _LOGGER.debug("Fetching modem info: %s", url_info)
                async with session.get(url_info) as resp:
                    # If the server returns HTML or an error status, this will raise
                    info = await resp.json()
                modem = info.get("modem") if info else None
                if not modem:
                    _LOGGER.warning("No modem info returned")
                    self._init_empty_data()
                    return self.data

                # battery may be str/number; keep as float if possible
                battery_raw = modem.get("battery")
                battery_val = float(battery_raw) if battery_raw is not None else None
                temperature = modem.get("temperature")

                self.data.update({
                    "battery": battery_val,
                    "temperature": temperature,
                })
                _LOGGER.debug("Modem info battery=%s temperature=%s", battery_val, temperature)

            except Exception as exc:
                _LOGGER.error("Error fetching modem info: %s", exc)
                # Keep existing data if available, but surface UpdateFailed so coordinator retries
                raise UpdateFailed(f"Failed fetching modem info: {exc}") from exc

            # --- Energy readings (last 30 days) ---
            try:
                now_utc = utcnow()
                thirty_days_ago_utc = now_utc - timedelta(days=30)

                url_values = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel={CHANNEL_ID}&key={self.api_key}"
                    f"&from={int(thirty_days_ago_utc.timestamp())}&to={int(now_utc.timestamp())}"
                )
                _LOGGER.debug("Fetching readings: %s", url_values)

                readings = []
                async with session.get(url_values) as resp:
                    ch_data = await resp.json()
                values = ch_data.get("values", {}) if ch_data else {}

                for ts, val in values.items():
                    try:
                        ts_int = int(ts)
                        # convert ms -> s if necessary
                        if ts_int > 1e12:
                            ts_int //= 1000
                        # store tuple (utc_timestamp_seconds, float_value)
                        readings.append((ts_int, float(val)))
                    except Exception as ex:
                        _LOGGER.debug("Skipping invalid reading ts=%s val=%s (%s)", ts, val, ex)

                readings.sort(key=lambda x: x[0])

                # Keep readings *internally* only; do not expose huge attributes.
                # We keep last 30 days only (API already requested that).
                self.data["readings"] = readings

            except Exception as exc:
                _LOGGER.warning("Failed fetching readings: %s", exc)
                # If we fail to fetch readings, do not overwrite existing useful data
                self.data.setdefault("readings", [])

            # --- Compute usage metrics (convert timestamps to HA server time) ---
            self._compute_usage()

        return self.data

    def _compute_usage(self):
        """Compute latest, hourly, and daily usage using HA server local time."""
        readings = self.data.get("readings", [])
        if not readings:
            # initialize keys so sensors are available
            self.data.update({
                "latest": None,
                "hourly": None,
                "daily": None,
                "last_update": None,
            })
            return

        # Use HA server local time for comparisons
        now_local = as_local(datetime.now(timezone.utc))
        one_hour_ago_local = now_local - timedelta(hours=1)
        one_day_ago_local = now_local - timedelta(days=1)

        # Latest reading is last in list (API returns cumulative kWh)
        latest_ts_utc, latest_value = readings[-1]
        # convert to local datetime
        last_update_local = as_local(datetime.fromtimestamp(latest_ts_utc, tz=timezone.utc))

        # latest cumulative total (kWh)
        self.data["latest"] = latest_value
        self.data["last_update"] = last_update_local

        # find last reading <= one_hour_ago_local
        hourly_prev = None
        for ts, val in reversed(readings):
            ts_local = as_local(datetime.fromtimestamp(ts, tz=timezone.utc))
            if ts_local <= one_hour_ago_local:
                hourly_prev = val
                break
        self.data["hourly"] = round(latest_value - hourly_prev, 3) if hourly_prev is not None else None

        # find last reading <= one_day_ago_local
        daily_prev = None
        for ts, val in reversed(readings):
            ts_local = as_local(datetime.fromtimestamp(ts, tz=timezone.utc))
            if ts_local <= one_day_ago_local:
                daily_prev = val
                break
        self.data["daily"] = round(latest_value - daily_prev, 3) if daily_prev is not None else None

        _LOGGER.debug("Computed usage latest=%s hourly=%s daily=%s", self.data["latest"], self.data["hourly"], self.data["daily"])

    def _init_empty_data(self):
        """Initialize empty/default data keys."""
        self.data.update({
            "battery": None,
            "temperature": None,
            "readings": [],
            "latest": None,
            "hourly": None,
            "daily": None,
            "last_update": None,
        })
