# WAVIoT Energy Monitor for Home Assistant
![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  <!-- Fixed: Inline badge -->

A custom Home Assistant integration to monitor **WAVIoT energy meters** via the official [curog.ru](https://lk.curog.ru) API.
It provides electricity usage, battery level, and temperature sensors — with full UI configuration.
---
## ✨ Features
- 🔋 **Battery Level Sensor**
- 🌡️ **Temperature Sensor**
- 🔁 Automatic updates every 10 minutes  <!-- Fixed: Standardized to match Notes -->
- 🧠 Data fetched directly from the WAVIoT API
- ⚙️ Full configuration via the UI
- 🧩 HACS compatible (custom repository)
---
## 🧰 Installation
### Method 1: HACS (Recommended)
1. Go to **HACS → Integrations → Custom repositories**
2. Add this repository:
https://github.com/soulripper13/hacs-waviot
Category: **Integration**
3. Search for **WAVIoT Updater** in HACS and click **Install**
4. Restart Home Assistant
### Method 2: Manual Installation
1. Copy the folder `custom_components/waviot_updater` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
---
## ⚙️ Configuration
After installing and restarting:
1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **WAVIoT Updater**
3. Enter:
- **API Key** (from your WAVIoT account)
- **Modem ID** (e.g. `86145D`)
4. Done! The integration will create the following sensors:
| Entity ID | Description | Unit |
|------------|--------------|------|
| `sensor.waviot_<modem_id>_energy_total` | Total accumulated energy (T1) | kWh |
| `sensor.waviot_<modem_id>_battery` | Battery level | %  <!-- Polished: Simplified description/unit for consistency -->
| `sensor.waviot_<modem_id>_temperature` | Device temperature | °C |
---
## 🔄 Data Source
All data is fetched from:
https://lk.curog.ru/api.data/get_modem_channel_values/
using your **API key** and **modem ID**.
---
## 🧪 Example Output
| Sensor | Example Value | Description |
|---------|----------------|-------------|
| `sensor.waviot_86145d_energy_total` | 21149.162 | Total reading |
| `sensor.waviot_86145d_battery` | 85 | Battery level |
| `sensor.waviot_86145d_temperature` | 22.5 | Device temperature |  <!-- Added: Complete the table -->
---
## ⚠️ Notes
- The integration fetches new data every **10 minutes**.
- Ensure your API key is valid and that the modem ID exists on your WAVIoT account.
- You can reconfigure at any time by removing and re-adding the integration.
---
## 🧑‍💻 Developer
**Author:** [soulripper13](https://github.com/soulripper13)
**License:** [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
**Repository:** [hacs-waviot](https://github.com/soulripper13/hacs-waviot)  <!-- Fixed: Link text matches URL -->
---
## 🩵 Support
If you find this integration helpful, please ⭐️ the repo or [open an issue](https://github.com/soulripper13/hacs-waviot/issues) for suggestions and bug reports.
