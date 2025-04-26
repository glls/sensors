import os
import time

import bme280
import smbus2
from dotenv import load_dotenv

from services import send_temp_data_to_api, send_temp_data_to_timescaledb

# Load environment variables from .env file
load_dotenv()

SEND_TO_TIMESCALEDB = os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true'
SEND_TO_API = os.environ.get('SEND_TO_API', 'False').lower() == 'true'
# unique sensor ID
BME280_SENSOR_ID = os.environ.get('BME280_SENSOR_ID')
# BME280 sensor address (default address)
BME280_ADDRESS = 0x76
# delay time for sensor readings (in seconds)
BME280_INTERVAL = 55

if BME280_SENSOR_ID is None:
    print("Error: BME280_SENSOR_ID not set in environment variables.")
    exit(1)

if SEND_TO_TIMESCALEDB is False and SEND_TO_API is False:
    print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
    exit(2)

if SEND_TO_TIMESCALEDB is True and SEND_TO_API is True:
    print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
    exit(3)

# Initialize I2C bus
try:
    bus = smbus2.SMBus(1)
    # Load calibration parameters ONCE
    calibration_params = bme280.load_calibration_params(bus, BME280_ADDRESS)
except FileNotFoundError:
    bus = None
    calibration_params = None
    print("Error: I2C bus not found. Sensor readings will be simulated.")
except Exception as e:
    bus = None
    calibration_params = None
    print(f"Error initializing I2C bus: {e}. Sensor readings will be simulated.")

while True:
    try:
        if bus and calibration_params:
            # Read sensor data
            data = bme280.sample(bus, BME280_ADDRESS, calibration_params)
            temperature = data.temperature
            pressure = data.pressure
            humidity = data.humidity

            # Print the readings
            print(f"Temperature: {temperature:.2f} °C\t"
                  f"Humidity: {humidity:.2f} %\t"
                  f"Pressure: {pressure:.2f} hPa")

            # Send data based on configuration
            if SEND_TO_TIMESCALEDB:
                send_temp_data_to_timescaledb(BME280_SENSOR_ID, temperature, humidity, pressure)
            elif SEND_TO_API:
                send_temp_data_to_api(BME280_SENSOR_ID, temperature, humidity, pressure)

        time.sleep(BME280_INTERVAL)

    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break
