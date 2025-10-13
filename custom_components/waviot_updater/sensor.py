from homeassistant.helpers.entity import Entity
from .const import DOMAIN

SENSOR_TYPES = {
    "battery": ("Battery", "%", "voltage"),
    "temperature": ("Temperature", "°C", "temperature"),
    "latest": ("Total Energy (T1)", "kWh", "energy"),
    "hourly": ("Hourly Usage (T1)", "kWh", "energy"),
    "daily": ("Daily Usage (T1)", "kWh", "energy"),
    "month_current": ("Current Month Usage", "kWh", "energy"),
    "month_previous": ("Previous Month Usage", "kWh", "energy"),
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [WaviotSensor(coordinator, key) for key in SENSOR_TYPES]
    async_add_entities(entities)

class WaviotSensor(Entity):
    def __init__(self, coordinator, sensor_type):
        self.coordinator = coordinator
        self.sensor_type = sensor_type
        self._attr_name = f"WAVIoT {sensor_type}"
        self._attr_unique_id = f"{coordinator.modem_id}_{sensor_type}"

    @property
    def state(self):
        return self.coordinator.data.get(self.sensor_type)

    @property
    def name(self):
        return SENSOR_TYPES[self.sensor_type][0]

    @property
    def unit_of_measurement(self):
        return SENSOR_TYPES[self.sensor_type][1]

    @property
    def device_class(self):
        return SENSOR_TYPES[self.sensor_type][2]

    async def async_update(self):
        await self.coordinator.async_request_refresh()
