# sensor.py - WAVIoT sensors
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR, TEMP_CELSIUS

from .const import DOMAIN

STATE_CLASS_TOTAL = "total_increasing"

SENSOR_TYPES = {
    "latest": {
        "name": "Total Energy",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": STATE_CLASS_TOTAL,
    },
    "hourly": {
        "name": "Hourly Usage",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": STATE_CLASS_TOTAL,
    },
    "daily": {
        "name": "Daily Usage",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": STATE_CLASS_TOTAL,
    },
    "battery": {
        "name": "Battery",
        "unit": "%",
        "device_class": None,
        "state_class": None,
    },
    "temperature": {
        "name": "Temperature",
        "unit": TEMP_CELSIUS,
        "device_class": "temperature",
        "state_class": None,
    },
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up WAVIoT sensors from coordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for key in SENSOR_TYPES:
        entities.append(WaviotSensor(coordinator, key))

    async_add_entities(entities, True)


class WaviotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WAVIoT sensor."""

    def __init__(self, coordinator, sensor_type):
        super().__init__(coordinator)
        self.sensor_type = sensor_type
        self._attr_name = f"WAVIoT {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit"]
        self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]
        self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return None

        if self.sensor_type == "latest":
            return data.get("latest")
        if self.sensor_type == "hourly":
            return data.get("hourly")
        if self.sensor_type == "daily":
            return data.get("daily")
        if self.sensor_type == "battery":
            return data.get("battery")
        if self.sensor_type == "temperature":
            return data.get("temperature")
        return None

    @property
    def extra_state_attributes(self):
        # only add last_update timestamp
        data = self.coordinator.data
        if not data:
            return {}
        last_update = data.get("last_update")
        if last_update:
            return {"last_update": last_update.isoformat()}
        return {}
