from channels.generic.websocket import AsyncWebsocketConsumer
import json

class SensorDataConsumer(AsyncWebsocketConsumer):
    connected_clients = set()

    async def connect(self):
        self.group_name = 'sensor_data'
        SensorDataConsumer.connected_clients.add(self.channel_name)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        SensorDataConsumer.connected_clients.discard(self.channel_name)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass

    async def send_sensor_data(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))