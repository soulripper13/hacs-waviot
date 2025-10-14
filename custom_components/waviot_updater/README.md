# WAVIoT Updater - HACS custom integration


Drop the folder into `custom_components/` or install via HACS.


Entities created per modem:


- `sensor.waviot_latest` — cumulative kWh (Energy dashboard)

- `sensor.waviot_daily` — kWh last 24h

- `sensor.waviot_hourly` — kWh last hour

- `sensor.waviot_battery` — battery voltage

- `sensor.waviot_temperature` — temperature

- `sensor.waviot_last_update` — timestamp of last reading

- `switch.waviot_diagnostics` — toggles verbose API logging to HA logs


Configuration: add integration via UI, provide API key and modem id. You can enable diagnostics during setup or toggle the switch after.

Update interval default: 600s (10 minutes)
