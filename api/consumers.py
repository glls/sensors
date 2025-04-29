import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SensorDataConsumer(AsyncWebsocketConsumer):
    connected_clients = set()

    async def connect(self):
        # Extract sensor ID from the WebSocket URL
        self.sensor_id = self.scope['url_route']['kwargs']['sensor_id']
        self.group_name = f'sensor_data_{self.sensor_id}'

        # Add the client to the sensor-specific group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"WebSocket connected for sensor {self.sensor_id}")

    async def disconnect(self, close_code):
        # Remove the client from the sensor-specific group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"WebSocket disconnected for sensor {self.sensor_id}")

    async def send_sensor_data(self, event):
        # Send the sensor data to the WebSocket client
        data = event['data']
        logger.info(f"Sending data to WebSocket: {data}")

        await self.send(text_data=json.dumps(data))
