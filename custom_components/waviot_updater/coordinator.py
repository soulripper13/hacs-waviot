# coordinator.py
import aiohttp
from datetime import datetime, timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem data for the last 30 days."""

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
        """Fetch modem info and energy readings."""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)

        async with aiohttp.ClientSession() as session:
            # --- Modem info ---
            try:
                url = f"{BASE_URL}modem/info/?id={self.modem_id.lower()}&key={self.api_key}"
                async with session.get(url) as resp:
                    info = await resp.json()
                modem = info.get("modem") if info else {}
                self.data["battery"] = float(modem.get("battery")) if modem.get("battery") else None
                self.data["temperature"] = modem.get("temperature")
            except Exception as e:
                raise UpdateFailed(f"Failed fetching modem info: {e}")

            # --- Energy readings (last 30 days) ---
            try:
                url = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel=electro_ac_p_lsum_t1"
                    f"&key={self.api_key}&from={int(thirty_days_ago.timestamp())}&to={int(now.timestamp())}"
                )
                async with session.get(url) as resp:
                    ch_data = await resp.json()
                values = ch_data.get("values", {}) if ch_data else {}

                readings = []
                for ts, val in values.items():
                    try:
                        ts_int = int(ts)
                        if ts_int > 1e12:  # milliseconds → seconds
                            ts_int //= 1000
                        readings.append((ts_int, float(val)))
                    except Exception:
                        continue
                readings.sort(key=lambda x: x[0])
                self.data["readings"] = readings

            except Exception as e:
                _LOGGER.warning("Failed fetching readings: %s", e)
                self.data["readings"] = []

            # --- Compute usage ---
            self._compute_usage()

        return self.data

    def _compute_usage(self):
        """Compute latest, hourly, daily usage."""
        readings = self.data.get("readings", [])
        if not readings:
            self.data.update({"latest": None, "hourly": None, "daily": None, "last_update": None})
            return

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        latest_ts, latest_val = readings[-1]
        self.data["latest"] = latest_val
        self.data["last_update"] = datetime.fromtimestamp(latest_ts)

        hourly_val = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) <= one_hour_ago), None)
        self.data["hourly"] = round(latest_val - hourly_val, 3) if hourly_val is not None else None

        daily_val = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) <= one_day_ago), None)
        self.data["daily"] = round(latest_val - daily_val, 3) if daily_val is not None else None
