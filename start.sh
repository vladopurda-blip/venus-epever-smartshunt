#!/bin/sh

LOG="/data/epever/log.txt"

echo "Epever watchdog started..." >> "$LOG"

while true
do
    if ! dbus -y | grep -q "com.victronenergy.solarcharger.ttyUSB0"; then
        echo "Starting Epever Solar..." >> "$LOG"

        PYTHONPATH=/opt/victronenergy/dbus-systemcalc-py/ext/velib_python \
        python3 /data/epever/dbus-epever-solarcharger.py >> "$LOG" 2>&1 &
    fi

    sleep 5

    if ! dbus -y | grep -q "com.victronenergy.battery.ttyUSB0"; then
        echo "Starting Epever Battery RAW..." >> "$LOG"

        PYTHONPATH=/opt/victronenergy/dbus-systemcalc-py/ext/velib_python \
        python3 /data/epever/dbus-epever-battery.py >> "$LOG" 2>&1 &
    fi

    sleep 5

    if ! dbus -y | grep -q "com.victronenergy.battery.epever_calc"; then
        echo "Starting Epever Calculated SmartShunt..." >> "$LOG"

        PYTHONPATH=/opt/victronenergy/dbus-systemcalc-py/ext/velib_python \
        python3 /data/epever/dbus-epever-battery-calc.py >> "$LOG" 2>&1 &
    fi

    sleep 30
done
