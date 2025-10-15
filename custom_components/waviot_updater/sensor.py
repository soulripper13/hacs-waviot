# sensor.py - WAVIoT sensors with safe backfill
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_call_later
from .const import DOMAIN
from datetime import datetime, timezone

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
    """Representation of a WAVIoT sensor with backfill support."""

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

        # Schedule backfill for energy readings
        if self.sensor_type == "latest":
            async_call_later(self.hass, 1, self._async_backfill_recent_readings)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self.sensor_type)

    async def _async_backfill_recent_readings(self, _now=None):
        """Backfill missing energy readings safely."""
        readings = self.coordinator.data.get("readings", [])
        entity_id = self.entity_id

        for ts, value in readings:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            # Only set state if not already present
            if not self.hass.states.get(entity_id) or self.hass.states.get(entity_id).last_updated < datetime.fromtimestamp(ts, tz=timezone.utc):
                self.hass.states.async_set(
                    entity_id=entity_id,
                    state=value,
                    attributes={
                        "unit_of_measurement": self._attr_native_unit_of_measurement,
                        "device_class": self._attr_device_class,
                        "friendly_name": self._attr_name,
                        "last_update": dt,
                    },
                )
