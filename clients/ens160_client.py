import os
import time

import adafruit_ens160
import board
from dotenv import load_dotenv

from services import get_temp_data_last, send_indoor_data_to_timescaledb, send_indoor_data_to_api

# Load environment variables from .env file
load_dotenv()

SEND_TO_TIMESCALEDB = os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true'

SEND_TO_API = os.environ.get('SEND_TO_API', 'False').lower() == 'true'
# unique sensor ID
ENS160_SENSOR_ID = os.environ.get('ENS160_SENSOR_ID')
BME280_SENSOR_ID = os.environ.get('BME280_SENSOR_ID')

# delay time for sensor readings (in seconds)
ENS160_INTERVAL = 55

if ENS160_SENSOR_ID is None:
    print("Error: ENS160_SENSOR_ID not set in environment variables.")
    exit(1)

# Initialize I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA
ens = adafruit_ens160.ENS160(i2c)
# Get the last sensor data from BME280_SENSOR_ID in TimescaleDB
last_data = get_temp_data_last(BME280_SENSOR_ID)
if last_data:
    print(f"Last sensor data from TimescaleDB: {last_data['temperature']:.4f} °C\t {last_data['humidity']:.4f} %")
    ens.temperature_compensation = last_data['temperature']
    ens.humidity_compensation = last_data['humidity']
else:
    ens.temperature_compensation = 25.0  # Set temperature compensation to 25 degrees Celsius
    ens.humidity_compensation = 50.0  # Set humidity compensation to 50% relative humidity

while True:
    try:
        aqi = ens.aqi
        tvoc = ens.tvoc
        e_co2 = ens.e_co2
        print(f"AQI (1-5): {aqi}\t"
              f"TVOC (ppb): {tvoc}\t"
              f"eCO2 (ppm): {e_co2}")
        # Send indoor air quality data based on configuration
        if SEND_TO_API:
            send_indoor_data_to_api(ENS160_SENSOR_ID, aqi, tvoc, e_co2)

        if SEND_TO_TIMESCALEDB:
            send_indoor_data_to_timescaledb(ENS160_SENSOR_ID, aqi, tvoc, e_co2)

        time.sleep(ENS160_INTERVAL)

    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break
