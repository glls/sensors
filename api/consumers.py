import json

from channels.generic.websocket import AsyncWebsocketConsumer


class SensorsDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("sensors", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensors", self.channel_name)

    async def sensor_update(self, event):
        # Send the sensor data to the WebSocket
        await self.send(text_data=json.dumps(event['data']))
