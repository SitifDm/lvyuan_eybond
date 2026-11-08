"""Config flow for LVYUAN Inverter (EyeBond G-ASCII)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .client import LvyuanError
from .client_serial import LvyuanSerialClient
from .const import (
    CONF_BAUDRATE,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_DEVICE,
    CONF_TIMEOUT,
    DEFAULT_BAUDRATE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERIAL_DEVICE,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

TIMEOUT_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=1,
        max=60,
        step=1,
        mode=selector.NumberSelectorMode.SLIDER,
        unit_of_measurement="s",
    )
)

SCAN_INTERVAL_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=2,
        max=3600,
        step=1,
        mode=selector.NumberSelectorMode.SLIDER,
        unit_of_measurement="s",
    )
)

SERIAL_DEVICE_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
)

# Для LVYUAN скорость фиксирована на 9600, но оставим селектор для единообразия
BAUDRATE_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=["9600"],
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)


async def _probe_client(user_input: dict[str, Any]) -> str:
    """Probe the inverter to verify connection."""
    client = LvyuanSerialClient(
        device=user_input.get(CONF_SERIAL_DEVICE, DEFAULT_SERIAL_DEVICE),
        baudrate=int(user_input.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
        timeout=int(user_input[CONF_TIMEOUT]),
    )
    try:
        # Пробуем отправить простую команду 'F' для проверки связи
        response = await client.send_command("F", expect_response=True)
        if response and (response.startswith("#") or response.startswith("(")):
            return user_input.get(CONF_SERIAL_DEVICE, DEFAULT_SERIAL_DEVICE)
        raise LvyuanError("Invalid response from inverter")
    finally:
        await client.close()


def _base_fields() -> dict[Any, Any]:
    return {
        vol.Required(CONF_SERIAL_DEVICE, default=DEFAULT_SERIAL_DEVICE): SERIAL_DEVICE_SELECTOR,
        vol.Optional(CONF_BAUDRATE, default=str(DEFAULT_BAUDRATE)): BAUDRATE_SELECTOR,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
        vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): TIMEOUT_SELECTOR,
    }


class LvyuanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LVYUAN Inverter."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_BAUDRATE] = int(user_input.get(CONF_BAUDRATE, DEFAULT_BAUDRATE))
            try:
                serial_id = await _probe_client(user_input)
            except LvyuanError:
                _LOGGER.debug("Lvyuan probe failed", exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(serial_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    **_base_fields(),
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> "LvyuanOptionsFlow":
        return LvyuanOptionsFlow()


class LvyuanOptionsFlow(config_entries.OptionsFlowWithReload):
    """LVYUAN options flow."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_BAUDRATE] = int(user_input.get(CONF_BAUDRATE, DEFAULT_BAUDRATE))
            try:
                await _probe_client(user_input)
            except LvyuanError:
                _LOGGER.debug("Lvyuan options probe failed", exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(data=user_input)
        
        options_schema = vol.Schema(_base_fields())
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema,
                {
                    CONF_SERIAL_DEVICE: self.config_entry.options.get(
                        CONF_SERIAL_DEVICE,
                        self.config_entry.data.get(CONF_SERIAL_DEVICE, DEFAULT_SERIAL_DEVICE),
                    ),
                    CONF_BAUDRATE: str(
                        self.config_entry.options.get(
                            CONF_BAUDRATE,
                            self.config_entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
                        )
                    ),
                    CONF_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ),
                    CONF_TIMEOUT: self.config_entry.options.get(
                        CONF_TIMEOUT,
                        self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ),
                },
            ),
            errors=errors,
        )