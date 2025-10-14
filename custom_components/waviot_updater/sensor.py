# sensor.py - WAVIoT sensors
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

SENSOR_TYPES = {
    "battery": {"name": "Battery Voltage", "unit": "V", "device_class": "voltage"},
    "temperature": {"name": "Temperature", "unit": "°C", "device_class": "temperature"},
    "latest": {"name": "Total Energy", "unit": "kWh", "device_class": "energy", "state_class": SensorStateClass.TOTAL_INCREASING},
    "hourly": {"name": "Hourly Usage", "unit": "kWh", "device_class": "energy", "state_class": None},
    "daily": {"name": "Daily Usage", "unit": "kWh", "device_class": "energy", "state_class": None},
    "last_update": {"name": "Last Reading", "unit": None, "device_class": "timestamp"},
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [WaviotSensor(coordinator, key, meta) for key, meta in SENSOR_TYPES.items()]
    async_add_entities(sensors, update_before_add=True)

class WaviotSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_type, meta):
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self.meta = meta
        self._attr_name = meta['name']
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
        value = self.coordinator.data.get(self.sensor_type)
        # Ensure timestamp is a datetime object for 'timestamp' device class
        if self.sensor_type == "last_update" and isinstance(value, str):
            from datetime import datetime
            value = datetime.fromisoformat(value)
        return value
