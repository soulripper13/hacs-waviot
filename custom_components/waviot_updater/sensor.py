# sensor.py - Updated to use SensorStateClass enums
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

SENSOR_TYPES = {
    "battery": {
        "name": "Battery Voltage",
        "unit": "V",
        "device_class": "voltage",
        "state_class": None,
    },
    "temperature": {
        "name": "Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": None,
    },
    "latest": {
        "name": "Total Energy",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": SensorStateClass.TOTAL_INCREASING,
    },
    "hourly": {
        "name": "Hourly Usage",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "daily": {
        "name": "Daily Usage",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "month_current": {
        "name": "Current Month Usage",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "month_previous": {
        "name": "Previous Month Usage",
        "unit": "kWh",
        "device_class": "energy",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "last_update": {
        "name": "Last Reading",
        "unit": None,
        "device_class": "timestamp",
        "state_class": None,
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for a Waviot modem entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        WaviotSensor(coordinator, key, meta)
        for key, meta in SENSOR_TYPES.items()
    ]
    async_add_entities(sensors, update_before_add=True)


class WaviotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WAVIoT sensor."""

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

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self.sensor_type)
        if value is None:
            return None
        # Convert last_update to ISO format
        if self.sensor_type == "last_update":
            return value.isoformat()
        return value

    @property
    def available(self):
        """Return True if sensor data is available."""
        return self.coordinator.data.get("latest") is not None
