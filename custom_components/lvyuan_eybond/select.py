"""Select platform for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_DEVICE, DOMAIN
from .coordinator import LvyuanRuntimeData

_LOGGER = logging.getLogger(__name__)

# --- Маппинги команд ---
OUTPUT_MODE_MAP = {
    "Appliance mode": "00",
    "UPS mode": "01",
}

OUTPUT_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "PV > Battery > Utility": "02",
}

CHARGING_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "Utility + PV": "02",
    "PV only": "03",
}

BATTERY_TYPE_MAP = {
    "Lead-acid": "0",
    "Flooded": "1",
    "Lithium": "2",
    "Custom": "3",
}

OUTPUT_VOLTAGE_MAP = {
    "208 V": "208",
    "220 V": "220",
    "230 V": "230",
    "240 V": "240",
}

CHARGING_METHOD_MAP = {
    "Auto": "00",
    "Forced 2-stage": "01",
    "Forced 3-stage": "02",
}

AC_INPUT_RANGE_MAP = {
    "APL (Wide 90-280V)": "0",
    "UPS (Narrow 170-280V)": "1",
}


@dataclass(frozen=True, kw_only=True)
class LvyuanSelectDescription(SelectEntityDescription):
    """Описание селекта LVYUAN."""
    read_key: str
    command_prefix: str
    option_map: dict[str, str]
    expected_code_length: int = 2


SELECTS: tuple[LvyuanSelectDescription, ...] = (
    LvyuanSelectDescription(
        key="output_mode",
        translation_key="output_mode",
        icon="mdi:transmission-tower",
        entity_category=EntityCategory.CONFIG,
        read_key="output_mode_code",
        command_prefix="OPM",
        option_map=OUTPUT_MODE_MAP,
        expected_code_length=2,
    ),
    LvyuanSelectDescription(
        key="output_priority",
        translation_key="output_priority",
        icon="mdi:priority-high",
        entity_category=EntityCategory.CONFIG,
        read_key="output_source_priority_code",
        command_prefix="OPR",
        option_map=OUTPUT_PRIORITY_MAP,
        expected_code_length=2,
    ),
    LvyuanSelectDescription(
        key="charging_priority",
        translation_key="charging_priority",
        icon="mdi:battery-charging",
        entity_category=EntityCategory.CONFIG,
        read_key="charger_source_priority_code",
        command_prefix="CPR",
        option_map=CHARGING_PRIORITY_MAP,
        expected_code_length=2,
    ),
    LvyuanSelectDescription(
        key="battery_type",
        translation_key="battery_type",
        icon="mdi:battery",
        entity_category=EntityCategory.CONFIG,
        read_key="battery_type_code",
        command_prefix="TBAT",
        option_map=BATTERY_TYPE_MAP,
        expected_code_length=1,
    ),
    LvyuanSelectDescription(
        key="output_voltage_setting",
        translation_key="output_voltage_setting",
        icon="mdi:sine-wave",
        entity_category=EntityCategory.CONFIG,
        read_key="output_voltage_code",
        command_prefix="V",
        option_map=OUTPUT_VOLTAGE_MAP,
        expected_code_length=3,
    ),
    LvyuanSelectDescription(
        key="charging_method",
        translation_key="charging_method",
        icon="mdi:battery-charging-100",
        entity_category=EntityCategory.CONFIG,
        read_key="charging_method_code",
        command_prefix="CST",
        option_map=CHARGING_METHOD_MAP,
        expected_code_length=2,
    ),
    LvyuanSelectDescription(
        key="ac_input_range",
        translation_key="ac_input_range",
        icon="mdi:flash",
        entity_category=EntityCategory.CONFIG,
        read_key="ac_input_range_code",
        command_prefix="HV",
        option_map=AC_INPUT_RANGE_MAP,
        expected_code_length=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LVYUAN select entities."""
    runtime: LvyuanRuntimeData = entry.runtime_data
    serial_device = entry.data.get(CONF_SERIAL_DEVICE, entry.entry_id)
    
    entities = [
        LvyuanSelect(runtime, entry, description, serial_device)
        for description in SELECTS
    ]
    async_add_entities(entities)


class LvyuanSelect(CoordinatorEntity, SelectEntity):
    """Representation of a LVYUAN select entity."""

    entity_description: LvyuanSelectDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: LvyuanRuntimeData,
        entry: ConfigEntry,
        description: LvyuanSelectDescription,
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

    def _normalize_code(self, code: str) -> str:
        """Нормализовать код, добавив ведущие нули если нужно."""
        code = str(code).strip()
        if len(code) < self.entity_description.expected_code_length:
            code = code.zfill(self.entity_description.expected_code_length)
        return code

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        settings = self.coordinator.data.get("settings", {})
        current_code = settings.get(self.entity_description.read_key)
        
        if current_code is None:
            _LOGGER.debug(
                "No value for %s in settings",
                self.entity_description.read_key
            )
            return None
        
        normalized_code = self._normalize_code(current_code)
        
        reverse_map = {
            self._normalize_code(v): k 
            for k, v in self.entity_description.option_map.items()
        }
        
        option = reverse_map.get(normalized_code)
        
        if option is None:
            _LOGGER.warning(
                "Unknown code '%s' (normalized: '%s') for %s",
                current_code,
                normalized_code,
                self.entity_description.read_key
            )
        
        return option

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        return list(self.entity_description.option_map.keys())

    async def async_select_option(self, option: str) -> None:
        """Set the select option."""
        suffix = self.entity_description.option_map.get(option)
        if suffix is None:
            raise ValueError(f"Unknown option '{option}'")
        
        command = f"{self.entity_description.command_prefix}{suffix}"
        _LOGGER.info("Sending command: %s", command)
        
        try:
            await self.runtime.coordinator.async_send_write_command(command)
        except Exception as err:
            _LOGGER.error(
                "Failed to send command '%s': %s",
                command,
                err
            )
            raise