#!/bin/sh

echo "Installing Venus Epever SmartShunt..."

mkdir -p /data/epever

cd /data/epever || exit

wget -O dbus-epever-battery.py \
https://raw.githubusercontent.com/TVOJ_USERNAME/venus-epever-smartshunt/main/battery/dbus-epever-battery.py

wget -O dbus-epever-solarcharger.py \
https://raw.githubusercontent.com/TVOJ_USERNAME/venus-epever-smartshunt/main/solar/dbus-epever-solarcharger.py

wget -O start.sh \
https://raw.githubusercontent.com/TVOJ_USERNAME/venus-epever-smartshunt/main/start.sh

chmod +x start.sh
chmod +x dbus-epever-battery.py
chmod +x dbus-epever-solarcharger.py

pkill -f dbus-epever-battery.py
pkill -f dbus-epever-solarcharger.py

sleep 2

nohup /data/epever/start.sh >/data/epever/log.txt 2>&1 &

echo ""
echo "Installation completed."
echo ""
echo "Solar + Battery services started."
