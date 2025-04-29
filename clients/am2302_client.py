import os
import time
import sys
from typing import Dict, Any, Optional, Tuple

import adafruit_dht
import board
from dotenv import load_dotenv

import services


def load_config() -> Dict[str, Any]:
    """Load and validate environment configuration."""
    load_dotenv()

    config = {
        'send_to_timescaledb': os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true',
        'send_to_api': os.environ.get('SEND_TO_API', 'False').lower() == 'true',
        'dht22_sensor_id': os.environ.get('DHT22_SENSOR_ID'),
        'dht22_pin': board.D22,  # Default GPIO pin for DHT22
        'dht22_interval': 55  # Default delay time in seconds
    }

    if config['dht22_sensor_id'] is None:
        print("Error: DHT22_SENSOR_ID not set in environment variables.")
        sys.exit(1)

    if not config['send_to_timescaledb'] and not config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
        sys.exit(2)

    if config['send_to_timescaledb'] and config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
        sys.exit(3)

    return config


def setup_sensor(pin):
    """Initialize the DHT22 sensor."""
    try:
        # Using use_pulseio=False for Raspberry Pi compatibility
        sensor = adafruit_dht.DHT22(pin, use_pulseio=False)
        print("DHT22 sensor initialized successfully")
        return sensor
    except Exception as e:
        print(f"Error initializing DHT22 sensor: {e}")
        return None


def read_sensor_data(sensor: adafruit_dht.DHT22) -> Optional[Dict[str, float]]:
    """Read data from the DHT22 sensor."""
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity

        return {
            'temperature': temperature,
            'humidity': humidity
        }
    except RuntimeError:
        # Errors happen fairly often with DHT sensors, just return None
        return None


def validate_data(data: Dict[str, float]) -> bool:
    """Validate sensor data is within acceptable ranges."""
    if data['temperature'] < -40 or data['temperature'] > 80:
        print(f"Invalid temperature value: {data['temperature']}")
        return False

    if data['humidity'] < 0 or data['humidity'] > 100:
        print(f"Invalid humidity value: {data['humidity']}")
        return False

    return True


def send_data(config: Dict[str, Any], data: Dict[str, float]) -> None:
    """Send sensor data to the configured destination."""
    sensor_id = config['dht22_sensor_id']

    try:
        if config['send_to_timescaledb']:
            services.send_temp_data_to_timescaledb(
                sensor_id,
                data['temperature'],
                data['humidity']
            )
        elif config['send_to_api']:
            services.send_temp_data_to_api(
                sensor_id,
                data['temperature'],
                data['humidity']
            )
    except Exception as e:
        print(f"Failed to send data: {str(e)}")


def main():
    """Main execution function."""
    config = load_config()
    sensor = setup_sensor(config['dht22_pin'])

    if not sensor:
        print("Cannot continue without working sensor. Exiting.")
        sys.exit(4)

    try:
        while True:
            # Read sensor data
            data = read_sensor_data(sensor)

            if data:
                print(f"Temperature: {data['temperature']:.2f} °C\t"
                      f"Humidity: {data['humidity']:.2f} %")

                # Validate and send data
                if validate_data(data):
                    send_data(config, data)
            else:
                print("Failed to read from DHT sensor, retrying...")
                time.sleep(2)
                continue

            # Wait for next reading
            time.sleep(config['dht22_interval'])

    except KeyboardInterrupt:
        print("Program stopped by user")
    except Exception as e:
        sensor.exit()
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
