# config_flow.py - No changes needed
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY, CONF_MODEM_ID
import voluptuous as vol

class WaviotFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"Modem {user_input[CONF_MODEM_ID]}", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_MODEM_ID): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)
