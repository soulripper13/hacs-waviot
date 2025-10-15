import aiohttp
from datetime import datetime, timedelta, timezone
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from .const import UPDATE_INTERVAL, BASE_URL

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1
STORAGE_KEY = "waviot_backfill_ts"

class WaviotDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch WAVIoT modem and energy data safely with persistent incremental backfill."""

    def __init__(self, hass: HomeAssistant, api_key: str, modem_id: str):
        self.hass = hass
        self.api_key = api_key
        self.modem_id = modem_id
        self.data = {}
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{modem_id}")
        self._last_backfill_ts = 0  # will load from storage
        super().__init__(
            hass,
            _LOGGER,
            name=f"WAVIoT Modem {modem_id}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def async_initialize(self):
        """Load last backfill timestamp from storage."""
        stored = await self._store.async_load()
        if stored and isinstance(stored, dict):
            self._last_backfill_ts = stored.get("last_backfill_ts", 0)
        _LOGGER.debug("Loaded last backfill timestamp: %s", self._last_backfill_ts)

    async def _async_update_data(self):
        """Fetch modem info, channel readings, and backfill historical values."""
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

            # --- Energy readings ---
            try:
                channel_id = "electro_ac_p_lsum_t1"
                now = datetime.now(tz=timezone.utc)
                # Backfill from Jan 1 of current year if no previous timestamp
                start_ts = self._last_backfill_ts or int(datetime(now.year, 1, 1, tzinfo=timezone.utc).timestamp())

                url = (
                    f"{BASE_URL}data/get_modem_channel_values/"
                    f"?modem_id={self.modem_id}&channel={channel_id}&key={self.api_key}"
                    f"&start={start_ts}&end={int(now.timestamp())}"
                )
                async with session.get(url) as resp:
                    ch_data = await resp.json()
                    values = ch_data.get("values", {}) if ch_data else {}
                    readings = []
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

                # --- Incremental Backfill into HA ---
                await self._async_backfill_incremental(readings)

            except Exception as e:
                _LOGGER.error("Exception fetching channel values: %s", e)
                self.data["readings"] = []

            # --- Compute latest metric only ---
            self._compute_latest()

        return self.data

    async def _async_backfill_incremental(self, readings):
        """Backfill only new readings into Home Assistant and persist last timestamp."""
        entity_id = f"sensor.waviot_{self.modem_id.lower()}_latest"

        new_readings = [r for r in readings if r[0] > self._last_backfill_ts]
        if not new_readings:
            return

        for ts, value in new_readings:
            dt_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            state_data = {
                "state": str(value),
                "attributes": {
                    "unit_of_measurement": "kWh",
                    "friendly_name": "Total Energy",
                    "device_class": "energy",
                    "state_class": "total_increasing"
                },
                "last_changed": dt_iso,
                "last_updated": dt_iso
            }
            try:
                await self.hass.states.async_set(entity_id, **state_data)
                self._last_backfill_ts = ts
            except Exception as e:
                _LOGGER.warning("Failed to backfill reading %s: %s", dt_iso, e)

        # persist last backfill timestamp
        await self._store.async_save({"last_backfill_ts": self._last_backfill_ts})

    def _compute_latest(self):
        """Compute only the latest reading value."""
        readings = self.data.get("readings", [])
        if not readings:
            self._init_empty_data()
            return
        latest_timestamp, latest_value = readings[-1]
        latest_dt = datetime.fromtimestamp(latest_timestamp, tz=timezone.utc)
        self.data["latest"] = latest_value
        self.data["last_update"] = latest_dt

    def _init_empty_data(self):
        """Initialize empty data dict."""
        self.data.update({
            "battery": None,
            "temperature": None,
            "readings": [],
            "latest": None,
            "last_update": None,
        })
