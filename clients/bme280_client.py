import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import bme280
import pytz
import smbus2
from dotenv import load_dotenv

import services


def load_config() -> Dict[str, Any]:
    """Load and validate environment configuration."""
    load_dotenv()

    config = {
        'send_to_timescaledb': os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true',
        'send_to_api': os.environ.get('SEND_TO_API', 'False').lower() == 'true',
        'bme280_sensor_id': os.environ.get('BME280_SENSOR_ID'),
        'bme280_address': 0x76,  # Default address for BME280
        'bme280_interval': 55  # Default delay time in seconds
    }

    if config['bme280_sensor_id'] is None:
        print("Error: BME280_SENSOR_ID not set in environment variables.")
        sys.exit(1)

    if not config['send_to_timescaledb'] and not config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
        sys.exit(2)

    if config['send_to_timescaledb'] and config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
        sys.exit(3)

    return config


def setup_sensor() -> Tuple[Optional[smbus2.SMBus], Optional[Any]]:
    """Initialize the I2C bus and load calibration parameters."""
    try:
        bus = smbus2.SMBus(1)
        # Load calibration parameters
        calibration_params = bme280.load_calibration_params(bus, 0x76)
        print("BME280 sensor initialized successfully")
        return bus, calibration_params
    except FileNotFoundError:
        print("Error: I2C bus not found. Sensor readings will be simulated.")
        return None, None
    except Exception as e:
        print(f"Error initializing I2C bus: {e}. Sensor readings will be simulated.")
        return None, None


def read_sensor_data(bus: smbus2.SMBus, address: int, calibration_params: Any) -> dict[str, Any]:
    """Read data from the BME280 sensor."""
    data = bme280.sample(bus, address, calibration_params)
    return {
        'temperature': data.temperature,
        'humidity': data.humidity,
        'pressure': data.pressure,
        'time': datetime.now(pytz.utc).isoformat()
    }


def validate_data(data: Dict[str, float]) -> bool:
    """Validate sensor data is within acceptable ranges."""
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
    sensor_id = config['bme280_sensor_id']
    success = False

    if config['send_to_timescaledb']:
        success = services.send_temp_data_to_timescaledb(
            sensor_id,
            data['temperature'],
            data['humidity'],
            data['pressure'],
            data['time']
        )
    elif config['send_to_api']:
        success = services.send_temp_data_to_api(
            sensor_id,
            data['temperature'],
            data['humidity'],
            data['pressure'],
            data['time']
        )
    return success


def main():
    """Main execution function."""
    config = load_config()
    buffer = []
    bus, calibration_params = setup_sensor()

    if not bus or not calibration_params:
        print("Cannot continue without working sensor. Exiting.")
        sys.exit(4)

    try:
        while True:
            try:
                # Try to resend buffered data first
                new_buffer = []
                for buffered_data in buffer:
                    if not send_data(config, buffered_data):
                        new_buffer.append(buffered_data)
                        print(f"Failed to resend buffered data will retry later. Buffer size: {len(new_buffer)}")
                buffer = new_buffer

                # Read sensor data
                data = read_sensor_data(bus, config['bme280_address'], calibration_params)
                print(f"Temperature: {data['temperature']:.2f} °C\t"
                      f"Humidity: {data['humidity']:.2f} %\t"
                      f"Pressure: {data['pressure']:.2f} hPa\t"
                      f"Time: {data['time']}")

                # Validate and send data
                if validate_data(data):
                    if not send_data(config, data):
                        buffer.append(data)
                        print(f"Failed to send new data, will buffer and retry later. Buffer size: {len(buffer)}")

                # Wait for next reading
                time.sleep(config['bme280_interval'])

            except Exception as e:
                print(f"Error during sensor reading: {str(e)}")
                time.sleep(10)  # Wait before retrying

    except KeyboardInterrupt:
        print("Program stopped by user")


if __name__ == "__main__":
    main()
