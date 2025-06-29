# Sensors

## AM2302/DHT22 installation

https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup

pip3 install adafruit-circuitpython-dht

## BME280 installation

https://randomnerdtutorials.com/raspberry-pi-bme280-python/

pip3 install RPI.BME280

## ENS160 installation

[Datasheet](https://dfimg.dfrobot.com/nobody/wiki/cbe10f01b67c3fee6d365039eb54f52c.pdf)\
https://wiki.dfrobot.com/SKU_SEN0514_Gravity_ENS160_Air_Quality_Sensor \
https://learn.adafruit.com/adafruit-ens160-mox-gas-sensor/circuitpython-python

pip3 install adafruit-circuitpython-ens160

### Service for the Client

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
# Replace with the user you want to run the script as
User=your_user
# Replace with the actual path
WorkingDirectory=/path/to/your/script/directory
# Replace with the full path to your script
ExecStart=/usr/bin/python3 /path/to/your/script/directory/bme280_client.py
Restart=on-failure
StandardOutput=journal
StandardError=journal
Environment="SEND_TO_TIMESCALEDB=True"
Environment="PYTHONUNBUFFERED=1"

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

## TODO

* [ ] store timestamp from sensor data (actual reading time)
* [ ] hold sensor data if database/api server is down and send when reconnected
