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

Custom Venus OS DBus integration for Epever MPPT controllers on Victron Venus OS.

This project exposes Epever data inside Victron Venus OS / VRM as:

- Solar Charger
- Calculated SmartShunt battery monitor
- RAW Epever battery SOC monitor

## Features

- Epever MPPT solar charger integration
- Battery voltage/current/SOC integration
- Calculated SmartShunt mode
- RAW Epever SOC monitor
- Venus OS dashboard support
- VRM Portal support
- Auto start script
- Works together with Victron inverter on ttyUSB1

## Tested hardware

- Raspberry Pi running Venus OS
- Epever Tracer series MPPT controller
- USB RS485 adapter
- Victron inverter on ttyUSB1

## Services

- `com.victronenergy.solarcharger.ttyUSB0`
- `com.victronenergy.battery.ttyUSB0`

## Current setup

- Solar charger: `DeviceInstance 290`
- Main calculated battery monitor: `DeviceInstance 0`
- RAW Epever battery monitor: `DeviceInstance 291`
- Victron inverter remains on `ttyUSB1`

## Install

Run on Venus OS:

```sh
wget -O - https://raw.githubusercontent.com/vladopurda-blip/venus-epever-smartshunt/main/install.sh | sh

controller battery SOC
voltage
charge/discharge current
smoothing filters
