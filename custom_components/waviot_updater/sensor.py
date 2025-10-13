from __future__ import annotations
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfVoltage, UnitOfTemperature
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime, timezone, timedelta
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "total": ("Total Energy (T1)", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "hourly": ("Hourly Usage (T1)", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    "daily": ("Daily Usage (T1)", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.MEASUREMENT),
    "month_current": ("Current Month Usage (T1)", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "month_previous": ("Previous Month Usage (T1)", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    "last_update": ("Last Reading Time (T1)", None, SensorDeviceClass.TIMESTAMP, None),
    "battery": ("Battery Voltage", UnitOfVoltage.VOLT, SensorDeviceClass.VOLTAGE, None),
    "temperature": ("Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, None),
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = []
    for suffix, (name, unit, dclass, sclass) in SENSOR_TYPES.items():
        unique_id = f"waviot_{entry.entry_id}_{suffix}"
        ent = WaviotSensor(
            coordinator,
            entry.entry_id,
            suffix,
            name,
            unit,
            dclass,
            sclass,
            unique_id,
        )
        entities.append(ent)

    async_add_entities(entities, update_before_add=True)


class WaviotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, suffix, name, unit, device_class, state_class, unique_id):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._suffix = suffix
        self._attr_name = f"WAVIoT {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = unique_id

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        if not data.get("status") == "ok":
            return None

        values = data.get("values", {})
        if not values:
            return None

        try:
            items = sorted(((int(ts), float(val)) for ts, val in values.items()), key=lambda x: x[0])
        except Exception as e:
            _LOGGER.error("Parsing WAVIoT response error: %s", e)
            return None

        # Latest cumulative
        if self._suffix == "total":
            return items[-1][1]

        if self._suffix == "last_update":
            return datetime.fromtimestamp(items[-1][0], tz=timezone.utc).isoformat()

        # Compute diffs: hourly usage list
        hourly = []
        prev = None
        for ts, val in items:
            if prev is not None:
                diff = val - prev
                if diff >= 0:
                    hourly.append((ts, diff))
            prev = val

        # Build daily aggregations
        daily = {}
        for ts, diff in hourly:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc).date()
            daily.setdefault(dt.isoformat(), 0.0)
            daily[dt.isoformat()] += diff

        now = datetime.now(timezone.utc).date()
        yesterday = now - timedelta(days=1)

        first_day_this_month = now.replace(day=1)
        prev_month_end = first_day_this_month - timedelta(days=1)
        first_day_prev_month = prev_month_end.replace(day=1)

        def month_total(start_date, end_date):
            s = 0.0
            d = start_date
            while d <= end_date:
                s += daily.get(d.isoformat(), 0.0)
                d += timedelta(days=1)
            return round(s, 3)

        if self._suffix == "hourly":
            if hourly:
                return round(hourly[-1][1], 3)
            return None

        if self._suffix == "daily":
            return round(daily.get(now.isoformat(), 0.0), 3)

        if self._suffix == "month_current":
            return month_total(first_day_this_month, now)

        if self._suffix == "month_previous":
            return month_total(first_day_prev_month, prev_month_end)

        # battery / temperature: you must extend coordinator data
        if self._suffix in ("battery", "temperature"):
            # expect coordinator.data["modem_info"] with keys "battery" / "temperature"
            mi = data.get("modem_info", {})
            return mi.get(self._suffix)

        return None
