# sensor.py
from homeassistant.helpers.entity import Entity
from homeassistant.const import DEVICE_CLASS_BATTERY, DEVICE_CLASS_ENERGY, TEMP_CELSIUS, ENERGY_KILO_WATT_HOUR
from .const import DOMAIN

SENSORS = [
    {"key": "battery", "name": "Battery Voltage", "unit": "V", "device_class": DEVICE_CLASS_BATTERY, "state_class": None},
    {"key": "temperature", "name": "Temperature", "unit": TEMP_CELSIUS, "device_class": None, "state_class": None},
    {"key": "latest", "name": "Last Reading", "unit": ENERGY_KILO_WATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "total_increasing"},
    {"key": "hourly", "name": "Hourly Energy", "unit": ENERGY_KILO_WATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "measurement"},
    {"key": "daily", "name": "Daily Energy", "unit": ENERGY_KILO_WATT_HOUR, "device_class": DEVICE_CLASS_ENERGY, "state_class": "measurement"},
]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entry_id = discovery_info["entry_id"] if discovery_info else None
    coordinator = hass.data[DOMAIN][entry_id]
    async_add_entities([WaviotSensor(coordinator, s["key"], s["name"], s["unit"], s["device_class"], s["state_class"]) for s in SENSORS])

class WaviotSensor(Entity):
    def __init__(self, coordinator, key, name, unit, device_class, state_class):
        self.coordinator = coordinator
        self._key = key
        self._name = name
        self._unit = unit
        self._device_class = device_class
        self._state_class = state_class

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self.coordinator.data.get(self._key)

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

    @property
    def available(self):
        return bool(self.coordinator.data)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
