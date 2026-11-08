"""Sensor platform for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_DEVICE, DOMAIN
from .coordinator import LvyuanRuntimeData


@dataclass(frozen=True, kw_only=True)
class LvyuanSensorDescription(SensorEntityDescription):
    """Описание сенсора LVYUAN."""
    value_fn: Callable[[dict[str, Any]], Any]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


# === Sensor entities ===
SENSORS: tuple[LvyuanSensorDescription, ...] = (
    # === Operating Mode ===
    LvyuanSensorDescription(
        key="operating_mode",
        translation_key="operating_mode",
        icon="mdi:power-settings",
        value_fn=lambda data: data.get("operating_mode_name"),
        attributes_fn=lambda data: {"code": data.get("operating_mode")},
    ),

    # === Software ===
    LvyuanSensorDescription(
        key="software_version",
        translation_key="software_version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("software_version"),
        attributes_fn=lambda data: {"date": data.get("software_date")},
    ),

    # === Battery ===
    LvyuanSensorDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("battery_voltage"),
    ),
    LvyuanSensorDescription(
        key="battery_current",
        translation_key="battery_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("battery_current"),
    ),
    LvyuanSensorDescription(
        key="battery_capacity",
        translation_key="battery_capacity",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("battery_capacity"),
    ),
    LvyuanSensorDescription(
        key="battery_type",
        translation_key="battery_type",
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_type_name"),
        attributes_fn=lambda data: {"code": data.get("battery_type_code")},
    ),
    LvyuanSensorDescription(
        key="battery_cutoff_voltage",
        translation_key="battery_cutoff_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_cutoff_voltage"),
    ),
    LvyuanSensorDescription(
        key="battery_alarm_voltage",
        translation_key="battery_alarm_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_alarm_voltage"),
    ),

    # === PV ===
    LvyuanSensorDescription(
        key="pv_voltage",
        translation_key="pv_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("pv_voltage"),
    ),
    LvyuanSensorDescription(
        key="pv_current",
        translation_key="pv_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("pv_current"),
    ),
    LvyuanSensorDescription(
        key="pv_charging_current",
        translation_key="pv_charging_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("pv_charging_current"),
    ),
    LvyuanSensorDescription(
        key="pv_power",
        translation_key="pv_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("pv_power"),
    ),
    LvyuanSensorDescription(
        key="pv_energy_today",
        translation_key="pv_energy_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("pv_energy_today"),
    ),
    LvyuanSensorDescription(
        key="pv_energy_total",
        translation_key="pv_energy_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("pv_energy_total"),
    ),

    # === Output ===
    LvyuanSensorDescription(
        key="output_voltage",
        translation_key="output_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("output_voltage"),
    ),
    LvyuanSensorDescription(
        key="output_frequency",
        translation_key="output_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("output_frequency"),
    ),
    LvyuanSensorDescription(
        key="output_current",
        translation_key="output_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("output_current"),
    ),
    LvyuanSensorDescription(
        key="output_active_power",
        translation_key="output_active_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("output_active_power"),
    ),
    LvyuanSensorDescription(
        key="output_load_percentage",
        translation_key="output_load_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda data: data.get("output_load_percentage"),
    ),
    LvyuanSensorDescription(
        key="output_energy_today",
        translation_key="output_energy_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("output_energy_today"),
    ),
    LvyuanSensorDescription(
        key="output_energy_total",
        translation_key="output_energy_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("output_energy_total"),
    ),

    # === Grid ===
    LvyuanSensorDescription(
        key="grid_voltage",
        translation_key="grid_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("grid_voltage"),
    ),
    LvyuanSensorDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("grid_frequency"),
    ),
    LvyuanSensorDescription(
        key="grid_energy_today",
        translation_key="grid_energy_today",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("grid_energy_today"),
    ),
    LvyuanSensorDescription(
        key="grid_energy_total",
        translation_key="grid_energy_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("grid_energy_total"),
    ),

    # === Inverter ===
    LvyuanSensorDescription(
        key="inverter_voltage",
        translation_key="inverter_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("inverter_voltage"),
    ),
    LvyuanSensorDescription(
        key="inverter_current",
        translation_key="inverter_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("inverter_current"),
    ),

    # === Temperatures ===
    LvyuanSensorDescription(
        key="mainboard_temperature",
        translation_key="mainboard_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("mainboard_temperature"),
    ),
    LvyuanSensorDescription(
        key="pv_temperature",
        translation_key="pv_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("pv_temperature"),
    ),
    LvyuanSensorDescription(
        key="charger_temperature",
        translation_key="charger_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("charger_temperature"),
    ),
    LvyuanSensorDescription(
        key="ambient_temperature",
        translation_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("ambient_temperature"),
    ),

    # === Fan Speed ===
    LvyuanSensorDescription(
        key="fan1_speed",
        translation_key="fan1_speed",
        native_unit_of_measurement="RPM",
        icon="mdi:fan",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("fan1_speed"),
    ),
    LvyuanSensorDescription(
        key="fan2_speed",
        translation_key="fan2_speed",
        native_unit_of_measurement="RPM",
        icon="mdi:fan",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("fan2_speed"),
    ),
    LvyuanSensorDescription(
        key="fan_speed_percentage",
        translation_key="fan_speed_percentage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:fan",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("fan_speed_percentage"),
    ),

    # === Fault/Warning ===
    LvyuanSensorDescription(
        key="fault_code",
        translation_key="fault_code",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("fault_code"),
    ),
    LvyuanSensorDescription(
        key="warning_status",
        translation_key="warning_status",
        icon="mdi:alert-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("warning_status"),
        attributes_fn=lambda data: {
            "warning_1": data.get("warning_status_1"),
            "warning_2": data.get("warning_status_2"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LVYUAN sensor entities."""
    runtime: LvyuanRuntimeData = entry.runtime_data
    serial_device = entry.data.get(CONF_SERIAL_DEVICE, entry.entry_id)

    async_add_entities(
        LvyuanSensor(runtime, entry, description, serial_device)
        for description in SENSORS
    )


class LvyuanSensor(CoordinatorEntity, SensorEntity):
    """Representation of a LVYUAN sensor."""

    entity_description: LvyuanSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: LvyuanRuntimeData,
        entry: ConfigEntry,
        description: LvyuanSensorDescription,
        serial_device: str,
    ) -> None:
        super().__init__(runtime.coordinator)
        self.runtime = runtime
        self.entity_description = description
        self._attr_unique_id = f"{serial_device}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_device)},
            manufacturer="LVYUAN",
            model="TY-SIC-3.6KBE-W1",
            name=entry.title,
        )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None