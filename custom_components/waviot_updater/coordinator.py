# coordinator.py
import aiohttp
from datetime import datetime, timedelta, timezone
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem and energy data safely for last 30 days."""

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

            except Exception as e:
                _LOGGER.error("Exception fetching modem info: %s", e)
                raise UpdateFailed(f"Failed fetching modem info: {e}")

            # --- Energy readings (last 30 days) ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                now = datetime.now(tz=timezone.utc)
                thirty_days_ago = now - timedelta(days=30)

                url = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                    f"&from={int(thirty_days_ago.timestamp())}&to={int(now.timestamp())}"
                )

                readings = []
                async with session.get(url) as resp:
                    ch_data = await resp.json()
                    values = ch_data.get("values", {}) if ch_data else {}
                    for ts, val in values.items():
                        try:
                            ts_sec = int(ts)
                            if ts_sec > 1e12:
                                ts_sec //= 1000
                            if ts_sec >= int(thirty_days_ago.timestamp()):
                                readings.append((ts_sec, float(val)))
                        except Exception as ex:
                            _LOGGER.warning("Skipping invalid reading ts=%s val=%s (%s)", ts, val, ex)

                readings.sort(key=lambda x: x[0])
                self.data["readings"] = readings

            except Exception as e:
                _LOGGER.error("Exception fetching channel values: %s", e)
                self.data["readings"] = []

            # --- Compute latest, hourly, daily usage ---
            self._compute_usage()

        return self.data

    def _compute_usage(self):
        """Compute latest, hourly, and daily usage only."""
        readings = self.data.get("readings", [])
        if not readings:
            self._init_empty_data()
            return

        now = datetime.now(tz=timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        latest_timestamp, latest_value = readings[-1]
        self.data["latest"] = latest_value
        self.data["last_update"] = datetime.fromtimestamp(latest_timestamp, tz=timezone.utc)

        # Hourly usage
        hourly_val = next(
            (v for t, v in reversed(readings) if datetime.fromtimestamp(t, tz=timezone.utc) <= one_hour_ago),
            None
        )
        self.data["hourly"] = round(latest_value - hourly_val, 3) if hourly_val is not None else None

        # Daily usage
        daily_val = next(
            (v for t, v in reversed(readings) if datetime.fromtimestamp(t, tz=timezone.utc) <= one_day_ago),
            None
        )
        self.data["daily"] = round(latest_value - daily_val, 3) if daily_val is not None else None

    def _init_empty_data(self):
        """Initialize empty data dict."""
        self.data.update({
            "battery": None,
            "temperature": None,
            "readings": [],
            "latest": None,
            "hourly": None,
            "daily": None,
            "last_update": None,
        })
