"""Constants for the LVYUAN Inverter (EyeBond G-ASCII) integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "lvyuan_eybond"
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
EYBOND_MODE_CODES = {
    "P": "power_on",
    "S": "standby",
    "L": "line",
    "B": "battery",
    "F": "fault",
}

# --- Тип батареи (TBAT) ---
EYBOND_BATTERY_TYPE_MAP = {
    "Lead-acid": "0",
    "Flooded": "1",
    "Lithium": "2",
    "Custom": "3",
}
EYBOND_BATTERY_TYPE_REVERSE = {v: k for k, v in EYBOND_BATTERY_TYPE_MAP.items()}

# --- Приоритет выхода (OPR) ---
EYBOND_OUTPUT_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "PV > Battery > Utility": "02",
}
EYBOND_OUTPUT_PRIORITY_REVERSE = {v: k for k, v in EYBOND_OUTPUT_PRIORITY_MAP.items()}

# --- Режим выхода (OPM) ---
EYBOND_OUTPUT_MODE_MAP = {
    "Appliance mode": "00",
    "UPS mode": "01",
}
EYBOND_OUTPUT_MODE_REVERSE = {v: k for k, v in EYBOND_OUTPUT_MODE_MAP.items()}

# --- Приоритет зарядки (CPR) ---
EYBOND_CHARGER_PRIORITY_MAP = {
    "Utility first": "00",
    "PV first": "01",
    "Utility + PV": "02",
    "PV only": "03",
}
EYBOND_CHARGER_PRIORITY_REVERSE = {v: k for k, v in EYBOND_CHARGER_PRIORITY_MAP.items()}

# --- Метод зарядки (CST) ---
EYBOND_CHARGING_METHOD_MAP = {
    "Auto": "00",
    "Forced 2-stage": "01",
    "Forced 3-stage": "02",
}
EYBOND_CHARGING_METHOD_REVERSE = {v: k for k, v in EYBOND_CHARGING_METHOD_MAP.items()}

# --- Напряжение выхода (V) ---
EYBOND_OUTPUT_VOLTAGE_MAP = {
    "208 V": "208",
    "220 V": "220",
    "230 V": "230",
    "240 V": "240",
}
EYBOND_OUTPUT_VOLTAGE_REVERSE = {v: k for k, v in EYBOND_OUTPUT_VOLTAGE_MAP.items()}

# --- Диапазон входа AC (HV) ---
EYBOND_AC_INPUT_RANGE_MAP = {
    "APL (Wide 90-280V)": "0",
    "UPS (Narrow 170-280V)": "1",
}
EYBOND_AC_INPUT_RANGE_REVERSE = {v: k for k, v in EYBOND_AC_INPUT_RANGE_MAP.items()}

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)