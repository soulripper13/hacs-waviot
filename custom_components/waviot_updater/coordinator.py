# coordinator.py - Fixed monthly usage calculation to use last reading before period boundaries for more accurate cumulative differences
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
        # Safety check to ensure self.data is a dict
        if self.data is None:
            self.data = {}
        async with aiohttp.ClientSession() as session:
            # --- Modem info ---
            try:
                url = f"{BASE_URL}modem/info/?id={self.modem_id.lower()}&key={self.api_key}"
                _LOGGER.debug("Fetching modem info from URL: %s", url)
                async with session.get(url) as resp:
                    _LOGGER.debug("HTTP status: %s", resp.status)
                    text = await resp.text()
                    _LOGGER.debug("Raw response text: %s", text)
                    try:
                        info = await resp.json()
                        _LOGGER.debug("Parsed JSON: %s", info)
                    except Exception as e:
                        _LOGGER.error("JSON parsing failed: %s", e)
                        raise UpdateFailed(f"Failed parsing modem info JSON: {e}")
                    modem = info.get("modem") if info else None
                    if not modem:
                        _LOGGER.warning("No modem data returned from API")
                        self.data.update({
                            "battery": None,
                            "temperature": None,
                            "readings": [],
                            "latest": None,
                            "hourly": None,
                            "daily": None,
                            "month_current": None,
                            "month_previous": None,
                            "last_update": None,
                        })
                        return self.data
                    battery_raw = modem.get("battery")
                    temperature = modem.get("temperature")
                    self.data["battery"] = float(battery_raw) if battery_raw is not None else None
                    self.data["temperature"] = temperature
                    _LOGGER.debug("Battery: %s, Temperature: %s", self.data["battery"], temperature)
            except Exception as e:
                _LOGGER.error("Exception fetching modem info: %s", e)
                raise UpdateFailed(f"Failed fetching modem info: {e}")
            # --- Energy channel: electro_ac_p_lsum_t1 ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                url = f"{BASE_URL}data/get_modem_channel_values/?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                _LOGGER.debug("Fetching channel data from URL: %s", url)
                async with session.get(url) as resp:
                    _LOGGER.debug("Channel HTTP status: %s", resp.status)
                    text = await resp.text()
                    _LOGGER.debug("Raw channel response: %s", text)
                    try:
                        ch_data = await resp.json()
                        _LOGGER.debug("Parsed channel JSON: %s", ch_data)
                    except Exception as e:
                        _LOGGER.error("JSON parsing failed for channel: %s", e)
                        self.data["readings"] = []
                        return self.data
                    values = ch_data.get("values", {}) if ch_data else {}
                    readings = []
                    for ts, val in values.items():
                        try:
                            readings.append((int(ts), float(val)))
                        except Exception as ex:
                            _LOGGER.warning("Skipping invalid reading ts=%s val=%s (%s)", ts, val, ex)
                    readings.sort(key=lambda x: x[0])
                    self.data["readings"] = readings
            except Exception as e:
                _LOGGER.error("Exception fetching channel values: %s", e)
                self.data["readings"] = []
            # --- Compute usage metrics ---
            self._compute_usage()
        return self.data
    def _compute_usage(self):
        """Compute latest, hourly, daily, current & previous month usage."""
        # Additional safety check
        if self.data is None:
            self.data = {}
        readings = self.data.get("readings", [])
        if not readings:
            _LOGGER.debug("No readings available to compute usage.")
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
        latest_dt = datetime.fromtimestamp(latest_timestamp, timezone.utc)
        self.data["latest"] = latest_value
        self.data["last_update"] = latest_dt
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
        # For current month: last value before month_start
        val_current_start = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) < month_start), None)
        self.data["month_current"] = round(latest_value - val_current_start, 3) if val_current_start is not None else None
        # For previous month: last before month_start and last before prev_month_start
        val_prev_end = val_current_start
        val_prev_start = next((v for t, v in reversed(readings) if datetime.fromtimestamp(t) < prev_month_start), None)
        self.data["month_previous"] = round(val_prev_end - val_prev_start, 3) if val_prev_end is not None and val_prev_start is not None else None
        _LOGGER.debug(
            "Usage computed: latest=%s hourly=%s daily=%s month_current=%s month_previous=%s",
            self.data["latest"], self.data["hourly"], self.data["daily"],
            self.data["month_current"], self.data["month_previous"]
        )
