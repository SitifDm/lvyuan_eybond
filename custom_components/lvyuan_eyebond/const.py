"""Constants for the LVYUAN Inverter (EyeBond G-ASCII) integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "lvyuan_eyebond"
PLATFORMS = ["sensor", "select", "binary_sensor", "number", "switch"]
DEFAULT_NAME = "LVYUAN Inverter"
DEFAULT_SCAN_INTERVAL = 5  # Изменено с 10 на 5 для быстрого цикла
DEFAULT_TIMEOUT = 3

# --- Конфигурация ---
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_SERIAL_DEVICE = "serial_device"
CONF_BAUDRATE = "baudrate"

DEFAULT_SERIAL_DEVICE = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 9600
BAUDRATE_OPTIONS = [9600]

# --- Сервисы ---
ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_COMMAND = "command"
ATTR_REFRESH = "refresh"
ATTR_EXPECT_RESPONSE = "expect_response"

SERVICE_SEND_COMMAND = "send_command"
SERVICE_REFRESH = "refresh"

# --- Режимы работы (GMOD) ---
EYEBOND_MODE_CODES = {
    "P": "power_on",
    "S": "standby",
    "L": "line",
    "B": "battery",
    "F": "fault",
}

# --- Тип батареи (TBAT) ---
EYEBOND_BATTERY_TYPE_MAP = {
    "Lead-acid": "0",
    "Flooded": "1",
    "Lithium": "2",
    "Custom": "3",
}
EYEBOND_BATTERY_TYPE_REVERSE = {v: k for k, v in EYEBOND_BATTERY_TYPE_MAP.items()}

# --- Приоритет выхода (OPR) ---
EYEBOND_OUTPUT_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "PV > Battery > Utility": "02",
}
EYEBOND_OUTPUT_PRIORITY_REVERSE = {v: k for k, v in EYEBOND_OUTPUT_PRIORITY_MAP.items()}

# --- Режим выхода (OPM) ---
EYEBOND_OUTPUT_MODE_MAP = {
    "Appliance mode": "00",
    "UPS mode": "01",
}
EYEBOND_OUTPUT_MODE_REVERSE = {v: k for k, v in EYEBOND_OUTPUT_MODE_MAP.items()}

# --- Приоритет зарядки (CPR) ---
EYEBOND_CHARGER_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "Utility + PV": "02",
    "PV only": "03",
}
EYEBOND_CHARGER_PRIORITY_REVERSE = {v: k for k, v in EYEBOND_CHARGER_PRIORITY_MAP.items()}

# --- Метод зарядки (CST) ---
EYEBOND_CHARGING_METHOD_MAP = {
    "Auto": "00",
    "Forced 2-stage": "01",
    "Forced 3-stage": "02",
}
EYEBOND_CHARGING_METHOD_REVERSE = {v: k for k, v in EYEBOND_CHARGING_METHOD_MAP.items()}

# --- Напряжение выхода (V) ---
EYEBOND_OUTPUT_VOLTAGE_MAP = {
    "208 V": "208",
    "220 V": "220",
    "230 V": "230",
    "240 V": "240",
}
EYEBOND_OUTPUT_VOLTAGE_REVERSE = {v: k for k, v in EYEBOND_OUTPUT_VOLTAGE_MAP.items()}

# --- Диапазон входа AC (HV) ---
EYEBOND_AC_INPUT_RANGE_MAP = {
    "APL (Wide 90-280V)": "0",
    "UPS (Narrow 170-280V)": "1",
}
EYEBOND_AC_INPUT_RANGE_REVERSE = {v: k for k, v in EYEBOND_AC_INPUT_RANGE_MAP.items()}

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
