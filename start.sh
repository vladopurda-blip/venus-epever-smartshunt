#!/bin/sh

while true
do
    if ! dbus -y | grep -q "com.victronenergy.solarcharger.ttyUSB0"; then
        echo "Starting Epever Solar..."
        nohup python3 /data/epever/dbus-epever-solarcharger.py >> /data/epever/log.txt 2>&1 &
    fi

    if ! dbus -y | grep -q "com.victronenergy.battery.ttyUSB0"; then
        echo "Starting Epever Battery..."
        nohup python3 /data/epever/dbus-epever-battery.py >> /data/epever/log.txt 2>&1 &
    fi

    sleep 30
done
