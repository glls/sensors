import os
import time
from datetime import datetime

import bme280
import psycopg2
import pytz  # For timezone handling
import requests
import smbus2
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Load environment variables from .env file
load_dotenv()

# database connection details
SEND_TO_TIMESCALEDB = os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true'
TIMESCALEDB_HOST = os.environ.get('TIMESCALEDB_HOST')
TIMESCALEDB_PORT = os.environ.get('TIMESCALEDB_PORT', '5432')
TIMESCALEDB_DBNAME = os.environ.get('TIMESCALEDB_DBNAME')
TIMESCALEDB_USER = os.environ.get('TIMESCALEDB_USER')
TIMESCALEDB_PASSWORD = os.environ.get('TIMESCALEDB_PASSWORD')
# unique sensor ID
BME_SENSOR_ID = os.environ.get('BME_SENSOR_ID')
# BME280 sensor address (default address)
BME280_ADDRESS = 0x76
# delay time for sensor readings (in seconds)
BME280_INTERVAL = 55

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

# API endpoint
API_URL = os.environ.get('API_URL')
SENSOR_ID = os.environ.get('SENSOR_ID', 1)


def send_data_to_api(temperature, pressure, humidity):
    try:
        payload = {
            "time": datetime.now(pytz.utc).isoformat(),
            "sensor_id": SENSOR_ID,
            "temperature": temperature,
            "pressure": pressure,
            "humidity": humidity
        }
        response = requests.post(API_URL, json=payload)
        if response.status_code == 201:
            print("Data sent to API successfully:", response.json())
        else:
            print(f"Failed to send data to API: {response.status_code} - {response.text}")
    except RequestException as e:
        print(f"HTTP request to API failed: {e}")


def send_data_to_timescaledb(temperature, pressure, humidity):
    if not all([TIMESCALEDB_HOST, TIMESCALEDB_DBNAME, TIMESCALEDB_USER, TIMESCALEDB_PASSWORD]):
        print("Error: TimescaleDB connection details not fully configured via environment variables.")
        return

    conn = None
    try:
        conn = psycopg2.connect(host=TIMESCALEDB_HOST, port=TIMESCALEDB_PORT, dbname=TIMESCALEDB_DBNAME,
                                user=TIMESCALEDB_USER, password=TIMESCALEDB_PASSWORD)
        cur = conn.cursor()
        now_utc = datetime.now(pytz.utc).isoformat()
        sql = """
            INSERT INTO sensor_data_temp (time, sensor_id, temperature, humidity, pressure)
            VALUES (%s, %s, %s, %s, %s);
        """
        data = (now_utc, SENSOR_ID, temperature, humidity, pressure)
        cur.execute(sql, data)
        conn.commit()
        print("Data sent to TimescaleDB successfully.")
    except psycopg2.Error as e:
        print(f"Error sending data to TimescaleDB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()


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
                  f"Pressure: {pressure:.2f} hPa\t"
                  f"Humidity: {humidity:.2f} %")

            # Send data based on configuration
            if API_URL:
                send_data_to_api(temperature, pressure, humidity)

            if SEND_TO_TIMESCALEDB:
                send_data_to_timescaledb(temperature, pressure, humidity)

        time.sleep(BME280_INTERVAL)

    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break