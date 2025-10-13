import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, CONF_MODEM_ID

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_API_KEY): str,
    vol.Required(CONF_MODEM_ID): str,
})

class WaviotUpdaterFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for WAVIoT Updater."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # You could validate the API key and modem here before creating entry
            return self.async_create_entry(title=user_input[CONF_MODEM_ID], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA
        )
