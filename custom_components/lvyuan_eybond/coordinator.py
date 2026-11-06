"""Coordinator for LVYUAN Inverter (EyeBond G-ASCII) - Optimized with Fast/Slow cycles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import LvyuanError
from .client_serial import LvyuanSerialClient
from .const import (
    EYBOND_MODE_CODES,
    EYBOND_OUTPUT_PRIORITY_REVERSE,
    EYBOND_OUTPUT_MODE_REVERSE,
    EYBOND_BATTERY_TYPE_REVERSE,
    EYBOND_CHARGER_PRIORITY_REVERSE,
    EYBOND_CHARGING_METHOD_REVERSE,
    EYBOND_OUTPUT_VOLTAGE_REVERSE,
    EYBOND_AC_INPUT_RANGE_REVERSE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class LvyuanRuntimeData:
    """Runtime data stored on the config entry."""
    client: LvyuanSerialClient
    coordinator: "LvyuanCoordinator"


def parse_eybond_response(response: str) -> list[str]:
    """Parse EyeBond response like '(val1 val2 val3' or '#val1 val2' into a list."""
    if not response:
        return []
    if response.startswith("(") or response.startswith("#"):
        return response[1:].split()
    return response.split()


def safe_float(value: str, default: float | None = None) -> float | None:
    """Safely convert string to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: str, default: int | None = None) -> int | None:
    """Safely convert string to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class LvyuanCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate LVYUAN polling with smart fast/slow cycles."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        client: LvyuanSerialClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.client = client
        self.serial: str | None = None
        self.model_name: str = "TY-SIC-3.6KBE-W1"
        
        # Счетчик циклов для разделения быстрых и тяжелых команд
        self._loop_counter = 0

    async def _async_setup(self) -> None:
        """Fetch static data quickly without blocking Home Assistant startup."""
        self.serial = "lvyuan_eybond"
        _LOGGER.debug("Lvyuan coordinator successfully initialized in fast mode")

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll the inverter with smart conditional heavy polling."""
        self._loop_counter += 1
        
        try:
            # === БЫСТРЫЙ ЦИКЛ (выполняется каждые 5 секунд) ===
            hmod = await self.client.send_command("GMOD")
            await asyncio.sleep(0.05)
            
            hbat = await self.client.send_command("GBAT")
            await asyncio.sleep(0.05)
            
            hpv = await self.client.send_command("GPV")
            await asyncio.sleep(0.05)
            
            hop = await self.client.send_command("GOP")
            await asyncio.sleep(0.05)
            
            hpd = await self.client.send_command("GPDAT0")
            await asyncio.sleep(0.05)
            
            hws = await self.client.send_command("GWS")
            await asyncio.sleep(0.05)
            
            hgrid = await self.client.send_command("GLINE")
            await asyncio.sleep(0.05)

            # Добавляем Q1 для температуры инвертора
            hq1 = await self.client.send_command("Q1")
            await asyncio.sleep(0.05)

            # Парсинг быстрых данных
            hmod_vals = parse_eybond_response(hmod)
            mode_code = hmod_vals[0] if hmod_vals else "X"
            
            hbat_vals = parse_eybond_response(hbat)
            hpv_vals = parse_eybond_response(hpv)
            hop_vals = parse_eybond_response(hop)
            hpd_vals = parse_eybond_response(hpd)
            hws_vals = parse_eybond_response(hws)
            hgrid_vals = parse_eybond_response(hgrid)
            hq1_vals = parse_eybond_response(hq1)

            # === МЕДЛЕННЫЙ ЦИКЛ (выполняется 1 раз в 60 циклов = ~5 минут) ===
            slow_data = self.data.get("slow_data") if self.data else None
            
            if self._loop_counter == 1 or self._loop_counter >= 60:
                _LOGGER.debug("Loop %d: Запрос тяжелых команд (настройки и диагностика)...", self._loop_counter)
                self._loop_counter = 1
                slow_data = await self._async_update_slow_data()

            # === СБОРКА РЕЗУЛЬТАТА ===
            result: dict[str, Any] = {
                "operating_mode": mode_code,
                "operating_mode_name": EYBOND_MODE_CODES.get(mode_code, "unknown"),
                "slow_data": slow_data or {},
                "raw": {
                    "GMOD": hmod, "GBAT": hbat, "GPV": hpv, "GOP": hop,
                    "GPDAT0": hpd, "GWS": hws, "GLINE": hgrid,
                    "Q1": hq1,
                }
            }

            # Парсинг GBAT
            if len(hbat_vals) >= 5:
                result["battery_voltage"] = safe_float(hbat_vals[0])
                result["battery_current"] = safe_float(hbat_vals[1])
                if "settings" not in (slow_data or {}):
                    result["battery_type_code"] = hbat_vals[2]
                    result["battery_type_name"] = EYBOND_BATTERY_TYPE_REVERSE.get(hbat_vals[2], "unknown")
                result["battery_cutoff_voltage"] = safe_float(hbat_vals[3])
                result["battery_alarm_voltage"] = safe_float(hbat_vals[4])

            # Парсинг GPV
            if len(hpv_vals) >= 5:
                result["pv_voltage"] = safe_float(hpv_vals[0])
                result["pv_charging_current"] = safe_float(hpv_vals[2])
                result["pv_current"] = safe_float(hpv_vals[3])
                result["pv_power"] = safe_float(hpv_vals[4])
            if len(hpv_vals) > 5: result["pv_tracking_status"] = hpv_vals[5]
            if len(hpv_vals) > 6: result["pv_chargeable_status"] = hpv_vals[6]
            if len(hpv_vals) > 20: result["pv_energy_today"] = safe_float(hpv_vals[20]) / 100
            if len(hpv_vals) > 22:
                pv_total_raw = int(hpv_vals[21]) * 10000 + int(hpv_vals[22])
                result["pv_energy_total"] = pv_total_raw / 100

            # Парсинг GOP
            if len(hop_vals) >= 5:
                result["output_voltage"] = safe_float(hop_vals[0])
                result["output_frequency"] = safe_float(hop_vals[1])
                result["output_current"] = safe_float(hop_vals[2])
                result["output_active_power"] = safe_float(hop_vals[4])
            if len(hop_vals) > 9: result["output_load_percentage"] = safe_float(hop_vals[9])
            if len(hop_vals) > 12: result["output_energy_today"] = safe_float(hop_vals[12]) / 100
            if len(hop_vals) > 14:
                output_total_raw = int(hop_vals[13]) * 10000 + int(hop_vals[14])
                result["output_energy_total"] = output_total_raw / 100

            # Парсинг GPDAT0
            if len(hpd_vals) >= 22:
                result["inverter_voltage"] = safe_float(hpd_vals[5])
                result["inverter_frequency"] = safe_float(hpd_vals[6])
                result["grid_voltage_gpdat0"] = safe_float(hpd_vals[7])
                result["grid_frequency_gpdat0"] = safe_float(hpd_vals[8])
                result["battery_capacity"] = safe_float(hpd_vals[17])
                result["pv_power_gpdat0"] = safe_float(hpd_vals[20])
                result["mainboard_temperature"] = safe_float(hpd_vals[21])

            # Парсинг GLINE
            if len(hgrid_vals) >= 8:
                result["grid_voltage"] = safe_float(hgrid_vals[0])
                result["grid_frequency"] = safe_float(hgrid_vals[1])
                result["grid_loss_high_voltage"] = safe_float(hgrid_vals[2])
                result["grid_loss_low_voltage"] = safe_float(hgrid_vals[3])
                result["grid_restore_high_voltage"] = safe_float(hgrid_vals[4])
                result["grid_restore_low_voltage"] = safe_float(hgrid_vals[5])
                result["grid_loss_high_frequency"] = safe_float(hgrid_vals[6])
                result["grid_loss_low_frequency"] = safe_float(hgrid_vals[7])
            if len(hgrid_vals) > 9: result["grid_energy_today"] = safe_float(hgrid_vals[9]) / 100
            if len(hgrid_vals) > 12:
                grid_total_raw = int(hgrid_vals[11]) * 10000 + int(hgrid_vals[12])
                result["grid_energy_total"] = grid_total_raw / 100

            # Парсинг GWS
            if len(hws_vals) >= 3:
                result["fault_code"] = safe_int(hws_vals[0], 0)
                result["warning_status_1"] = hws_vals[1]
                result["warning_status_2"] = hws_vals[2]
                has_warning = ("1" in hws_vals[1]) or ("1" in hws_vals[2])
                result["warning_status"] = 1 if has_warning else 0

            # Парсинг Q1 для температуры инвертора
            if len(hq1_vals) >= 8:
                result["inverter_temperature"] = safe_float(hq1_vals[6])

            # Добавляем медленные данные (если они есть), чтобы сенсоры не мигали
            if slow_data:
                result.update(slow_data)
                if "raw_slow" in slow_data:
                    result["raw"].update(slow_data["raw_slow"])

            return result

        except LvyuanError as err:
            raise UpdateFailed(f"Failed to read data from inverter: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error parsing data: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error during polling: {err}") from err

    async def _async_update_slow_data(self) -> dict[str, Any]:
        """Update slow-changing data (settings and diagnostics) safely."""
        slow_result: dict[str, Any] = {}
        settings: dict[str, Any] = {}
        raw_slow: dict[str, str] = {}
        
        read_commands = [
            ("CHGC???", "max_charging_current", safe_int),
            ("GCC???", "max_utility_charging_current", safe_int),
            ("CST??", "charging_method_code", str),
            ("TCCV????", "constant_voltage_charging_voltage", safe_float),
            ("TCFV????", "float_charging_voltage", safe_float),
            ("TCQV????", "equalization_charging_voltage", safe_float),
            ("TCVT????", "constant_voltage_charging_time", safe_int),
            ("TCQT????", "equalization_charging_time", safe_int),
            ("TCQO????", "equalization_timeout", safe_int),
            ("TCQI????", "equalization_interval", safe_int),
            ("EOD????", "battery_discharge_cutoff_voltage", safe_float),
            ("TBLV????", "battery_discharge_alarm_voltage", safe_float),
            ("LWDT????", "low_power_discharge_time", safe_int),
            ("BTG????", "battery_to_grid_voltage", safe_float),
            ("BTB????", "grid_to_battery_voltage", safe_float),
            ("BTO????", "battery_overvoltage_protection_voltage", safe_float),
            ("OVP???", "grid_overvoltage_protection", safe_int),
            ("LVP???", "grid_undervoltage_protection", safe_int),
            ("CI1??", "constant_current_charging_max_time", safe_int),
            ("TBAT?", "battery_type_code", str),
            ("CPR??", "charger_source_priority_code", str),
            ("OPM??", "output_mode_code", str),
            ("OPR??", "output_source_priority_code", str),
            ("V???", "output_voltage_code", str),
            ("HV?", "ac_input_range_code", str),
        ]

        for cmd, key, type_fn in read_commands:
            try:
                resp = await self.client.send_command(cmd)
                raw_slow[cmd] = resp
                vals = parse_eybond_response(resp)
                if vals:
                    settings[key] = type_fn(vals[0])
                await asyncio.sleep(0.05)
            except Exception as err:
                _LOGGER.debug("Slow command %s skipped this turn: %s", cmd, err)

        # Нормализация кодов
        if "output_voltage_code" in settings:
            settings["output_voltage_code"] = str(settings["output_voltage_code"]).split()[0]

        slow_result["settings"] = settings

        # Диагностические команды
        diag_commands = [
            ("SVFW", self._parse_svfw),
            ("GTMP", self._parse_gtmp),
            ("GCHG", self._parse_gchg),
            ("FAN???", self._parse_fan),
            ("TE?", self._parse_te),
            ("GINV", self._parse_ginv),
        ]

        for cmd, parser_fn in diag_commands:
            try:
                resp = await self.client.send_command(cmd)
                raw_slow[cmd] = resp
                parsed = parser_fn(resp)
                if parsed:
                    slow_result.update(parsed)
                await asyncio.sleep(0.05)
            except Exception as err:
                _LOGGER.debug("Diagnostic command %s skipped this turn: %s", cmd, err)

        # Маппинги
        if "battery_type_code" in settings:
            slow_result["battery_type_name"] = EYBOND_BATTERY_TYPE_REVERSE.get(settings["battery_type_code"], "unknown")
        if "charger_source_priority_code" in settings:
            slow_result["charger_source_priority_name"] = EYBOND_CHARGER_PRIORITY_REVERSE.get(settings["charger_source_priority_code"], "unknown")
        if "output_source_priority_code" in settings:
            slow_result["output_source_priority_name"] = EYBOND_OUTPUT_PRIORITY_REVERSE.get(settings["output_source_priority_code"], "unknown")
        if "output_mode_code" in settings:
            slow_result["output_mode_name"] = EYBOND_OUTPUT_MODE_REVERSE.get(settings["output_mode_code"], "unknown")
        if "ac_input_range_code" in settings:
            slow_result["ac_input_range_name"] = EYBOND_AC_INPUT_RANGE_REVERSE.get(settings["ac_input_range_code"], "unknown")

        slow_result["raw_slow"] = raw_slow

        _LOGGER.debug("Slow data updated successfully")
        return slow_result

    # --- Вспомогательные парсеры для медленных данных ---
    def _parse_svfw(self, payload: str) -> dict[str, Any] | None:
        vals = parse_eybond_response(payload)
        if len(vals) >= 2:
            return {"software_version": vals[0], "software_date": vals[1].replace("(", "")}
        return None

    def _parse_gtmp(self, payload: str) -> dict[str, Any] | None:
        vals = parse_eybond_response(payload)
        if len(vals) >= 3:
            return {
                "pv_temperature": safe_float(vals[0]),
                "charger_temperature": safe_float(vals[1]),
                "ambient_temperature": safe_float(vals[2])
            }
        return None

    def _parse_gchg(self, payload: str) -> dict[str, Any] | None:
        vals = parse_eybond_response(payload)
        if len(vals) >= 18:
            return {
                "constant_voltage_charging_voltage": safe_float(vals[6]),
                "float_charging_voltage": safe_float(vals[7]),
                "equalization_charging_voltage": safe_float(vals[8]),
                "max_charging_current": safe_float(vals[9]),
                "equalization_interval": safe_int(vals[13]),
                "low_power_discharge_time": safe_int(vals[16])
            }
        return None

    def _parse_fan(self, payload: str) -> dict[str, Any] | None:
        vals = parse_eybond_response(payload)
        if len(vals) >= 5:
            return {
                "fan_speed_percentage": safe_float(vals[0]),
                "fan1_speed": safe_float(vals[1]),
                "fan2_speed": safe_float(vals[2]),
                "fan1_stopped": vals[3] == "1",
                "fan2_stopped": vals[4] == "1"
            }
        return None

    def _parse_te(self, payload: str) -> dict[str, Any] | None:
        """Парсинг буквенных флагов TE? с сохранением сырой строки для switch.py"""
        vals = parse_eybond_response(payload)
        if vals:
            flags_str = vals[0]
            return {
                "buzzer_enabled": "O" not in flags_str,
                "bms_enabled": "S" in flags_str or "B" in flags_str,
                "te_flags_raw": flags_str,
            }
        return None

    def _parse_ginv(self, payload: str) -> dict[str, Any] | None:
        vals = parse_eybond_response(payload)
        if len(vals) >= 3:
            return {
                "inverter_voltage": safe_float(vals[0]),
                "inverter_frequency": safe_float(vals[1]),
                "inverter_current": safe_float(vals[2])
            }
        return None

    async def async_send_write_command(self, command: str) -> str:
        """Send a write command and instantly optimize HA cache."""
        response = await self.client.send_command(command)
        
        # Оптимистичное обновление кэша для мгновенного отклика UI
        if self.data and "settings" in self.data:
            settings = self.data["settings"]
            
            # Number entities
            if command.startswith("TCFV"): settings["float_charging_voltage"] = safe_float(command[4:])
            elif command.startswith("TCCV"): settings["constant_voltage_charging_voltage"] = safe_float(command[4:])
            elif command.startswith("TCQV"): settings["equalization_charging_voltage"] = safe_float(command[4:])
            elif command.startswith("EOD"): settings["battery_discharge_cutoff_voltage"] = safe_float(command[3:])
            elif command.startswith("TBLV"): settings["battery_discharge_alarm_voltage"] = safe_float(command[4:])
            elif command.startswith("BTG"): settings["battery_to_grid_voltage"] = safe_float(command[3:])
            elif command.startswith("BTB"): settings["grid_to_battery_voltage"] = safe_float(command[3:])
            elif command.startswith("BTO"): settings["battery_overvoltage_protection_voltage"] = safe_float(command[3:])
            elif command.startswith("CHGC"): settings["max_charging_current"] = safe_int(command[4:])
            elif command.startswith("GCC"): settings["max_utility_charging_current"] = safe_int(command[3:])
            elif command.startswith("TCVT"): settings["constant_voltage_charging_time"] = safe_int(command[4:])
            elif command.startswith("TCQT"): settings["equalization_charging_time"] = safe_int(command[4:])
            elif command.startswith("TCQO"): settings["equalization_timeout"] = safe_int(command[4:])
            elif command.startswith("TCQI"): settings["equalization_interval"] = safe_int(command[4:])
            elif command.startswith("LWDT"): settings["low_power_discharge_time"] = safe_int(command[4:])
            elif command.startswith("CI1"): settings["constant_current_charging_max_time"] = safe_int(command[3:])
            elif command.startswith("OVP"): settings["grid_overvoltage_protection"] = safe_int(command[3:])
            elif command.startswith("LVP"): settings["grid_undervoltage_protection"] = safe_int(command[3:])
            
            # Select entities
            elif command.startswith("OPM"): settings["output_mode_code"] = command[3:]
            elif command.startswith("OPR"): settings["output_source_priority_code"] = command[3:]
            elif command.startswith("CPR"): settings["charger_source_priority_code"] = command[3:]
            elif command.startswith("TBAT"): settings["battery_type_code"] = command[4:]
            elif command.startswith("V"): settings["output_voltage_code"] = command[1:]
            elif command.startswith("CST"): settings["charging_method_code"] = command[3:]
            elif command.startswith("HV"): settings["ac_input_range_code"] = command[2:]

        await asyncio.sleep(0.1)
        return response

    def build_command(self, cmd_prefix: str, value: str) -> str:
        """Build a write command."""
        return f"{cmd_prefix}{value}"