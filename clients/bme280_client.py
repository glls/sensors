import time

import bme280
import requests
import smbus2
from requests.exceptions import RequestException

# BME280 sensor address (default address)
address = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)

# API endpoint
API_URL = "http://192.168.33.5:3000/api/sensors/temperature/"

while True:
    try:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        # Extract temperature, pressure, and humidity
        temperature = data.temperature
        pressure = data.pressure
        humidity = data.humidity

        # Prepare the payload
        payload = {
            "temperature": temperature,
            "pressure": pressure,
            "humidity": humidity
        }

        # Print the readings
        print(f"Temperature: {temperature:.2f} °C\t"
              f"Pressure: {pressure:.2f} hPa\t"
              f"Humidity: {humidity:.2f} %")

        # Send POST request
        try:
            response = requests.post(API_URL, json=payload)
            # Check response status
            if response.status_code == 201:
                print("Data sent successfully:", response.json())
            else:
                print("Failed to send data:", response.status_code, response.text)
        except RequestException as e:
            print("HTTP request failed:", str(e))

        time.sleep(60)

    except KeyboardInterrupt:
        print('Program stopped')
        break
    except Exception as e:
        print('An unexpected error occurred:', str(e))
        break
