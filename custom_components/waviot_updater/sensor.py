# sensor.py - defines sensors for WAVIoT
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_VOLTAGE, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_ENERGY, UNIT_KILOWATT_HOUR, UNIT_VOLT
from homeassistant.helpers.update_coordinator import CoordinatorEntity

SENSOR_TYPES = {
    "battery": {"name": "Battery Voltage", "unit": UNIT_VOLT, "device_class": DEVICE_CLASS_VOLTAGE, "state_class": None},
    "temperature": {"name": "Temperature", "unit": "°C", "device_class": DEVICE_CLASS_TEMPERATURE, "state_class": None},
    "last_update": {"name": "Last Reading", "unit": None, "device_class": "timestamp", "state_class": None},
    "latest": {"name": "Total Energy", "unit": UNIT_KILOWATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "total_increasing"},
    "hourly": {"name": "Hourly Energy", "unit": UNIT_KILOWATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "total"},
    "daily": {"name": "Daily Energy", "unit": UNIT_KILOWATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "total"},
}

class WaviotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]

    @property
    def state(self):
        value = self.coordinator.data.get(self.sensor_type)
        if self.sensor_type == "last_update" and value:
            return value.isoformat()
        return value

