import os
import time

import adafruit_dht
import board
import pytz  # For timezone handling
from dotenv import load_dotenv

from services import send_data_to_api, send_data_to_timescaledb

# Load environment variables from .env file
load_dotenv()

# database connection details
SEND_TO_TIMESCALEDB = os.environ.get('SEND_TO_TIMESCALEDB', 'False').lower() == 'true'
SEND_TO_API = os.environ.get('SEND_TO_API', 'False').lower() == 'true'

# unique sensor ID
DHT22_SENSOR_ID = os.environ.get('DHT22_SENSOR_ID')
# delay time for sensor readings (in seconds)
DHT22_INTERVAL = 55

if DHT22_SENSOR_ID is None:
    print("Error: DHT_SENSOR_ID not set in environment variables.")
    exit(1)

# You can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
dhtDevice = adafruit_dht.DHT22(board.D22, use_pulseio=False)

while True:
    try:
        # Print the values to the serial port
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity

        # Print the readings
        print(f"Temperature: {temperature:.2f} °C\t"
              f"Humidity: {humidity:.2f} %")

        if SEND_TO_API:
            send_data_to_api(DHT22_SENSOR_ID, temperature, humidity)

        if SEND_TO_TIMESCALEDB:
            send_data_to_timescaledb(DHT22_SENSOR_ID, temperature, humidity)

        time.sleep(DHT22_INTERVAL)

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error
