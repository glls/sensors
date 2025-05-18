# Sensors

## Sensor Data Collection System

This repository contains a system for collecting and storing sensor data from various environmental sensors. The system
is designed to be modular, allowing for easy integration of new sensors and data sources.

## Architecture

The architecture of the system consists of these main components:

1. Clients
    1. **BME280 Sensor**: Reads temperature, humidity, and pressure data.
    2. **AM2302 Sensor**: Reads temperature and humidity data.
    3. **ENS160 Sensor**: Reads indoor air quality data (AQI, TVOC, eCO2).
    4. **AIRROHR**: Reads particulate matter (PM10, PM2.5) data.
2. Servers
    1. **API**: A Django REST API that receives data from the sensor clients and stores it in a database.
    2. **TimescaleDB**: A time-series database built on PostgreSQL for storing sensor data.
3. Web Interface: Allows users to view sensor data in real-time.

## Clients

The clients read data from the sensors and send it to the server.
[Readme](clients/README.md) for more information.

## Servers

### API

Django REST API (based on DRF) that receives data from the sensor clients and stores it in a database.

### TimescaleDB

TimescaleDB is a time-series database built on PostgreSQL for storing sensor data.
Runs with docker on UNRAID server.

## Web Interface
The web interface allows users to view sensor data in real-time.


```sh
uvicorn sensors.asgi:application --host 0.0.0.0 --port 8000 --reload --lifespan=off
```

## TODO

- [ ] add user events
