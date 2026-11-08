"""LVYUAN Inverter (EyeBond G-ASCII) integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import UpdateFailed

from .client import LvyuanError
from .client_serial import LvyuanSerialClient
from .const import (
    ATTR_COMMAND,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_EXPECT_RESPONSE,
    ATTR_REFRESH,
    CONF_BAUDRATE,
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_DEVICE,
    CONF_TIMEOUT,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERIAL_DEVICE,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    SERVICE_REFRESH,
    SERVICE_SEND_COMMAND,
)
from .coordinator import LvyuanCoordinator, LvyuanRuntimeData

_LOGGER = logging.getLogger(__name__)

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): str,
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Optional(ATTR_EXPECT_RESPONSE, default=True): cv.boolean,
        vol.Optional(ATTR_REFRESH, default=False): cv.boolean,
    }
)
REFRESH_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIG_ENTRY_ID): str})


def _get_loaded_runtime_data(hass: HomeAssistant, config_entry_id: str) -> LvyuanRuntimeData:
    entry = hass.config_entries.async_get_entry(config_entry_id)
    if entry is None:
        raise ServiceValidationError("Config entry not found")
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError("Config entry is not loaded")
    return cast(LvyuanRuntimeData, entry.runtime_data)


def _build_client(entry: ConfigEntry) -> LvyuanSerialClient:
    """Build a serial client for LVYUAN inverter."""
    return LvyuanSerialClient(
        device=entry.options.get(
            CONF_SERIAL_DEVICE,
            entry.data.get(CONF_SERIAL_DEVICE, DEFAULT_SERIAL_DEVICE),
        ),
        baudrate=int(
            entry.options.get(
                CONF_BAUDRATE, entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
            )
        ),
        timeout=int(
            entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))
        ),
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up LVYUAN services."""
    
    async def async_send_command(call: ServiceCall) -> ServiceResponse | None:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        command = call.data[ATTR_COMMAND]
        
        response = await runtime.coordinator.async_send_write_command(command)
        
        if call.return_response:
            return {"command": command, "response": response}
        return None

    async def async_refresh(call: ServiceCall) -> ServiceResponse:
        runtime = _get_loaded_runtime_data(hass, call.data[ATTR_CONFIG_ENTRY_ID])
        await runtime.coordinator.async_refresh()
        return {"refreshed": True}

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_COMMAND,
            async_send_command,
            schema=SEND_COMMAND_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
        
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH,
            async_refresh,
            schema=REFRESH_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )
        
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a LVYUAN config entry."""
    client = _build_client(entry)
    
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    
    coordinator = LvyuanCoordinator(
        hass,
        client=client,
        name=entry.title,
        update_interval=timedelta(seconds=scan_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except (LvyuanError, UpdateFailed) as err:
        _LOGGER.warning("First refresh failed, will retry: %s", err)
        raise ConfigEntryNotReady(str(err)) from err
    except HomeAssistantError as err:
        _LOGGER.warning("First refresh failed with HA error: %s", err)
        raise ConfigEntryNotReady(str(err)) from err
    except Exception as err:
        _LOGGER.error("Unexpected error during first refresh: %s", err, exc_info=True)
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = LvyuanRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = getattr(entry, "runtime_data", None)
        client = getattr(runtime, "client", None)
        if client and hasattr(client, "close"):
            await client.close()
    return unloaded