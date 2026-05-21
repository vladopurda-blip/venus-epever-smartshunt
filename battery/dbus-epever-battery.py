#!/usr/bin/env python3

import sys
import time

sys.path.insert(1, "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python")
sys.path.insert(1, "/opt/victronenergy/dbus-systemcalc-py")

from vedbus import VeDbusService
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from pymodbus.client.sync import ModbusSerialClient

DBusGMainLoop(set_as_default=True)

DEVICE = "/dev/ttyUSB0"
SLAVE_ID = 1
BATTERY_CAPACITY_AH = 400.0
START_SOC = 55.0
UPDATE_MS = 3000
LOW_CURRENT_ZERO = 0.05

client = ModbusSerialClient(
    method="rtu",
    port=DEVICE,
    baudrate=115200,
    timeout=1
)

client.connect()

dbus_service = VeDbusService(
    "com.victronenergy.battery.ttyUSB0",
    register=False
)

dbus_service.add_path("/Mgmt/ProcessName", "Epever Battery RAW")
dbus_service.add_path("/Mgmt/ProcessVersion", "v12 raw-main")
dbus_service.add_path("/Mgmt/Connection", DEVICE)

dbus_service.add_path("/DeviceInstance", 291)
dbus_service.add_path("/ProductId", 0xA389)
dbus_service.add_path("/ProductName", "Epever Battery RAW")
dbus_service.add_path("/FirmwareVersion", "1.0")
dbus_service.add_path("/HardwareVersion", "1.0")
dbus_service.add_path("/Connected", 1)

dbus_service.add_path("/Dc/0/Voltage", 0.0)
dbus_service.add_path("/Dc/0/Current", 0.0)
dbus_service.add_path("/Dc/0/Power", 0.0)

dbus_service.add_path("/Soc", START_SOC)
dbus_service.add_path("/Capacity", BATTERY_CAPACITY_AH)
dbus_service.add_path("/ConsumedAmphours", 0.0)

dbus_service.add_path("/State", 0)
dbus_service.add_path("/TimeToGo", 0)

dbus_service.add_path("/Info/BatteryLowVoltage", 11.8)
dbus_service.add_path("/Info/MaxChargeVoltage", 14.4)

# Diagnostika pre druhý SmartShunt
dbus_service.add_path("/Epever/RawSoc", START_SOC)

dbus_service.register()

last_voltage = 0.0
last_current = 0.0
last_soc = START_SOC


def clamp(value, low, high):
    return max(low, min(high, value))


def read_input(address, count):
    try:
        rr = client.read_input_registers(address, count, unit=SLAVE_ID)
        if rr and not rr.isError():
            return rr.registers
    except Exception:
        pass

    return None


def get_state(current):
    if current > 0.1:
        return 1
    elif current < -0.1:
        return 2
    return 0


def update():
    global last_voltage
    global last_current
    global last_soc

    try:
        regs = read_input(0x331A, 2)

        if regs:
            voltage = regs[0] / 100.0
            current = regs[1] / 100.0

            if abs(current) < LOW_CURRENT_ZERO:
                current = 0.0

            last_voltage = voltage
            last_current = current

        soc_regs = read_input(0x311A, 1)

        if soc_regs:
            soc = float(soc_regs[0])

            if soc > 100:
                soc = soc / 10.0

            last_soc = clamp(soc, 0.0, 100.0)

        power = last_voltage * last_current

        dbus_service["/Dc/0/Voltage"] = round(last_voltage, 2)
        dbus_service["/Dc/0/Current"] = round(last_current, 2)
        dbus_service["/Dc/0/Power"] = round(power, 1)

        dbus_service["/Soc"] = round(last_soc, 1)
        dbus_service["/Epever/RawSoc"] = round(last_soc, 1)

        dbus_service["/State"] = get_state(last_current)

        print(
            f"EPEVER RAW: {round(last_soc,1)}% | "
            f"{round(last_voltage,2)}V | "
            f"{round(last_current,2)}A"
        )

    except Exception as e:
        print("ERROR:", e)

    return True


GLib.timeout_add(UPDATE_MS, update)

print("Epever RAW Battery Monitor hlavny spusteny...")
print("DBUS: com.victronenergy.battery.ttyUSB0")

GLib.MainLoop().run()
