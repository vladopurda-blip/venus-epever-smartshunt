#!/usr/bin/env python3

import sys
import time
import os
import subprocess

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

sys.path.insert(1, "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python")

from vedbus import VeDbusService

DBusGMainLoop(set_as_default=True)

SOURCE_SERVICE = "com.victronenergy.battery.ttyUSB0"
CALC_SERVICE = "com.victronenergy.battery.epever_calc"

DEVICE_INSTANCE = 0
BATTERY_CAPACITY_AH = 400.0

SOC_SAVE_FILE = "/data/epever/calculated_soc.txt"

START_SOC = 55.0
UPDATE_MS = 3000
UPDATE_SECONDS = UPDATE_MS / 1000.0

FULL_VOLTAGE = 14.35
FULL_CURRENT = 1.0
FULL_CONFIRM_CYCLES = 60

LOW_CURRENT_ZERO = 0.05

# maximálna zmena SOC za update, aby to nelietalo
MAX_STEP_PER_UPDATE = 0.05

# napäťová korekcia len keď to dáva zmysel
VOLTAGE_ALPHA_IDLE = 0.015
VOLTAGE_ALPHA_CHARGE = 0.003

full_counter = 0
last_save = 0


def clamp(value, low, high):
    return max(low, min(high, value))


def load_soc():
    try:
        if os.path.exists(SOC_SAVE_FILE):
            with open(SOC_SAVE_FILE, "r") as f:
                return clamp(float(f.read().strip()), 0.0, 100.0)
    except Exception:
        pass

    return START_SOC


def save_soc(value):
    try:
        with open(SOC_SAVE_FILE, "w") as f:
            f.write(str(round(value, 2)))
    except Exception:
        pass


def dbus_value(path, default=0.0):
    try:
        out = subprocess.check_output(
            ["dbus", "-y", SOURCE_SERVICE, path, "GetValue"],
            stderr=subprocess.DEVNULL
        )
        txt = out.decode().strip()
        if txt == "":
            return default
        return float(txt)
    except Exception:
        return default


def voltage_to_soc(v, current):
    # Toto nie je "pravda", ale rozumná 12V olovo/AGM/GEL orientačná krivka.
    # Pri nabíjaní sa napätie umelo zdvihne, preto ho upravíme.
    if current > 1.0:
        v = v - min(0.45, current * 0.04)

    if v >= 12.80:
        return 90.0
    if v >= 12.70:
        return 80.0
    if v >= 12.60:
        return 70.0
    if v >= 12.50:
        return 60.0
    if v >= 12.40:
        return 50.0
    if v >= 12.30:
        return 40.0
    if v >= 12.20:
        return 30.0
    if v >= 12.10:
        return 20.0
    if v >= 11.95:
        return 10.0

    return 5.0


def limit_step(old, new):
    diff = new - old

    if diff > MAX_STEP_PER_UPDATE:
        return old + MAX_STEP_PER_UPDATE

    if diff < -MAX_STEP_PER_UPDATE:
        return old - MAX_STEP_PER_UPDATE

    return new


def get_state(current):
    if current > 0.1:
        return 1
    elif current < -0.1:
        return 2
    return 0


def time_to_go(soc, current):
    current_abs = abs(current)

    if current_abs < 0.05:
        return 0

    remaining_ah = (soc / 100.0) * BATTERY_CAPACITY_AH
    hours = remaining_ah / current_abs

    return int(hours * 3600)


calc_soc = load_soc()

calc_service = VeDbusService(
    CALC_SERVICE,
    register=False
)

calc_service.add_path("/Mgmt/ProcessName", "Epever Calculated SmartShunt")
calc_service.add_path("/Mgmt/ProcessVersion", "v1 calculated")
calc_service.add_path("/Mgmt/Connection", "Mirror + calculated from Epever RAW")

calc_service.add_path("/DeviceInstance", DEVICE_INSTANCE)
calc_service.add_path("/ProductId", 0xA389)
calc_service.add_path("/ProductName", "Epever Calculated SmartShunt")
calc_service.add_path("/FirmwareVersion", "1.0")
calc_service.add_path("/HardwareVersion", "1.0")
calc_service.add_path("/Connected", 1)

calc_service.add_path("/Dc/0/Voltage", 0.0)
calc_service.add_path("/Dc/0/Current", 0.0)
calc_service.add_path("/Dc/0/Power", 0.0)

calc_service.add_path("/Soc", calc_soc)
calc_service.add_path("/Capacity", BATTERY_CAPACITY_AH)
calc_service.add_path("/ConsumedAmphours", 0.0)

calc_service.add_path("/State", 0)
calc_service.add_path("/TimeToGo", 0)

calc_service.add_path("/Info/BatteryLowVoltage", 11.8)
calc_service.add_path("/Info/MaxChargeVoltage", 14.4)

# diagnostika
calc_service.add_path("/Epever/RawSoc", 0.0)
calc_service.add_path("/Epever/VoltageSoc", 0.0)
calc_service.add_path("/Epever/FullCounter", 0)

calc_service.register()


def update():
    global calc_soc
    global full_counter
    global last_save

    try:
        voltage = dbus_value("/Dc/0/Voltage", 0.0)
        current = dbus_value("/Dc/0/Current", 0.0)
        power = dbus_value("/Dc/0/Power", voltage * current)
        raw_soc = dbus_value("/Epever/RawSoc", 0.0)

        if abs(current) < LOW_CURRENT_ZERO:
            current = 0.0

        voltage_soc = voltage_to_soc(voltage, current)

        # Full sync iba keď prúd naozaj klesne nízko.
        # 14.4V + 8A nie je full, to je stále silné nabíjanie.
        if voltage >= FULL_VOLTAGE and 0 <= current <= FULL_CURRENT:
            full_counter += 1
        else:
            full_counter = 0

        target = calc_soc

        if full_counter >= FULL_CONFIRM_CYCLES:
            target = 100.0

        else:
            # Coulomb-like počítanie z prúdu.
            # Epever current je u teba kladný pri nabíjaní.
            delta_ah = current * (UPDATE_SECONDS / 3600.0)
            delta_soc = (delta_ah / BATTERY_CAPACITY_AH) * 100.0
            target = calc_soc + delta_soc

            # Napäťová korekcia:
            # pri malom prúde viac veríme napätiu,
            # pri nabíjaní len veľmi slabo, aby slnko neskákalo na 100%.
            if current == 0.0:
                target += (voltage_soc - target) * VOLTAGE_ALPHA_IDLE
            elif current > 0.0:
                target += (voltage_soc - target) * VOLTAGE_ALPHA_CHARGE

            # Bezpečnostná korekcia pri nízkom napätí
            if voltage < 12.10 and target > 25:
                target -= 0.03

            if voltage < 11.95 and target > 15:
                target -= 0.08

        target = clamp(target, 0.0, 100.0)
        calc_soc = limit_step(calc_soc, target)
        calc_soc = clamp(calc_soc, 0.0, 100.0)

        calc_service["/Dc/0/Voltage"] = round(voltage, 2)
        calc_service["/Dc/0/Current"] = round(current, 2)
        calc_service["/Dc/0/Power"] = round(power, 1)

        calc_service["/Soc"] = round(calc_soc, 1)
        calc_service["/State"] = get_state(current)
        calc_service["/TimeToGo"] = time_to_go(calc_soc, current)

        calc_service["/Epever/RawSoc"] = round(raw_soc, 1)
        calc_service["/Epever/VoltageSoc"] = round(voltage_soc, 1)
        calc_service["/Epever/FullCounter"] = full_counter

        if time.time() - last_save > 60:
            save_soc(calc_soc)
            last_save = time.time()

        print(
            f"CALC: {round(calc_soc,1)}% | "
            f"RAW: {round(raw_soc,1)}% | "
            f"V-SOC: {round(voltage_soc,1)}% | "
            f"{round(voltage,2)}V | {round(current,2)}A | "
            f"FULLCNT:{full_counter}"
        )

    except Exception as e:
        print("CALC ERROR:", e)

    return True


GLib.timeout_add(UPDATE_MS, update)

print("Epever Calculated SmartShunt spusteny...")
print("DBUS:", CALC_SERVICE)

GLib.MainLoop().run()
