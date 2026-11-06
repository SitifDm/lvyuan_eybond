"""Number platform for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfElectricPotential, UnitOfElectricCurrent, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_DEVICE, DOMAIN
from .coordinator import LvyuanRuntimeData


@dataclass(frozen=True, kw_only=True)
class LvyuanNumberDescription(NumberEntityDescription):
    """Описание числовой настройки LVYUAN."""
    read_key: str
    command_prefix: str
    command_width: int
    is_scaled: bool = False
    scale_factor: float = 10.0
    native_step: float = 1.0


# Числовые настройки с точными диапазонами согласно инструкции LVYUAN TY-SIC-3.6KBE-W1
NUMBERS: tuple[LvyuanNumberDescription, ...] = (
    # --- Charging ---
    LvyuanNumberDescription(
        key="max_charging_current",
        translation_key="max_charging_current",
        icon="mdi:current-dc",
        entity_category=EntityCategory.CONFIG,
        native_min_value=2,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class="current",
        read_key="max_charging_current",
        command_prefix="CHGC",
        command_width=3,
    ),
    LvyuanNumberDescription(
        key="max_utility_charging_current",
        translation_key="max_utility_charging_current",
        icon="mdi:current-ac",
        entity_category=EntityCategory.CONFIG,
        native_min_value=2,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class="current",
        read_key="max_utility_charging_current",
        command_prefix="GCC",
        command_width=3,
    ),
    LvyuanNumberDescription(
        key="constant_voltage_charging_voltage",
        translation_key="constant_voltage_charging_voltage",
        icon="mdi:battery-charging-high",
        entity_category=EntityCategory.CONFIG,
        native_min_value=24.0,
        native_max_value=29.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="constant_voltage_charging_voltage",
        command_prefix="TCCV",
        command_width=4,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="float_charging_voltage",
        translation_key="float_charging_voltage",
        icon="mdi:battery-charging-medium",
        entity_category=EntityCategory.CONFIG,
        native_min_value=24.0,
        native_max_value=28.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="float_charging_voltage",
        command_prefix="TCFV",
        command_width=4,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="constant_voltage_charging_time",
        translation_key="constant_voltage_charging_time",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=1,
        native_max_value=720,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        read_key="constant_voltage_charging_time",
        command_prefix="TCVT",
        command_width=4,
    ),
    LvyuanNumberDescription(
        key="constant_current_charging_max_time",
        translation_key="constant_current_charging_max_time",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=1,
        native_max_value=99,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        read_key="constant_current_charging_max_time",
        command_prefix="CI1",
        command_width=2,
    ),

    # --- Battery ---
    LvyuanNumberDescription(
        key="equalization_charging_voltage",
        translation_key="equalization_charging_voltage",
        icon="mdi:battery-charging-wireless",
        entity_category=EntityCategory.CONFIG,
        native_min_value=25.0,
        native_max_value=31.5,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="equalization_charging_voltage",
        command_prefix="TCQV",
        command_width=4,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="equalization_charging_time",
        translation_key="equalization_charging_time",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=5,
        native_max_value=900,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        read_key="equalization_charging_time",
        command_prefix="TCQT",
        command_width=4,
    ),
    LvyuanNumberDescription(
        key="equalization_timeout",
        translation_key="equalization_timeout",
        icon="mdi:timer-off-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=5,
        native_max_value=900,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        read_key="equalization_timeout",
        command_prefix="TCQO",
        command_width=4,
    ),
    LvyuanNumberDescription(
        key="equalization_interval",
        translation_key="equalization_interval",
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.CONFIG,
        native_min_value=1,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement="day",
        read_key="equalization_interval",
        command_prefix="TCQI",
        command_width=4,
    ),
    LvyuanNumberDescription(
        key="battery_discharge_cutoff_voltage",
        translation_key="battery_discharge_cutoff_voltage",
        icon="mdi:battery-alert-variant-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=20.0,
        native_max_value=24.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="battery_discharge_cutoff_voltage",
        command_prefix="EOD",
        command_width=3,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="battery_discharge_alarm_voltage",
        translation_key="battery_discharge_alarm_voltage",
        icon="mdi:battery-alert",
        entity_category=EntityCategory.CONFIG,
        native_min_value=20.6,
        native_max_value=27.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="battery_discharge_alarm_voltage",
        command_prefix="TBLV",
        command_width=4,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="low_power_discharge_time",
        translation_key="low_power_discharge_time",
        icon="mdi:timer-sand",
        entity_category=EntityCategory.CONFIG,
        native_min_value=1,
        native_max_value=8,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        read_key="low_power_discharge_time",
        command_prefix="LWDT",
        command_width=4,
    ),
    LvyuanNumberDescription(
        key="battery_to_grid_voltage",
        translation_key="battery_to_grid_voltage",
        icon="mdi:battery-arrow-up",
        entity_category=EntityCategory.CONFIG,
        native_min_value=22.0,
        native_max_value=26.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="battery_to_grid_voltage",
        command_prefix="BTG",
        command_width=3,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="grid_to_battery_voltage",
        translation_key="grid_to_battery_voltage",
        icon="mdi:battery-arrow-down",
        entity_category=EntityCategory.CONFIG,
        native_min_value=24.0,
        native_max_value=29.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="grid_to_battery_voltage",
        command_prefix="BTB",
        command_width=3,
        is_scaled=True,
    ),
    LvyuanNumberDescription(
        key="battery_overvoltage_protection_voltage",
        translation_key="battery_overvoltage_protection_voltage",
        icon="mdi:battery-alert-variant",
        entity_category=EntityCategory.CONFIG,
        native_min_value=28.0,
        native_max_value=32.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="battery_overvoltage_protection_voltage",
        command_prefix="BTO",
        command_width=3,
        is_scaled=True,
    ),

    # --- System ---
    LvyuanNumberDescription(
        key="grid_overvoltage_protection",
        translation_key="grid_overvoltage_protection",
        icon="mdi:flash-alert",
        entity_category=EntityCategory.CONFIG,
        native_min_value=264,
        native_max_value=280,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="grid_overvoltage_protection",
        command_prefix="OVP",
        command_width=3,
    ),
    LvyuanNumberDescription(
        key="grid_undervoltage_protection",
        translation_key="grid_undervoltage_protection",
        icon="mdi:flash-alert-outline",
        entity_category=EntityCategory.CONFIG,
        native_min_value=90,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        read_key="grid_undervoltage_protection",
        command_prefix="LVP",
        command_width=3,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LVYUAN number entities."""
    runtime: LvyuanRuntimeData = entry.runtime_data
    serial_device = entry.data.get(CONF_SERIAL_DEVICE, entry.entry_id)
    
    entities = [
        LvyuanNumber(runtime, entry, description, serial_device)
        for description in NUMBERS
    ]
    async_add_entities(entities)


class LvyuanNumber(CoordinatorEntity, NumberEntity):
    """Representation of a LVYUAN number entity."""

    entity_description: LvyuanNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: LvyuanRuntimeData,
        entry: ConfigEntry,
        description: LvyuanNumberDescription,
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
    def native_value(self) -> float | None:
        """Return the current value."""
        settings = self.coordinator.data.get("settings", {})
        value = settings.get(self.entity_description.read_key)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        desc = self.entity_description
        
        if desc.is_scaled:
            # Для напряжений: отправляем как есть с 1 знаком после запятой (27.4)
            formatted = f"{value:.1f}"
            command = f"{desc.command_prefix}{formatted}"
        else:
            # Для токов/времен: отправляем как целое число с padding
            int_value = int(value)
            command = f"{desc.command_prefix}{int_value:0{desc.command_width}d}"
        
        await self.runtime.coordinator.async_send_write_command(command)