#!/usr/bin/env python3

import sys
import subprocess

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

sys.path.insert(1, '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python')

from vedbus import VeDbusService

DBusGMainLoop(set_as_default=True)

# =====================
# CONFIG
# =====================

SOURCE_SERVICE = 'com.victronenergy.battery.ttyUSB0'
RAW_SERVICE = 'com.victronenergy.battery.epever_raw'

DEVICE_INSTANCE = 291
BATTERY_CAPACITY_AH = 400.0

# =====================
# DBUS SERVICE
# =====================

raw_service = VeDbusService(
    RAW_SERVICE,
    register=False
)

raw_service.add_path('/Mgmt/ProcessName', 'Epever RAW Battery Monitor')
raw_service.add_path('/Mgmt/ProcessVersion', 'v3 DBUS CLI mirror')
raw_service.add_path('/Mgmt/Connection', 'Mirror from main Epever battery')

raw_service.add_path('/DeviceInstance', DEVICE_INSTANCE)
raw_service.add_path('/ProductId', 0xA389)
raw_service.add_path('/ProductName', 'Epever RAW Battery SOC')
raw_service.add_path('/FirmwareVersion', '1.0')
raw_service.add_path('/HardwareVersion', '1.0')
raw_service.add_path('/Connected', 1)

raw_service.add_path('/Dc/0/Voltage', 0.0)
raw_service.add_path('/Dc/0/Current', 0.0)
raw_service.add_path('/Dc/0/Power', 0.0)

raw_service.add_path('/Soc', 0.0)
raw_service.add_path('/Capacity', BATTERY_CAPACITY_AH)
raw_service.add_path('/ConsumedAmphours', 0.0)

raw_service.add_path('/State', 0)
raw_service.add_path('/TimeToGo', 0)

raw_service.add_path('/Info/BatteryLowVoltage', 11.8)
raw_service.add_path('/Info/MaxChargeVoltage', 14.4)

raw_service.register()

# =====================
# HELPERS
# =====================

def read_dbus_value(path, default=0.0):
    try:
        out = subprocess.check_output(
            ['dbus', '-y', SOURCE_SERVICE, path, 'GetValue'],
            stderr=subprocess.DEVNULL
        )

        value = out.decode().strip()

        if value == '':
            return default

        return float(value)

    except Exception:
        return default


def get_state(current):
    if current > 0.1:
        return 1
    elif current < -0.1:
        return 2
    return 0


# =====================
# UPDATE
# =====================

def update():
    try:
        voltage = read_dbus_value('/Dc/0/Voltage', 0.0)
        current = read_dbus_value('/Dc/0/Current', 0.0)
        power = read_dbus_value('/Dc/0/Power', voltage * current)

        # RAW SOC ak hlavný battery script poskytuje /Epever/RawSoc
        raw_soc = read_dbus_value('/Epever/RawSoc', None)

        # fallback: ak /Epever/RawSoc neexistuje, zobrazí hlavný SOC
        if raw_soc is None:
            raw_soc = read_dbus_value('/Soc', 0.0)

        raw_service['/Dc/0/Voltage'] = round(voltage, 2)
        raw_service['/Dc/0/Current'] = round(current, 2)
        raw_service['/Dc/0/Power'] = round(power, 1)

        raw_service['/Soc'] = round(raw_soc, 1)
        raw_service['/State'] = get_state(current)

        print(
            f"RAW BATTERY: {round(raw_soc,1)}% | "
            f"{round(voltage,2)}V | "
            f"{round(current,2)}A"
        )

    except Exception as e:
        print("RAW ERROR:", e)

    return True


# =====================
# START
# =====================

GLib.timeout_add(5000, update)

print("Epever RAW Battery Monitor v3 spusteny...")
print("Service:", RAW_SERVICE)
print("DeviceInstance:", DEVICE_INSTANCE)

GLib.MainLoop().run()
