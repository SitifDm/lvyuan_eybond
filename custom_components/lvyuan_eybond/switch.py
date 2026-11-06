"""Switch platform for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_DEVICE, DOMAIN
from .coordinator import LvyuanRuntimeData


@dataclass(frozen=True, kw_only=True)
class LvyuanSwitchDescription(SwitchEntityDescription):
    """Описание переключателя LVYUAN."""
    is_on_fn: Callable[[dict[str, Any]], bool | None]
    turn_on_command: str
    turn_off_command: str
    flag_char: str | None = None


def _get_te_flags(data: dict[str, Any]) -> str:
    """Получить строку флагов из ответа TE?.
    
    Ищет в нескольких местах: сначала в slow_data.raw_slow (медленный цикл),
    потом в raw (быстрый цикл), потом в верхнем уровне данных.
    """
    try:
        # Сначала пробуем из slow_data (медленный цикл, раз в 5 минут)
        te_response = data.get("slow_data", {}).get("raw_slow", {}).get("TE?", "")
        if not te_response:
            # Пробуем из raw (быстрый цикл)
            te_response = data.get("raw", {}).get("TE?", "")
        if not te_response:
            # Пробуем из верхнего уровня (если TE? был добавлен туда)
            te_response = data.get("te_flags_raw", "")
        if not te_response:
            return ""
        return te_response.strip().lstrip("(")
    except Exception:
        return ""


def _is_flag_on(data: dict[str, Any], flag_char: str) -> bool | None:
    """Проверить, включен ли флаг в строке TE?."""
    flags = _get_te_flags(data)
    if not flags:
        return None
    return flag_char in flags


# --- Switch entities ---
SWITCHES: tuple[LvyuanSwitchDescription, ...] = (
    # BMS Communication (TDS/TES) - флаг 'S' или 'B'
    LvyuanSwitchDescription(
        key="bms_communication",
        translation_key="bms_communication",
        icon="mdi:battery-sync",
        entity_category=EntityCategory.CONFIG,
        flag_char="S",
        is_on_fn=lambda data: _is_flag_on(data, "S") or _is_flag_on(data, "B"),
        turn_on_command="TES",
        turn_off_command="TDS",
    ),

    # Energy Saving Mode (TDI/TEI) - флаг 'I'
    LvyuanSwitchDescription(
        key="energy_saving_mode",
        translation_key="energy_saving_mode",
        icon="mdi:leaf",
        entity_category=EntityCategory.CONFIG,
        flag_char="I",
        is_on_fn=lambda data: _is_flag_on(data, "I"),
        turn_on_command="TEI",
        turn_off_command="TDI",
    ),

    # Battery Equalization (TDQ/TEQ) - флаг 'Q'
    LvyuanSwitchDescription(
        key="battery_equalization",
        translation_key="battery_equalization",
        icon="mdi:battery-sync",
        entity_category=EntityCategory.CONFIG,
        flag_char="Q",
        is_on_fn=lambda data: _is_flag_on(data, "Q"),
        turn_on_command="TEQ",
        turn_off_command="TDQ",
    ),

    # Battery Not Connected Alarm (TDL/TEL) - флаг 'L'
    LvyuanSwitchDescription(
        key="battery_not_connected_alarm",
        translation_key="battery_not_connected_alarm",
        icon="mdi:battery-alert",
        entity_category=EntityCategory.CONFIG,
        flag_char="L",
        is_on_fn=lambda data: _is_flag_on(data, "L"),
        turn_on_command="TEL",
        turn_off_command="TDL",
    ),

    # Buzzer Silent Mode (TDO/TEO) - флаг 'O'
    LvyuanSwitchDescription(
        key="buzzer_silent_mode",
        translation_key="buzzer_silent_mode",
        icon="mdi:volume-off",
        entity_category=EntityCategory.CONFIG,
        flag_char="O",
        is_on_fn=lambda data: _is_flag_on(data, "O"),
        turn_on_command="TEO",
        turn_off_command="TDO",
    ),

    # Inverter Soft Start Relay (TDY/TEY) - флаг 'Y'
    LvyuanSwitchDescription(
        key="inverter_soft_start",
        translation_key="inverter_soft_start",
        icon="mdi:power-plug-battery",
        entity_category=EntityCategory.CONFIG,
        flag_char="Y",
        is_on_fn=lambda data: _is_flag_on(data, "Y"),
        turn_on_command="TEY",
        turn_off_command="TDY",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LVYUAN switch entities."""
    runtime: LvyuanRuntimeData = entry.runtime_data
    serial_device = entry.data.get(CONF_SERIAL_DEVICE, entry.entry_id)
    
    entities = [
        LvyuanSwitch(runtime, entry, description, serial_device)
        for description in SWITCHES
    ]
    async_add_entities(entities)


class LvyuanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a LVYUAN switch entity."""

    entity_description: LvyuanSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: LvyuanRuntimeData,
        entry: ConfigEntry,
        description: LvyuanSwitchDescription,
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
    def is_on(self) -> bool | None:
        """Return true if switch is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.turn_on_command
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.runtime.coordinator.async_send_write_command(
            self.entity_description.turn_off_command
        )