import os
import sys
import time
from datetime import datetime
from typing import Dict, Optional, Any

import pytz
import requests
from dotenv import load_dotenv

import services


def load_config() -> Dict[str, Any]:
    """Load and validate environment configuration."""
    load_dotenv()

    config = {
        'send_to_timescaledb': os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true',
        'send_to_api': os.environ.get('SEND_TO_API', 'False').lower() == 'true',
        'airrohr_sensor_id': os.environ.get('AIRROHR_SENSOR_ID'),
        'airrohr_url': os.environ.get('AIRROHR_URL'),
        'airrohr_interval': 145
    }

    if config['airrohr_sensor_id'] is None or config['airrohr_url'] is None:
        print("Error: AIRROHR_SENSOR_ID or AIRROHR_URL not set in environment variables.")
        sys.exit(1)

    if not config['send_to_timescaledb'] and not config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
        sys.exit(2)

    if config['send_to_timescaledb'] and config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
        sys.exit(3)

    return config


def get_airrohr_data(url: str) -> Optional[Dict[str, Any]]:
    """Get air quality data from AirRohr sensor."""
    try:
        response = requests.get(url)
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
            'signal': readings.get('signal', 0),
            'time': datetime.now(pytz.utc).isoformat()
        }
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing data: {e}")
        return None


def validate_data(data: Dict[str, float]) -> bool:
    """Validate sensor data is within acceptable ranges."""
    if data['pm10'] < 0 or data['pm10'] > 1000:
        print(f"Invalid PM10 value: {data['pm10']}")
        return False

    if data['pm25'] < 0 or data['pm25'] > 1000:
        print(f"Invalid PM2.5 value: {data['pm25']}")
        return False

    if data['temperature'] < -40 or data['temperature'] > 85:
        print(f"Invalid temperature value: {data['temperature']}")
        return False

    if data['humidity'] < 0 or data['humidity'] > 100:
        print(f"Invalid humidity value: {data['humidity']}")
        return False

    if data['pressure'] < 300 or data['pressure'] > 1100:
        print(f"Invalid pressure value: {data['pressure']}")
        return False

    return True


def send_data(config: Dict[str, Any], data: Dict[str, float]) -> bool:
    """Send sensor data to the configured destination."""
    sensor_id = int(config['airrohr_sensor_id'])
    success = False

    if config['send_to_timescaledb']:
        success = services.send_air_data_to_timescaledb(
            sensor_id,
            data['pm10'],
            data['pm25'],
            data['temperature'],
            data['humidity'],
            data['pressure'],
            int(data['signal']),
            data['time']
        )
    elif config['send_to_api']:
        success = services.send_air_data_to_api(
            sensor_id,
            data['pm10'],
            data['pm25'],
            data['temperature'],
            data['humidity'],
            data['pressure'],
            int(data['signal']),
            data['time']
        )

    return success


def main():
    """Main execution function."""
    config = load_config()
    buffer = []

    try:
        while True:

            # Try to resend buffered data first
            new_buffer = []
            for buffered_data in buffer:
                if not send_data(config, buffered_data):
                    new_buffer.append(buffered_data)
                    print(f"Failed to resend buffered data will retry later. Buffer size: {len(new_buffer)}")
            buffer = new_buffer

            # Fetch new data from AirRohr sensor
            data = get_airrohr_data(config['airrohr_url'])
            if data:
                print(f"PM10: {data['pm10']:.2f} µg/m³\t"
                      f"PM2.5: {data['pm25']:.2f} µg/m³\t"
                      f"Temperature: {data['temperature']:.2f} °C\t"
                      f"Humidity: {data['humidity']:.2f} %\t"
                      f"Pressure: {data['pressure']:.2f} hPa\t"
                      f"Signal: {data['signal']} dBm\t"
                      f"Time: {data['time']}")

                if validate_data(data):
                    if not send_data(config, data):
                        buffer.append(data)
                        print(f"Failed to send new data, will buffer and retry later. Buffer size: {len(buffer)}")

            time.sleep(config['airrohr_interval'])

    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(4)


if __name__ == "__main__":
    main()
