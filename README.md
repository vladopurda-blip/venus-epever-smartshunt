# Venus Epever SmartShunt

DIY Victron-style battery monitor + solar integration for Venus OS using Epever charge controllers.

## Features

- Venus OS integration
- VRM Portal support
- Epever solar charger support
- Virtual battery monitor
- Stable DBus services
- Auto restart after reboot
- Victron-style UI
- No physical SmartShunt required

## Supported

- Venus OS
- Raspberry Pi GX
- Epever Tracer series
- USB RS485 adapters

## Services

- com.victronenergy.solarcharger.ttyUSB0
- com.victronenergy.battery.ttyUSB0

## Install

```bash
wget -O - https://raw.githubusercontent.com/TVOJ_USERNAME/venus-epever-smartshunt/main/install.sh | sh


Notes

This project creates a virtual Victron battery monitor using Epever battery data.

SOC values are estimated from:

controller battery SOC
voltage
charge/discharge current
smoothing filters
