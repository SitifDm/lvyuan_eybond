"""Binary sensor platform for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_DEVICE, DOMAIN
from .coordinator import LvyuanRuntimeData


@dataclass(frozen=True, kw_only=True)
class LvyuanBinarySensorDescription(BinarySensorEntityDescription):
    """Описание бинарного сенсора LVYUAN."""
    value_fn: Callable[[dict[str, Any]], bool | None]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None


# --- Binary sensors ---
BINARY_SENSORS: tuple[LvyuanBinarySensorDescription, ...] = (
    # --- Зарядка батареи ---
    LvyuanBinarySensorDescription(
        key="battery_charging",
        translation_key="battery_charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: (
            data.get("battery_current", 0) > 0
            if data.get("battery_current") is not None
            else None
        ),
    ),

    LvyuanBinarySensorDescription(
        key="battery_discharging",
        translation_key="battery_discharging",
        device_class=BinarySensorDeviceClass.BATTERY,
        value_fn=lambda data: (
            data.get("battery_current", 0) < 0
            if data.get("battery_current") is not None
            else None
        ),
    ),

    # --- PV зарядка ---
    LvyuanBinarySensorDescription(
        key="pv_charging",
        translation_key="pv_charging",
        icon="mdi:solar-power",
        value_fn=lambda data: (
            data.get("pv_charging_current", 0) > 0
            if data.get("pv_charging_current") is not None
            else None
        ),
    ),

    # --- PV статусы ---
    LvyuanBinarySensorDescription(
        key="pv_tracking",
        translation_key="pv_tracking",
        icon="mdi:solar-power-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("pv_tracking_status") == "01",
    ),

    LvyuanBinarySensorDescription(
        key="pv_chargeable",
        translation_key="pv_chargeable",
        icon="mdi:battery-charging",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("pv_chargeable_status") == "1",
    ),

    # --- Вентиляторы ---
    LvyuanBinarySensorDescription(
        key="fan1_stopped",
        translation_key="fan1_stopped",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:fan-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("fan1_stopped"),
    ),

    LvyuanBinarySensorDescription(
        key="fan2_stopped",
        translation_key="fan2_stopped",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:fan-alert",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("fan2_stopped"),
    ),

    # --- Ошибки и предупреждения ---
    LvyuanBinarySensorDescription(
        key="fault",
        translation_key="fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: (
            int(data.get("fault_code", 0)) != 0
            if data.get("fault_code") is not None
            else None
        ),
        attributes_fn=lambda data: {"fault_code": data.get("fault_code")},
    ),

    LvyuanBinarySensorDescription(
        key="warning",
        translation_key="warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: (
            data.get("warning_status", 0) != 0
            if data.get("warning_status") is not None
            else None
        ),
        attributes_fn=lambda data: {
            "warning_status_1": data.get("warning_status_1"),
            "warning_status_2": data.get("warning_status_2"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LVYUAN binary sensors."""
    runtime: LvyuanRuntimeData = entry.runtime_data
    serial_device = entry.data.get(CONF_SERIAL_DEVICE, entry.entry_id)

    async_add_entities(
        LvyuanBinarySensor(runtime, entry, description, serial_device)
        for description in BINARY_SENSORS
    )


class LvyuanBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a LVYUAN binary sensor."""

    entity_description: LvyuanBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: LvyuanRuntimeData,
        entry: ConfigEntry,
        description: LvyuanBinarySensorDescription,
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
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attributes_fn is not None:
            return self.entity_description.attributes_fn(self.coordinator.data)
        return None