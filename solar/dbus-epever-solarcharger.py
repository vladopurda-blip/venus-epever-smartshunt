import sys
import time
import threading

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

sys.path.insert(1, '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python')
sys.path.insert(1, '/data/epever')

from vedbus import VeDbusService
from epever_tracer import EpeverTracer

DBusGMainLoop(set_as_default=True)

# =========================
# DBUS
# =========================

dbus_service = VeDbusService(
    'com.victronenergy.solarcharger.ttyUSB0',
    register=False
)

dbus_service.add_path('/Mgmt/ProcessName', 'Epever Solar Charger')
dbus_service.add_path('/Mgmt/ProcessVersion', '1.0')
dbus_service.add_path('/Mgmt/Connection', '/dev/ttyUSB0')

dbus_service.add_path('/DeviceInstance', 290)
dbus_service.add_path('/ProductId', 0xA042)
dbus_service.add_path('/ProductName', 'Epever MPPT')
dbus_service.add_path('/Connected', 1)

dbus_service.add_path('/State', 3)

dbus_service.add_path('/Pv/V', 0.0)
dbus_service.add_path('/Pv/I', 0.0)
dbus_service.add_path('/Pv/P', 0.0)

dbus_service.add_path('/Dc/0/Voltage', 0.0)
dbus_service.add_path('/Dc/0/Current', 0.0)

dbus_service.add_path('/Yield/Power', 0.0)

dbus_service.register()

# =========================
# TRACER
# =========================

tracer = EpeverTracer('/dev/ttyUSB0', 1)

pv_v = 0.0
pv_i = 0.0
pv_p = 0.0

bat_v = 0.0
bat_i = 0.0

# =========================
# READER
# =========================

def reader():

    global tracer
    global pv_v
    global pv_i
    global pv_p
    global bat_v
    global bat_i

    while True:

        try:
            d = tracer.read()

            if d:

                pv_v = round(float(d.get('pv_v', 0)), 2)
                pv_i = round(float(d.get('pv_a', 0)), 2)

                pv_p = round(pv_v * pv_i, 1)

                bat_v = round(float(d.get('bat_v', 0)), 2)
                bat_i = round(float(d.get('bat_a', 0)), 2)

        except Exception as e:
            print("READ ERROR:", e)

            try:
                tracer = EpeverTracer('/dev/ttyUSB0', 1)
            except:
                pass

        time.sleep(2)

# =========================
# DBUS UPDATER
# =========================

def updater():

    while True:

        try:

            dbus_service['/Pv/V'] = pv_v
            dbus_service['/Pv/I'] = pv_i
            dbus_service['/Pv/P'] = pv_p

            dbus_service['/Dc/0/Voltage'] = bat_v
            dbus_service['/Dc/0/Current'] = bat_i

            dbus_service['/Yield/Power'] = pv_p

            print(
                f"PV: {pv_v}V | {pv_i}A | {pv_p}W "
                f"|| BAT: {bat_v}V | {bat_i}A"
            )

        except Exception as e:
            print("DBUS ERROR:", e)

        time.sleep(2)

# =========================
# START
# =========================

threading.Thread(target=reader, daemon=True).start()
threading.Thread(target=updater, daemon=True).start()

print("Epever SOLAR ORIGINAL spusteny...")

GLib.MainLoop().run()
