# sensor.py
from __future__ import annotations
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR, TEMP_CELSIUS
from .const import DOMAIN

SENSOR_DEFS = {
    "battery": {
        "name": "Battery Voltage",
        "unit": "V",
        "device_class": "voltage",
        "state_class": None,
    },
    "temperature": {
        "name": "Temperature",
        "unit": TEMP_CELSIUS,
        "device_class": "temperature",
        "state_class": None,
    },
    "last_update": {
        "name": "Last Reading",
        "unit": None,
        "device_class": "timestamp",
        "state_class": None,
    },
    "latest": {
        "name": "Total Energy",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "hourly": {
        "name": "Hourly Energy",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "daily": {
        "name": "Daily Energy",
        "unit": ENERGY_KILO_WATT_HOUR,
        "device_class": "energy",
        "state_class": "total_increasing",
    },
}

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for key, meta in SENSOR_DEFS.items():
        entities.append(WaviotSensor(coordinator, key, meta))
    async_add_entities(entities, update_before_add=True)

class WaviotSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WAVIoT sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_key: str, meta: dict):
        super().__init__(coordinator)
        self.sensor_key = sensor_key
        self._meta = meta
        self._attr_name = meta["name"]
        self._attr_native_unit_of_measurement = meta["unit"]
        self._attr_device_class = meta.get("device_class")
        self._attr_state_class = meta.get("state_class")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.modem_id)},
            "name": f"WAVIoT Modem {coordinator.modem_id}",
            "model": "Modem",
            "manufacturer": "WAVIoT",
        }

    @property
    def native_value(self):
        """Return the native value for the sensor."""
        data = self.coordinator.data or {}
        val = data.get(self.sensor_key)

        # last_update must be a datetime object (Home Assistant handles formatting)
        if self.sensor_key == "last_update":
            if isinstance(val, datetime):
                return val
            return None

        return val
