# __init__.py - WAVIoT integration
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, CONF_API_KEY, CONF_MODEM_ID
from .coordinator import WaviotDataUpdateCoordinator

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WAVIoT integration (no YAML support)."""
    return True  # We only support config entries

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WAVIoT integration from a config entry."""
    # Lazy import of platforms to avoid blocking the event loop
    # This prevents the "Detected blocking call to import_module" warning
    coordinator = WaviotDataUpdateCoordinator(
        hass,
        api_key=entry.data[CONF_API_KEY],
        modem_id=entry.data[CONF_MODEM_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator for this entry
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup to sensor platform (lazy, non-blocking)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
