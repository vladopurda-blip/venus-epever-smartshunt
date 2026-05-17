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

# -------------------------
# MODBUS
# -------------------------

client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    baudrate=115200,
    timeout=1
)

client.connect()

# -------------------------
# DBUS
# -------------------------

service = VeDbusService("com.victronenergy.battery.ttyUSB0")

service.add_path('/Mgmt/ProcessName', __file__)
service.add_path('/Mgmt/ProcessVersion', '1.0')
service.add_path('/Mgmt/Connection', 'Epever Battery')

service.add_path('/DeviceInstance', 0)
service.add_path('/ProductId', 0)
service.add_path('/ProductName', 'Epever Smart Battery')
service.add_path('/FirmwareVersion', '1.0')
service.add_path('/HardwareVersion', '1.0')
service.add_path('/Connected', 1)

service.add_path('/Dc/0/Voltage', 12.0)
service.add_path('/Dc/0/Current', 0.0)
service.add_path('/Dc/0/Power', 0.0)

service.add_path('/Soc', 55.0)

service.add_path('/Capacity', 400.0)
service.add_path('/ConsumedAmphours', 0)

service.add_path('/Info/BatteryLowVoltage', 11.8)
service.add_path('/Info/MaxChargeVoltage', 14.4)

print("Epever REAL BATTERY FINAL spusteny...")

# -------------------------
# UPDATE
# -------------------------

def update():

    try:

        # battery voltage/current
        rr = client.read_input_registers(0x331A, 2, unit=1)

        if not rr.isError():

            voltage = rr.registers[0] / 100.0
            current = rr.registers[1] / 100.0

            # battery SOC
            soc_rr = client.read_input_registers(0x311A, 1, unit=1)

            if not soc_rr.isError():
                soc = float(soc_rr.registers[0])

                # sanity clamp
                soc = max(0, min(100, soc))

            else:
                soc = service['/Soc']

            power = voltage * current

            service['/Dc/0/Voltage'] = round(voltage, 2)
            service['/Dc/0/Current'] = round(current, 2)
            service['/Dc/0/Power'] = round(power, 1)

            service['/Soc'] = round(soc, 1)

            print(
                f"SOC: {soc:.1f}% | "
                f"{voltage:.2f}V | "
                f"{current:.2f}A"
            )

    except Exception as e:
        print("ERROR:", e)

    return True


# pomalšie čítanie = stabilita
GLib.timeout_add(3000, update)

mainloop = GLib.MainLoop()
mainloop.run()
