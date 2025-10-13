import aiohttp
from datetime import datetime, timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem and energy data."""

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
        """Fetch modem info and energy channel safely."""
        async with aiohttp.ClientSession() as session:
            # --- Modem info ---
            try:
                url = f"{BASE_URL}modem/info/?id={self.modem_id}&key={self.api_key}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Modem info HTTP {resp.status}")
                    info = await resp.json()
                    if not info or info.get("status") != "ok":
                        raise UpdateFailed(f"Modem info status invalid: {info}")
                    modem = info.get("modem")
                    if not modem:
                        raise UpdateFailed(f"No 'modem' data in response: {info}")

                    # Battery (cast string to float)
                    battery_raw = modem.get("battery")
                    self.data["battery"] = float(battery_raw) if battery_raw is not None else None

                    # Temperature
                    self.data["temperature"] = modem.get("temperature")
            except Exception as e:
                raise UpdateFailed(f"Failed fetching modem info: {e}")

            # --- Energy channel: electro_ac_p_lsum_t1 ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                url = f"{BASE_URL}data/get_modem_channel_values/?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Channel info HTTP {resp.status}")
                    ch_data = await resp.json()
                    if not ch_data or ch_data.get("status") != "ok":
                        raise UpdateFailed(f"Channel data status invalid: {ch_data}")

                    values = ch_data.get("values", {})
                    readings = []
                    for ts, val in values.items():
                        try:
                            readings.append((int(ts), float(val)))
                        except Exception:
                            continue
                    readings.sort(key=lambda x: x[0])
                    self.data["readings"] = readings
            except Exception as e:
                raise UpdateFailed(f"Failed fetching channel values: {e}")

            # --- Compute usage metrics ---
            self._compute_usage()

        return self.data

    def _compute_usage(self):
        """Compute hourly, daily, current & previous month usage."""
        readings = self.data.get("readings", [])
        if not readings:
            self.data.update({
                "latest": None,
                "hourly": None,
                "daily": None,
                "month_current": None,
                "month_previous": None,
                "last_update": None,
            })
            return

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        latest_timestamp, latest_value = readings[-1]
        latest_dt = datetime.fromtimestamp(latest_timestamp)

        self.data["latest"] = latest_value
        self.data["last_update"] = latest_dt.isoformat()

        # Hourly usage
        hourly_val = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) <= one_hour_ago), None)
        self.data["hourly"] = round(latest_value - hourly_val, 3) if hourly_val is not None else None

        # Daily usage
        daily_val = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) <= one_day_ago), None)
        self.data["daily"] = round(latest_value - daily_val, 3) if daily_val is not None else None

        # Monthly usage
        month_start = datetime(now.year, now.month, 1)
        prev_month = month_start - timedelta(days=1)
        prev_month_start = datetime(prev_month.year, prev_month.month, 1)

        val_current_month = next((v for t, v in readings if datetime.fromtimestamp(t) >= month_start), None)
        val_prev_month = next((v for t, v in readings if prev_month_start <= datetime.fromtimestamp(t) < month_start), None)

        self.data["month_current"] = round(latest_value - val_current_month, 3) if val_current_month else None
        self.data["month_previous"] = round(val_current_month - val_prev_month, 3) if val_prev_month else None
