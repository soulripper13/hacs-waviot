# config_flow.py - WAVIoT integration
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY, CONF_MODEM_ID
import voluptuous as vol
import aiohttp
from homeassistant.exceptions import ConfigEntryNotReady

class WaviotFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a WAVIoT config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Optional: validate API key/modem_id by fetching modem info
            api_key = user_input[CONF_API_KEY]
            modem_id = user_input[CONF_MODEM_ID]
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.waviot.com/modem/info/?id={modem_id}&key={api_key}"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            errors["base"] = "cannot_connect"
                        else:
                            data = await resp.json()
                            if not data.get("modem"):
                                errors["base"] = "invalid_modem"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Modem {modem_id}",
                    data=user_input
                )

        # Show the form
        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_MODEM_ID): str,
        })
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
