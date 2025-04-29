from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor
from .serializers import (
    SensorSerializer,
    SensorDataTempSerializer,
    SensorDataAirSerializer,
    SensorDataIndoorSerializer,
)


def broadcast_sensor_data(sensor_id, data):
    """
    Broadcast sensor data to the WebSocket group for the specific sensor.
    """
    print(f"Broadcasting data to sensor {sensor_id}: {data}")
    channel_layer = get_channel_layer()
    logger.info(f"Broadcasting data to sensor {sensor_id}: {data}")
    async_to_sync(channel_layer.group_send)(
        f'sensor_data_{sensor_id}',
        {
            'type': 'send_sensor_data',
            'data': data
        }
    )


class SensorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sensor.objects.all().order_by('id')
    serializer_class = SensorSerializer

class SensorDataTempListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataTemp.objects.all().order_by('-time')
    serializer_class = SensorDataTempSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        data = {
            'sensor_id': instance.sensor_id.id,
            'temperature': instance.temperature,
            'humidity': instance.humidity,
            'pressure': instance.pressure,
            'time': instance.time.isoformat(),
        }
        broadcast_sensor_data(instance.sensor_id.id, data)


class SensorDataAirListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataAir.objects.all().order_by('-time')
    serializer_class = SensorDataAirSerializer

    def perform_create(self, serializer):
        # Save the new data
        instance = serializer.save()

        # Prepare the data for broadcasting
        data = {
            'sensor_id': instance.sensor_id.id,
            'pm10': instance.p1,
            'pm25': instance.p2,
            'temperature': instance.temperature,
            'humidity': instance.humidity,
            'pressure': instance.pressure,
            'signal': instance.signal,
            'time': instance.time.isoformat(),
        }

        # Broadcast the data via WebSocket
        broadcast_sensor_data(instance.sensor_id.id, data)

class SensorDataIndoorListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataIndoor.objects.all().order_by('-time')
    serializer_class = SensorDataIndoorSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        data = {
            'sensor_id': instance.sensor_id.id,
            'aqi': instance.aqi,
            'tvoc': instance.tvoc,
            'eco2': instance.eco2,
            'time': instance.time.isoformat(),
        }
        broadcast_sensor_data(instance.sensor_id.id, data)

class SensorDataTempLatestAPIView(generics.RetrieveAPIView):
    serializer_class = SensorDataTempSerializer
    pagination_class = None  # Disable pagination for this view

    def get_object(self):
        sensor_id = self.kwargs.get('sensor_id')
        return SensorDataTemp.objects.filter(
            sensor_id=sensor_id
        ).order_by('-time').first()
