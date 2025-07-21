import os
from datetime import datetime
from typing import Dict, Any

import psycopg2
import pytz
import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException


def load_config() -> Dict[str, Any]:
    """Load environment configuration for services."""
    # Load environment variables from .env file
    load_dotenv()

    config = {
        # Database connection details
        'timescaledb_host': os.environ.get('TIMESCALEDB_HOST'),
        'timescaledb_port': os.environ.get('TIMESCALEDB_PORT', '5432'),
        'timescaledb_dbname': os.environ.get('TIMESCALEDB_DBNAME'),
        'timescaledb_user': os.environ.get('TIMESCALEDB_USER'),
        'timescaledb_password': os.environ.get('TIMESCALEDB_PASSWORD'),

        # API endpoints
        'api_temp_url': os.environ.get('API_TEMP_URL'),
        'api_indoor_url': os.environ.get('API_INDOOR_URL'),
        'api_air_url': os.environ.get('API_AIR_URL')
    }

    return config


# Load configuration once at module level
CONFIG = load_config()


def send_temp_data_to_api(sensor_id, temperature, humidity, pressure=None, time=None):
    try:
        payload = {
            "time": time if time else datetime.now(pytz.utc).isoformat(),
            "sensor_id": sensor_id,
            "temperature": temperature,
            "pressure": pressure,
            "humidity": humidity
        }
        response = requests.post(CONFIG['api_temp_url'], json=payload)
        if response.status_code == 201:
            print("Data sent to API successfully:", response.json())
        else:
            print(f"Failed to send data to API: {response.status_code} - {response.text}")
    except RequestException as e:
        print(f"HTTP request to API failed: {e}")


def send_temp_data_to_timescaledb(sensor_id, temperature, humidity, pressure=None, time=None):
    if not all([CONFIG['timescaledb_host'], CONFIG['timescaledb_dbname'],
                CONFIG['timescaledb_user'], CONFIG['timescaledb_password']]):
        print("Error: TimescaleDB connection details not fully configured via environment variables.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=CONFIG['timescaledb_host'],
            port=CONFIG['timescaledb_port'],
            dbname=CONFIG['timescaledb_dbname'],
            user=CONFIG['timescaledb_user'],
            password=CONFIG['timescaledb_password']
        )
        cur = conn.cursor()
        now_utc = time if time else datetime.now(pytz.utc).isoformat()
        sql = """
              INSERT INTO sensor_data_temp (time, sensor_id, temperature, humidity, pressure)
              VALUES (%s, %s, %s, %s, %s); \
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


def get_temp_data_last_timescaledb(sensor_id):
    if not all([CONFIG['timescaledb_host'], CONFIG['timescaledb_dbname'],
                CONFIG['timescaledb_user'], CONFIG['timescaledb_password']]):
        print("Error: TimescaleDB connection details not fully configured via environment variables.")
        return None

    conn = None
    try:
        conn = psycopg2.connect(
            host=CONFIG['timescaledb_host'],
            port=CONFIG['timescaledb_port'],
            dbname=CONFIG['timescaledb_dbname'],
            user=CONFIG['timescaledb_user'],
            password=CONFIG['timescaledb_password']
        )
        cur = conn.cursor()
        sql = """
              SELECT time, temperature, humidity, pressure
              FROM sensor_data_temp
              WHERE sensor_id = %s
              ORDER BY time DESC
              LIMIT 1; \
              """
        cur.execute(sql, (sensor_id,))
        row = cur.fetchone()

        if row:
            return {
                'time': row[0],
                'temperature': row[1],
                'humidity': row[2],
                'pressure': row[3]
            }
        return None

    except psycopg2.Error as e:
        print(f"Error fetching latest reading for sensor [{sensor_id}]: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()


def get_temp_data_last_api(sensor_id):
    """
    Fetches the last temperature reading for a specific sensor from the API.

    Args:
        sensor_id: The ID of the sensor to fetch data for

    Returns:
        A dictionary containing temperature data or None if not found
    """
    try:
        api_url = CONFIG['api_temp_url']
        if not api_url:
            print("Error: API_TEMP_URL not set in environment variables.")
            return None

        # Construct the URL for the latest temperature endpoint
        url = f"{api_url}latest/{sensor_id}/"

        # Make the API request
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return {
                'time': data.get('time'),
                'temperature': data.get('temperature'),
                'humidity': data.get('humidity'),
                'pressure': data.get('pressure')
            }
        elif response.status_code == 404:
            print(f"No temperature data found for sensor ID {sensor_id}")
            return None
        else:
            print(f"API request failed with status code: {response.status_code}")
            return None

    except RequestException as e:
        print(f"HTTP request to API failed: {e}")
        return None
    except Exception as e:
        print(f"Error getting last temperature data from API: {e}")
        return None


def send_indoor_data_to_api(sensor_id, aqi, tvoc, e_co2,  time=None):
    try:
        payload = {
            "time": time if time else datetime.now(pytz.utc).isoformat(),
            "sensor_id": sensor_id,
            "aqi": aqi,
            "tvoc": tvoc,
            "eco2": e_co2
        }
        response = requests.post(CONFIG['api_indoor_url'], json=payload)
        if response.status_code == 201:
            print("Data sent to API successfully:", response.json())
        else:
            print(f"Failed to send data to API: {response.status_code} - {response.text}")
    except RequestException as e:
        print(f"HTTP request to API failed: {e}")


def send_indoor_data_to_timescaledb(ens160_sensor_id, aqi, tvoc, e_co2, time=None):
    if not all([CONFIG['timescaledb_host'], CONFIG['timescaledb_dbname'],
                CONFIG['timescaledb_user'], CONFIG['timescaledb_password']]):
        print("Error: TimescaleDB connection details not fully configured via environment variables.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=CONFIG['timescaledb_host'],
            port=CONFIG['timescaledb_port'],
            dbname=CONFIG['timescaledb_dbname'],
            user=CONFIG['timescaledb_user'],
            password=CONFIG['timescaledb_password']
        )
        cur = conn.cursor()
        now_utc = time if time else datetime.now(pytz.utc).isoformat()
        sql = """
              INSERT INTO sensor_data_indoor (time, sensor_id, aqi, tvoc, eco2)
              VALUES (%s, %s, %s, %s, %s); \
              """
        data = (now_utc, ens160_sensor_id, aqi, tvoc, e_co2)
        cur.execute(sql, data)
        conn.commit()
        print(f"Sensor [{ens160_sensor_id}] indoor data sent to TimescaleDB successfully.")
    except psycopg2.Error as e:
        print(f"Error sending sensor [{ens160_sensor_id}] indoor data to TimescaleDB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()


def send_air_data_to_api(sensor_id, pm10, pm25, temperature=None, humidity=None, pressure=None, signal=None, time=None):
    try:
        payload = {
            "time": time if time else datetime.now(pytz.utc).isoformat(),
            "sensor_id": sensor_id,
            "p1": pm10,
            "p2": pm25,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "signal": signal
        }
        response = requests.post(CONFIG['api_air_url'], json=payload)
        if response.status_code == 201:
            print("Data sent to API successfully:", response.json())
        else:
            print(f"Failed to send data to API: {response.status_code} - {response.text}")
    except RequestException as e:
        print(f"HTTP request to API failed: {e}")


def send_air_data_to_timescaledb(sensor_id, pm10, pm25, temperature=None, humidity=None, pressure=None, signal=None,
                                 time=None):
    if not all([CONFIG['timescaledb_host'], CONFIG['timescaledb_dbname'],
                CONFIG['timescaledb_user'], CONFIG['timescaledb_password']]):
        print("Error: TimescaleDB connection details not fully configured via environment variables.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=CONFIG['timescaledb_host'],
            port=CONFIG['timescaledb_port'],
            dbname=CONFIG['timescaledb_dbname'],
            user=CONFIG['timescaledb_user'],
            password=CONFIG['timescaledb_password']
        )
        cur = conn.cursor()
        now_utc = time if time else datetime.now(pytz.utc).isoformat()
        sql = """
              INSERT INTO sensor_data_air (time, sensor_id, p1, p2, temperature, humidity, pressure, signal)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s); \
              """
        data = (now_utc, sensor_id, pm10, pm25, temperature, humidity, pressure, signal)
        cur.execute(sql, data)
        conn.commit()
        print(f"Sensor [{sensor_id}] air data sent to TimescaleDB successfully.")
    except psycopg2.Error as e:
        print(f"Error sending sensor [{sensor_id}] air data to TimescaleDB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()
