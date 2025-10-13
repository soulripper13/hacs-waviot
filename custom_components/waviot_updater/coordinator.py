import aiohttp
from datetime import datetime, timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
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
        """Fetch data from WAVIoT API"""
        async with aiohttp.ClientSession() as session:
            # --- Modem info (battery, temperature) ---
            try:
                url = f"{BASE_URL}modem/info/?id={self.modem_id}&key={self.api_key}"
                async with session.get(url) as resp:
                    info = await resp.json()
                    modem = info.get("modem", {})
                    self.data["battery"] = modem.get("battery")
                    self.data["temperature"] = modem.get("temperature")
            except Exception as e:
                raise UpdateFailed(f"Failed fetching modem info: {e}")

            # --- Energy channel ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                url = f"{BASE_URL}data/get_modem_channel_values/?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                async with session.get(url) as resp:
                    ch_data = await resp.json()
                    values = ch_data.get("values", {})
                    # Convert keys to sorted list
                    readings = sorted(((int(k), float(v)) for k,v in values.items()), key=lambda x: x[0])
                    self.data["readings"] = readings
            except Exception as e:
                raise UpdateFailed(f"Failed fetching channel values: {e}")

            # --- Compute daily/hourly/monthly usage ---
            self._compute_usage()

        return self.data

    def _compute_usage(self):
        readings = self.data.get("readings", [])
        if not readings:
            return

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        latest_timestamp, latest_value = readings[-1]
        latest_dt = datetime.fromtimestamp(latest_timestamp)

        self.data["latest"] = latest_value
        self.data["last_update"] = latest_dt.isoformat()

        # Hourly usage
        hourly_val = next((v for t,v in reversed(readings) if datetime.fromtimestamp(t) <= one_hour_ago), None)
        self.data["hourly"] = round(latest_value - hourly_val, 3) if hourly_val is not None else None

        # Daily usage
        daily_val = next((v for t,v in reversed(readings) if datetime.fromtimestamp(t) <= one_day_ago), None)
        self.data["daily"] = round(latest_value - daily_val, 3) if daily_val is not None else None

        # Monthly usage (current & previous)
        month_start = datetime(now.year, now.month, 1)
        prev_month = month_start - timedelta(days=1)
        prev_month_start = datetime(prev_month.year, prev_month.month, 1)

        val_current = next((v for t,v in readings if datetime.fromtimestamp(t) >= month_start), None)
        val_prev = next((v for t,v in readings if prev_month_start <= datetime.fromtimestamp(t) < month_start), None)

        self.data["month_current"] = round(latest_value - val_current, 3) if val_current else None
        self.data["month_previous"] = round(val_current - val_prev, 3) if val_prev else None
