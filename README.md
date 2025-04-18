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

check tested and ready to use

- [ ] validate measurements
- [ ] send data to API
- [X] send data to TimescaleDB

### BME280 Sensor Client

#### Systemd Service Setup for BME280 Client, AM2302 Client, ENS160 Client, and AIRROHR Client

To run the `bme280_client.py` script as a systemd service for reliable background operation and automatic startup on
boot, follow these steps:

1. **Create the service file:** Create a new file named `bme280_client.service` in the systemd service directory,
   typically located at `/etc/systemd/system/`. You will need root privileges for this:
   ```bash
   sudo nano /etc/systemd/system/bme280_client.service
   ```

2. **Paste the service definition:** Copy and paste the following content into the `bme280_client.service` file. **Make
   sure to replace the placeholder values** with your actual setup:

   ```ini
   [Unit]
   Description=BME280 Sensor Data Client
   After=network.target

   [Service]
   User=your_user  # Replace with the user you want to run the script as
   WorkingDirectory=/path/to/your/script/directory  # Replace with the actual path
   ExecStart=/usr/bin/python3 /path/to/your/script/directory/bme280_client.py  # Replace with the full path to your script
   Restart=on-failure
   StandardOutput=journal
   StandardError=journal
   Environment="SEND_TO_TIMESCALEDB=True"

   [Install]
   WantedBy=multi-user.target
   ```

3. **Edit the service file:**
    * **`User`**: Replace `your_user` with the non-root username you want to run the script under.
    * **`WorkingDirectory`**: Replace `/path/to/your/script/directory` with the absolute path to the directory
      containing `bme280_client.py`.
    * **`ExecStart`**: Ensure `/usr/bin/python3` is the correct path to your Python 3 interpreter and update the script
      path accordingly.

4. **Save and close the file.**

5. **Reload systemd configuration:** Apply the changes by reloading the systemd manager configuration:
   ```bash
   sudo systemctl daemon-reload
   ```

6. **Enable the service to start on boot:**
   ```bash
   sudo systemctl enable bme280_client.service
   ```

7. **Start the service immediately:**
   ```bash
   sudo systemctl start bme280_client.service
   ```

8. **Check the service status:** Verify that the service is running correctly:
   ```bash
   sudo systemctl status bme280_client.service
   ```

9. **View logs:** To see the output and any errors from the service, use:
   ```bash
   sudo journalctl -u bme280_client.service -f
   ```

## Server

There are two servers, the API and the database.

### API

Django REST API server that receives data from the sensor clients and stores it in a database.

### TimescaleDB

TimescaleDB is a time-series database built on PostgreSQL. It is used to store the sensor data for later retrieval and
analysis. It can be a local database or a cloud-based database.
Runs with docker on UNRAID server.
