# Монитор энергии WAVIoT для Home Assistant
![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
Пользовательская интеграция для Home Assistant для мониторинга **энергомеров WAVIoT** через официальный API [curog.ru](https://lk.curog.ru).
Она предоставляет сенсоры использования электричества, уровня батареи и температуры — с полной конфигурацией через UI.
---
## ✨ Возможности
- 🔋 **Сенсор уровня батареи**
- 🌡️ **Сенсор температуры**
- 🔁 Автоматические обновления каждые 10 минут
- 🧠 Данные получаются напрямую из API WAVIoT
- ⚙️ Полная конфигурация через UI
- 🧩 Совместима с HACS (пользовательское хранилище)
---
## 🧰 Установка
### Метод 1: HACS (Рекомендуется)
Предпочтительный способ — использовать HACS:
1. Найдите и загрузите эту интеграцию в вашу установку HA через HACS, или нажмите:  
   [Открыть репозиторий HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=soulripper13&repository=hacs-waviot&category=integration)
2. Перезапустите Home Assistant
3. Добавьте эту интеграцию в Home Assistant, или нажмите:  
   [Добавить интеграцию](https://my.home-assistant.io/redirect/config_flow/?domain=waviot_updater)

### Метод 2: Ручная установка
1. Скопируйте папку `custom_components/waviot_updater` в директорию `config/custom_components/` вашего Home Assistant.
2. Перезапустите Home Assistant.
---
## ⚙️ Конфигурация
После установки и перезапуска:
1. Перейдите в **Настройки → Устройства и сервисы → Добавить интеграцию**
2. Найдите **WAVIoT Updater**
3. Введите:
- **API-ключ** (из вашего аккаунта WAVIoT)
- **ID модема** (например, `86145D`)
4. Готово! Интеграция создаст следующие сенсоры:
| Entity ID | Описание | Единица |
|-----------|----------|---------|
| `sensor.waviot_<modem_id>_energy_total` | Общая накопленная энергия (T1) | кВт·ч |
| `sensor.waviot_<modem_id>_battery` | Уровень батареи | % |
| `sensor.waviot_<modem_id>_temperature` | Температура устройства | °C |
---
## 🔄 Источник данных
Все данные получаются из:
https://lk.curog.ru/api.data/get_modem_channel_values/
с использованием вашего **API-ключа** и **ID модема**.
---
## 🧪 Пример вывода
| Сенсор | Пример значения | Описание |
|--------|------------------|----------|
| `sensor.waviot_86145d_energy_total` | 21149.162 | Общее показание |
| `sensor.waviot_86145d_battery` | 85 | Уровень батареи |
| `sensor.waviot_86145d_temperature` | 22.5 | Температура устройства |
---
## ⚠️ Примечания
- Интеграция получает новые данные каждые **10 минут**.
- Убедитесь, что ваш API-ключ действителен и ID модема существует в вашем аккаунте WAVIoT.
- Вы можете переконфигурировать в любое время, удалив и заново добавив интеграцию.
---
## 🧑‍💻 Разработчик
**Автор:** [soulripper13](https://github.com/soulripper13)
**Лицензия:** [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
**Репозиторий:** [hacs-waviot](https://github.com/soulripper13/hacs-waviot)
---
## 🩵 Поддержка
Если эта интеграция вам полезна, пожалуйста, ⭐️ репозиторию или [откройте issue](https://github.com/soulripper13/hacs-waviot/issues) для предложений и отчетов об ошибках.

---

# WAVIoT Energy Monitor for Home Assistant
![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
A custom Home Assistant integration to monitor **WAVIoT energy meters** via the official [curog.ru](https://lk.curog.ru) API.
It provides electricity usage, battery level, and temperature sensors — with full UI configuration.
---
## ✨ Features
- 🔋 **Battery Level Sensor**
- 🌡️ **Temperature Sensor**
- 🔁 Automatic updates every 10 minutes
- 🧠 Data fetched directly from the WAVIoT API
- ⚙️ Full configuration via the UI
- 🧩 HACS compatible (custom repository)
---
## 🧰 Installation
### Method 1: HACS (Recommended)
The preferred way is to use HACS:
1. Search and download this integration to your HA installation via HACS, or click:  
   [Open HACS Repository](https://my.home-assistant.io/redirect/hacs_repository/?owner=soulripper13&repository=hacs-waviot&category=integration)
2. Restart Home Assistant
3. Add this integration to Home Assistant, or click:  
   [Add Integration](https://my.home-assistant.io/redirect/config_flow/?domain=waviot_updater)

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
|-----------|-------------|------|
| `sensor.waviot_<modem_id>_energy_total` | Total accumulated energy (T1) | kWh |
| `sensor.waviot_<modem_id>_battery` | Battery level | % |
| `sensor.waviot_<modem_id>_temperature` | Device temperature | °C |
---
## 🔄 Data Source
All data is fetched from:
https://lk.curog.ru/api.data/get_modem_channel_values/
using your **API key** and **modem ID**.
---
## 🧪 Example Output
| Sensor | Example Value | Description |
|--------|---------------|-------------|
| `sensor.waviot_86145d_energy_total` | 21149.162 | Total reading |
| `sensor.waviot_86145d_battery` | 85 | Battery level |
| `sensor.waviot_86145d_temperature` | 22.5 | Device temperature |
---
## ⚠️ Notes
- The integration fetches new data every **10 minutes**.
- Ensure your API key is valid and that the modem ID exists on your WAVIoT account.
- You can reconfigure at any time by removing and re-adding the integration.
---
## 🧑‍💻 Developer
**Author:** [soulripper13](https://github.com/soulripper13)
**License:** [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
**Repository:** [hacs-waviot](https://github.com/soulripper13/hacs-waviot)
---
## 🩵 Support
If you find this integration helpful, please ⭐️ the repo or [open an issue](https://github.com/soulripper13/hacs-waviot/issues) for suggestions and bug reports.
