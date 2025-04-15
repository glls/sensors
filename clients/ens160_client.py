import os
import time

from DFRobot_ENS160 import *
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

'''
  # Select communication interface I2C, please comment out SPI interface. And vise versa.
  # I2C : For Fermion version, I2C communication address setting: 
  #         connect SDO pin to GND, I2C address is 0×52 now;
  #         connect SDO pin to VCC(3v3), I2C address is 0x53 now
  # SPI : Set up digital pin according to the on-board pin connected with SPI chip-select pin.
'''
sensor = DFRobot_ENS160_I2C(i2c_addr=0x53, bus=1)


def setup(ambient_temp=25.0, ambient_hum=50.0):
    while (sensor.begin() == False):
        print('Please check that the device is properly connected')
        time.sleep(3)
    print("sensor begin successfully!!!")

    '''
      # Configure power mode
      # mode Configurable power mode:
      #   ENS160_SLEEP_MODE: DEEP SLEEP mode (low power standby)
      #   ENS160_IDLE_MODE: IDLE mode (low-power)
      #   ENS160_STANDARD_MODE: STANDARD Gas Sensing Modes
    '''
    sensor.set_PWR_mode(ENS160_STANDARD_MODE)

    '''
      # Users write ambient temperature and relative humidity into ENS160 for calibration and compensation of the measured gas data.
      # ambient_temp Compensate the current ambient temperature, float type, unit: C
      # relative_humidity Compensate the current ambient humidity, float type, unit: %rH
    '''
    sensor.set_temp_and_hum(ambient_temp, ambient_hum)


# Get the last sensor data from BME280_SENSOR_ID in TimescaleDB
last_data = get_temp_data_last(BME280_SENSOR_ID)
if last_data:
    print(f"Last sensor data from TimescaleDB: {last_data['temperature']:.4f} °C\t {last_data['humidity']:.4f} %")
    setup(last_data['temperature'], last_data['humidity'])
else:
    setup()

while True:
    try:
        sensor_status = sensor.get_ENS160_status()
        aqi = sensor.get_AQI
        tvoc = sensor.get_TVOC_ppb
        e_co2 = sensor.get_ECO2_ppm
        print(f"status: {sensor_status}\tAQI: {aqi} (1-5)\tTVOC: {tvoc} (ppb)\teCO2: {e_co2} (ppm)")
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
