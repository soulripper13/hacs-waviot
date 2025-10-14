# switch.py - Diagnostics switch for WAVIoT per modem
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_DIAGNOSTICS

class WaviotDiagnosticsSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to toggle diagnostics logging for a modem."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entry_id = entry_id
        self._attr_name = f"WAVIoT Diagnostics {coordinator.modem_id}"
        self._attr_unique_id = f"{coordinator.modem_id}_diagnostics"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.modem_id)},
            "name": f"WAVIoT Modem {coordinator.modem_id}",
        }

    @property
    def is_on(self):
        return bool(self.coordinator.enable_diagnostics)

    async def async_turn_on(self, **kwargs):
        self.coordinator.enable_diagnostics = True
        # immediate log to indicate change
        self.coordinator.hass.async_create_task(self.coordinator.async_request_refresh())

    async def async_turn_off(self, **kwargs):
        self.coordinator.enable_diagnostics = False
        self.coordinator.hass.async_create_task(self.coordinator.async_request_refresh())

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WaviotDiagnosticsSwitch(coordinator, entry.entry_id)])
