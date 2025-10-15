# coordinator.py - Fetches WAVIoT modem data and backfills from the beginning of the current year
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
                start_of_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)

                url = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                    f"&start={int(start_of_year.timestamp())}&end={int(now.timestamp())}"
                )
                _LOGGER.debug("Fetching readings from start of current year: %s", url)

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

            # --- Backfill past readings into HA state machine ---
            await self._backfill_readings()

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

    async def _backfill_readings(self):
        """Backfill hourly readings from the beginning of the current year."""
        readings = self.data.get("readings", [])
        if not readings:
            _LOGGER.debug("No readings to backfill.")
            return

        entity_id = f"sensor.waviot_{self.modem_id}_latest"
        now = datetime.now(tz=timezone.utc)
        start_of_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)

        new_readings = [
            (ts, val) for ts, val in readings
            if ts >= int(start_of_year.timestamp())
        ]

        _LOGGER.debug("Backfilling %d readings from %s", len(new_readings), start_of_year)

        for ts, value in new_readings:
            dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            attributes = {
                "unit_of_measurement": "kWh",
                "friendly_name": "Total Energy",
                "device_class": "energy",
                "state_class": "total_increasing",
                "last_changed": dt_iso,
                "last_updated": dt_iso,
            }

            try:
                await self.hass.states.async_set(entity_id, str(value), attributes=attributes)
            except Exception as e:
                _LOGGER.warning("Failed to backfill reading %s: %s", dt_iso, e)

        _LOGGER.info("Finished backfilling readings.")

    def _init_empty_data(self):
        """Initialize empty data dict."""
        self.data.update({
            "battery": None,
            "temperature": None,
            "readings": [],
            "latest": None,
            "last_update": None,
        })
