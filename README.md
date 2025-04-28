# sensors

## Architecture

The architecture of the system consists of these main components:

1. Clients
    1. **BME280 Sensor**: This component is responsible for reading data from the BME280 sensor and sending it to a
       server. It runs on a Raspberry Pi or similar device.
    2. **AM2302 Sensor**: This component is responsible for reading data from the AM2302 sensor and sending it to a
       server. It runs on a Raspberry Pi or similar device.
    3. **ENS160 Sensor**: This component is responsible for reading data from the ENS160 sensor and sending it to a
       server. It runs on a Raspberry Pi or similar device.
    4. **AIRROHR**: This component is responsible for reading data from the AIRROHR device and sending it to a server.
2. **Server**: This component receives the data from the sensor clients and stores it in a database. It can be a local
   server or a cloud-based server.
3. **Database**: The database stores the sensor data for later retrieval and analysis. It can be a local database or a
   cloud-based database.
4. **Web Interface**: The web interface allows users to view the sensor data in real-time. It can be a local web
   application or a cloud-based web application.
5. **Mobile Application**: The mobile application allows users to view the sensor data on their mobile devices. It can
   be a native mobile application or a web-based mobile application.
6. **Notification System**: The notification system sends alerts to users when certain conditions are met, such as high
   temperature or humidity levels. It can be a local notification system or a cloud-based notification system.
7. **Data Visualization**: The data visualization component allows users to visualize the sensor data in various
   formats, such as graphs and charts. It can be a local data visualization tool or a cloud-based data visualization
   tool.

## Clients

The clients are responsible for reading data from the sensors and sending it to the server.
[Readme](clients/README.md) for more information.

## Servers

There are two servers, the REST API and the database server.

### API

Django REST API server that receives data from the sensor clients and stores it in a database.

### TimescaleDB

TimescaleDB is a time-series database built on PostgreSQL. It is used to store the sensor data for later retrieval and
analysis. It can be a local database or a cloud-based database.
Runs with docker on UNRAID server.
