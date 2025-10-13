from homeassistant.helpers.entity import Entity
from .const import DOMAIN

SENSOR_TYPES = {
    "battery": {"name": "Battery Voltage", "unit": "V", "device_class": "voltage"},
    "temperature": {"name": "Temperature", "unit": "°C", "device_class": "temperature"},
    "latest": {"name": "Total Energy", "unit": "kWh", "device_class": "energy"},
    "hourly": {"name": "Hourly Usage", "unit": "kWh", "device_class": "energy"},
    "daily": {"name": "Daily Usage", "unit": "kWh", "device_class": "energy"},
    "month_current": {"name": "Current Month Usage", "unit": "kWh", "device_class": "energy"},
    "month_previous": {"name": "Previous Month Usage", "unit": "kWh", "device_class": "energy"},
    "last_update": {"name": "Last Reading", "unit": None, "device_class": "timestamp"},
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors for a Waviot modem entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    sensors = []

    for key, meta in SENSOR_TYPES.items():
        sensors.append(WaviotSensor(coordinator, key, meta))

    async_add_entities(sensors, update_before_add=True)


class WaviotSensor(Entity):
    """Representation of a WAVIoT sensor."""

    def __init__(self, coordinator, sensor_type, meta):
        self.coordinator = coordinator
        self.sensor_type = sensor_type
        self.meta = meta
        self._attr_name = f"{coordinator.modem_id} {meta['name']}"
        self._attr_unique_id = f"{coordinator.modem_id}_{sensor_type}"

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        value = self.coordinator.data.get(self.sensor_type)
        return value

    @property
    def unit_of_measurement(self):
        return self.meta.get("unit")

    @property
    def device_class(self):
        return self.meta.get("device_class")

    async def async_update(self):
        """Request coordinator update."""
        await self.coordinator.async_request_refresh()
