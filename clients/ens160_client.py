import os
import time
import sys
from typing import Dict, Optional, Any
from datetime import datetime
import pytz

from dotenv import load_dotenv

import services
from DFRobot_ENS160 import DFRobot_ENS160_I2C, ENS160_STANDARD_MODE


def load_config() -> Dict[str, Any]:
    """Load and validate environment configuration."""
    load_dotenv()

    config = {
        'send_to_timescaledb': os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true',
        'send_to_api': os.environ.get('SEND_TO_API', 'False').lower() == 'true',
        'ens160_sensor_id': os.environ.get('ENS160_SENSOR_ID'),
        'bme280_sensor_id': os.environ.get('BME280_SENSOR_ID'),
        'ens160_interval': 55
    }

    if config['ens160_sensor_id'] is None:
        print("Error: ENS160_SENSOR_ID not set in environment variables.")
        sys.exit(1)

    if not config['send_to_timescaledb'] and not config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
        sys.exit(2)

    if config['send_to_timescaledb'] and config['send_to_api']:
        print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
        sys.exit(3)

    return config


def validate_data(aqi: int, tvoc: int, e_co2: int) -> bool:
    """Validate sensor data is within acceptable ranges."""
    if aqi is None or aqi < 1 or aqi > 5:
        print("Invalid AQI value")
        return False

    if tvoc is None or tvoc < 0 or tvoc > 65000:
        print("Invalid TVOC value")
        return False

    if e_co2 is None or e_co2 < 400 or e_co2 > 65000:
        print("Invalid eCO2 value")
        return False

    return True


def setup_sensor(sensor: DFRobot_ENS160_I2C, ambient_temp: float = 25.0, ambient_hum: float = 50.0) -> bool:
    """Initialize the ENS160 sensor with provided temperature and humidity."""
    max_attempts = 5
    attempts = 0

    while attempts < max_attempts:
        if sensor.begin():
            print("Sensor initialized successfully")
            break

        print(f"Failed to initialize sensor. Attempt {attempts + 1} of {max_attempts}")
        attempts += 1
        time.sleep(3)

    if attempts >= max_attempts:
        print(f"Failed to initialize sensor after {max_attempts} attempts")
        return False

    sensor.set_PWR_mode(ENS160_STANDARD_MODE)
    sensor.set_temp_and_hum(ambient_temp, ambient_hum)
    print(f"Sensor configured with temp: {ambient_temp:.1f}°C, humidity: {ambient_hum:.1f}%")

    return True


def get_environmental_data(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get the latest temperature and humidity data from BME280 sensor."""
    bme280_id = config['bme280_sensor_id']
    if not bme280_id:
        print("BME280_SENSOR_ID not set, using default values")
        return None

    try:
        if config['send_to_timescaledb']:
            data = services.get_temp_data_last_timescaledb(bme280_id)
        elif config['send_to_api']:
            data = services.get_temp_data_last_api(bme280_id)
        else:
            return None

        if data:
            print(
                f"Retrieved environmental data: {data['temperature']:.2f}°C, {data['humidity']:.2f}% on {data['time']}")
        return data
    except Exception as e:
        print(f"Failed to retrieve environmental data: {str(e)}")
        return None


def send_data(config: Dict[str, Any], data: dict[str, Any]) -> None:
    """Send sensor data to the configured destination."""
    sensor_id = config['ens160_sensor_id']

    try:
        if config['send_to_timescaledb']:
            services.send_indoor_data_to_timescaledb(sensor_id, data['aqi'], data['tvoc'], data['e_co2'], data['time'])
        elif config['send_to_api']:
            services.send_indoor_data_to_api(sensor_id, data['aqi'], data['tvoc'], data['e_co2'], data['time'])
    except Exception as e:
        print(f"Failed to send data: {str(e)}")


def main():
    """Main execution function."""
    config = load_config()
    sensor = DFRobot_ENS160_I2C(i2c_addr=0x53, bus=1)
    buffer = []

    # Initial setup
    env_data = get_environmental_data(config)
    if env_data:
        setup_success = setup_sensor(sensor, env_data['temperature'], env_data['humidity'])
    else:
        setup_success = setup_sensor(sensor)

    if not setup_success:
        print("Failed to set up the sensor. Exiting.")
        sys.exit(4)

    try:
        while True:

            # Try to resend buffered data first
            new_buffer = []
            for buffered_data in buffer:
                if not send_data(config, buffered_data):
                    new_buffer.append(buffered_data)
                    print(f"Failed to resend buffered data will retry later. Buffer size: {len(new_buffer)}")
            buffer = new_buffer

            # Update environmental data before each measurement
            env_data = get_environmental_data(config)
            if env_data:
                sensor.set_temp_and_hum(env_data['temperature'], env_data['humidity'])

            try:
                # Get sensor readings
                sensor_status = sensor.get_ENS160_status()
                data = {
                    'aqi': sensor.get_AQI,
                    'tvoc': sensor.get_TVOC_ppb,
                    'e_co2': sensor.get_ECO2_ppm,
                    'time': datetime.now(pytz.utc).isoformat()
                }

                print(f"Status: {sensor_status}\t"
                      f"AQI: {data['aqi']} (1-5)\t"
                      f"TVOC: {data['tvoc']} ppb\t"
                      f"eCO2: {data['e_co2']} ppm\t"
                      f"Time: {time}")

                # Validate and send data
                if validate_data(data):
                    if not send_data(config, data):
                        buffer.append(data)
                        print(f"Failed to send new data, will buffer and retry later. Buffer size: {len(buffer)}")

                # Wait for next reading
                time.sleep(config['ens160_interval'])

            except Exception as e:
                print(f"Error during sensor reading: {str(e)}")
                time.sleep(10)

    except KeyboardInterrupt:
        print("Program stopped by user")


if __name__ == "__main__":
    main()
