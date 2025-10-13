import aiohttp
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import API_BASE, CONF_API_KEY, CONF_MODEM_ID

_LOGGER = logging.getLogger(__name__)

class WaviotDataCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from WAVIoT."""

    def __init__(self, hass, api_key: str, modem_id: str):
        super().__init__(
            hass,
            _LOGGER,
            name=f"waviot_{modem_id}",
            update_interval=timedelta(minutes=10),
        )
        self.api_key = api_key
        self.modem_id = modem_id

    async def _async_update_data(self):
        """Fetch data from WAVIoT API."""
        url = f"{API_BASE}/get_modem_channel_values/?modem_id={self.modem_id}&channel=electro_ac_p_lsum_t1&key={self.api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=20) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP error {resp.status}")
                    data = await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Error fetching data: {e}")

        # Optionally you can fetch battery and temperature via another endpoint:
        # For example:
        # url2 = f"{API_BASE}/modem/info/?id={self.modem_id}&key={self.api_key}"
        # etc.
        # For now, attach that info inside the returned data:
        # For example:
        # info_resp = ...
        # data["modem_info"] = info_resp

        return data
