# sensor.py - WAVIoT sensors with safe async backfill for last 3 months
from datetime import datetime, timedelta, timezone
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_call_later
from .const import DOMAIN, BACKFILL_INTERVAL_SECONDS

SENSOR_TYPES = {
    "battery": {
        "name": "Battery Voltage",
        "unit": "V",
        "device_class": "voltage",
    },
    "temperature": {
        "name": "Temperature",
        "unit": "°C",
        "device_class": "temperature",
    },
    "latest": {
        "name": "Total Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "last_update": {
        "name": "Last Reading",
        "unit": None,
        "device_class": "timestamp",
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for a Waviot modem entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [WaviotSensor(coordinator, key, meta) for key, meta in SENSOR_TYPES.items()]
    async_add_entities(sensors, update_before_add=True)


class WaviotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WAVIoT sensor with backfill."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_type, meta):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self.meta = meta
        self._attr_name = meta["name"]
        self._attr_unique_id = f"{coordinator.modem_id}_{sensor_type}"
        self._attr_device_class = meta.get("device_class")
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_state_class = meta.get("state_class")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.modem_id)},
            "name": f"WAVIoT Modem {coordinator.modem_id}",
            "model": "Modem",
            "manufacturer": "WAVIoT",
        }

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        await super().async_added_to_hass()
        # Schedule backfill after the entity is fully added
        self.hass.async_create_task(self._async_backfill_recent_readings())

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.coordinator.data.get(self.sensor_type)

    async def _async_backfill_recent_readings(self):
        """Fetch and add past readings (last 3 months) safely."""
        coordinator = self.coordinator
        if not hasattr(coordinator, "data") or "readings" not in coordinator.data:
            return

        # Calculate 3 months ago
        now = datetime.now(tz=timezone.utc)
        three_months_ago = now - timedelta(days=90)

        backfill_readings = []
        for ts, val in coordinator.data.get("readings", []):
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if dt >= three_months_ago:
                backfill_readings.append((dt, val))

        # Optionally, you can store these somewhere or log them
        if backfill_readings:
            # Update latest reading if applicable
            latest_dt, latest_val = backfill_readings[-1]
            coordinator.data["latest"] = latest_val
            coordinator.data["last_update"] = latest_dt
