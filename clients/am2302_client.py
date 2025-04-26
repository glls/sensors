import os
import time

import adafruit_dht
import board
from dotenv import load_dotenv

from services import send_temp_data_to_api, send_temp_data_to_timescaledb

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

if SEND_TO_TIMESCALEDB is False and SEND_TO_API is False:
    print("Error: SEND_TO_TIMESCALEDB or SEND_TO_API must be set to True in environment variables.")
    exit(2)

if SEND_TO_TIMESCALEDB is True and SEND_TO_API is True:
    print("Error: SEND_TO_TIMESCALEDB and SEND_TO_API cannot be both True in environment variables.")
    exit(3)

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

        if SEND_TO_TIMESCALEDB:
            send_temp_data_to_timescaledb(DHT22_SENSOR_ID, temperature, humidity)
        elif SEND_TO_API:
            send_temp_data_to_api(DHT22_SENSOR_ID, temperature, humidity)

        time.sleep(DHT22_INTERVAL)

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        dhtDevice.exit()
        print('An unexpected error occurred:', str(e))
        break
