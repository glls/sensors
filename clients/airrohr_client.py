import os
import time

import requests
from dotenv import load_dotenv

from services import send_air_data_to_timescaledb, send_air_data_to_api

# Load environment variables
load_dotenv()

AIRROHR_SENSOR_ID = os.environ.get('AIRROHR_SENSOR_ID')
AIRROHR_URL = os.environ.get('AIRROHR_URL')
AIRROHR_INTERVAL = 145
SEND_TO_TIMESCALEDB = os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true'
SEND_TO_API = os.environ.get('SEND_TO_API', 'False').lower() == 'true'

if AIRROHR_SENSOR_ID is None or AIRROHR_URL is None:
    print("Error: AIRROHR_SENSOR_ID or AIRROHR_URL not set in environment variables.")
    exit(1)

if SEND_TO_TIMESCALEDB is False and SEND_TO_API is False:
    print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
    exit(2)

if SEND_TO_TIMESCALEDB is True and SEND_TO_API is True:
    print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
    exit(3)


def get_airrohr_data():
    try:
        response = requests.get(AIRROHR_URL)
        response.raise_for_status()
        data = response.json()

        # Extract sensor values from response
        sensor_data = data.get('sensordatavalues', [])
        readings = {}
        for item in sensor_data:
            value_type = item.get('value_type')
            value = float(item.get('value', 0))
            readings[value_type] = value

        return {
            'pm10': readings.get('SDS_P1', 0),
            'pm25': readings.get('SDS_P2', 0),
            'temperature': readings.get('BME280_temperature', 0),
            'pressure': readings.get('BME280_pressure', 0) / 100.0,
            'humidity': readings.get('BME280_humidity', 0),
            'signal': readings.get('signal', 0)
        }
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None


while True:
    try:
        data = get_airrohr_data()
        if data:
            print(f"PM10: {data['pm10']:.2f} µg/m³\t"
                  f"PM2.5: {data['pm25']:.2f} µg/m³\t"
                  f"Temperature: {data['temperature']:.2f} °C\t"
                  f"Humidity: {data['humidity']:.2f} %\t"
                  f"Pressure: {data['pressure']:.2f} hPa\t"
                  f"Signal: {data['signal']} dBm")

            if SEND_TO_TIMESCALEDB:
                send_air_data_to_timescaledb(
                    int(AIRROHR_SENSOR_ID),
                    data['pm10'],
                    data['pm25'],
                    data['temperature'],
                    data['humidity'],
                    data['pressure'],
                    int(data['signal'])
                )
            elif SEND_TO_API:
                send_air_data_to_api(
                    int(AIRROHR_SENSOR_ID),
                    data['pm10'],
                    data['pm25'],
                    data['temperature'],
                    data['humidity'],
                    data['pressure'],
                    int(data['signal'])
                )

        time.sleep(AIRROHR_INTERVAL)

    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        continue
