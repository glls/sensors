import os
from datetime import datetime

import psycopg2
import pytz
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

# Load environment variables from .env file
load_dotenv()

# Database connection details
TIMESCALEDB_HOST = os.environ.get('TIMESCALEDB_HOST')
TIMESCALEDB_PORT = os.environ.get('TIMESCALEDB_PORT', '5432')
TIMESCALEDB_DBNAME = os.environ.get('TIMESCALEDB_DBNAME')
TIMESCALEDB_USER = os.environ.get('TIMESCALEDB_USER')
TIMESCALEDB_PASSWORD = os.environ.get('TIMESCALEDB_PASSWORD')
API_URL = os.environ.get('API_URL')


def send_data_to_api(sensor_id, temperature, humidity, pressure=None):
    try:
        payload = {
            "time": datetime.now(pytz.utc).isoformat(),
            "sensor_id": sensor_id,
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


def send_data_to_timescaledb(sensor_id, temperature, humidity, pressure=None):
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
        data = (now_utc, sensor_id, temperature, humidity, pressure)
        cur.execute(sql, data)
        conn.commit()
        print(f"Sensor [{sensor_id}] data sent to TimescaleDB successfully.")
    except psycopg2.Error as e:
        print(f"Error sending sensor [{sensor_id}] data to TimescaleDB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
