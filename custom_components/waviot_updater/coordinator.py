# coordinator.py - Fetches WAVIoT modem data for the last 3 months
import aiohttp
from datetime import datetime, timedelta, timezone
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem and energy data safely."""

    def __init__(self, hass, api_key, modem_id):
        self.hass = hass
        self.api_key = api_key
        self.modem_id = modem_id
        self.data = {}
        super().__init__(
            hass,
            _LOGGER,
            name=f"WAVIoT Modem {modem_id}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch modem info and channel readings safely."""
        if self.data is None:
            self.data = {}

        async with aiohttp.ClientSession() as session:
            # --- Modem info ---
            try:
                url = f"{BASE_URL}modem/info/?id={self.modem_id.lower()}&key={self.api_key}"
                _LOGGER.debug("Fetching modem info: %s", url)
                async with session.get(url) as resp:
                    info = await resp.json()
                modem = info.get("modem") if info else None
                if not modem:
                    _LOGGER.warning("No modem data returned from API")
                    self._init_empty_data()
                    return self.data

                battery_raw = modem.get("battery")
                temperature = modem.get("temperature")
                self.data["battery"] = float(battery_raw) if battery_raw is not None else None
                self.data["temperature"] = temperature
                _LOGGER.debug("Battery: %s, Temperature: %s", self.data["battery"], temperature)

            except Exception as e:
                _LOGGER.error("Exception fetching modem info: %s", e)
                raise UpdateFailed(f"Failed fetching modem info: {e}")

            # --- Energy readings ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                now = datetime.now(tz=timezone.utc)
                three_months_ago = now - timedelta(days=90)  # only last 3 months

                url = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                    f"&from={int(three_months_ago.timestamp())}&to={int(now.timestamp())}"
                )
                _LOGGER.debug("Fetching readings for last 3 months: %s", url)

                readings = []
                async with session.get(url) as resp:
                    ch_data = await resp.json()
                    values = ch_data.get("values", {}) if ch_data else {}
                    for ts, val in values.items():
                        try:
                            ts_sec = int(ts)
                            if ts_sec > 1e12:  # milliseconds → seconds
                                ts_sec //= 1000
                            readings.append((ts_sec, float(val)))
                        except Exception as ex:
                            _LOGGER.warning("Skipping invalid reading ts=%s val=%s (%s)", ts, val, ex)

                readings.sort(key=lambda x: x[0])
                self.data["readings"] = readings

            except Exception as e:
                _LOGGER.error("Exception fetching channel values: %s", e)
                self.data["readings"] = []

            # --- Compute latest metric only ---
            self._compute_latest()

        return self.data

    def _compute_latest(self):
        """Compute only the latest reading value."""
        if self.data is None:
            self.data = {}

        readings = self.data.get("readings", [])
        if not readings:
            _LOGGER.debug("No readings available to compute latest value.")
            self._init_empty_data()
            return

        latest_timestamp, latest_value = readings[-1]
        latest_dt = datetime.fromtimestamp(latest_timestamp, tz=timezone.utc)
        self.data["latest"] = latest_value
        self.data["last_update"] = latest_dt

        _LOGGER.debug("Latest reading computed: %s at %s", latest_value, latest_dt)

    def _init_empty_data(self):
        """Initialize empty data dict."""
        self.data.update({
            "battery": None,
            "temperature": None,
            "readings": [],
            "latest": None,
            "last_update": None,
        })
