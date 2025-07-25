import os

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from dotenv import load_dotenv
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor
from .serializers import (
    SensorSerializer,
    SensorDataTempSerializer,
    SensorDataAirSerializer,
    SensorDataIndoorSerializer,
)

LAT, LON = 40.678967, 22.917712  # Thessaloniki, Greece


def broadcast_sensor_data(data):
    """
    Broadcast sensor data to the WebSocket group for all sensors.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)('sensors', {'type': 'sensor_update', 'data': data})


class SensorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sensor.objects.all().order_by('id')
    serializer_class = SensorSerializer


class SensorDataTempListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataTemp.objects.all().order_by('-time')
    serializer_class = SensorDataTempSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        data = {
            'sensor_id': instance.sensor_id,
            'type': 'temperature',
            'temperature': instance.temperature,
            'humidity': instance.humidity,
            'pressure': instance.pressure,
            'time': instance.time.isoformat(),
        }
        broadcast_sensor_data(data)


class SensorDataAirListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataAir.objects.all().order_by('-time')
    serializer_class = SensorDataAirSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        data = {
            'sensor_id': instance.sensor_id,
            'type': 'air',
            'pm10': instance.p1,
            'pm25': instance.p2,
            'temperature': instance.temperature,
            'humidity': instance.humidity,
            'pressure': instance.pressure,
            'signal': instance.signal,
            'time': instance.time.isoformat(),
        }
        broadcast_sensor_data(data)


class SensorDataIndoorListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataIndoor.objects.all().order_by('-time')
    serializer_class = SensorDataIndoorSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        data = {
            'sensor_id': instance.sensor_id,
            'type': 'indoor',
            'aqi': instance.aqi,
            'tvoc': instance.tvoc,
            'eco2': instance.eco2,
            'time': instance.time.isoformat(),
        }
        broadcast_sensor_data(data)


class SensorDataTempLatestAPIView(generics.RetrieveAPIView):
    serializer_class = SensorDataTempSerializer
    pagination_class = None  # Disable pagination for this view

    def get_object(self):
        sensor_id = self.kwargs.get('sensor_id')
        return SensorDataTemp.objects.filter(
            sensor_id=sensor_id
        ).order_by('-time').first()


# api/views.py
class WeatherDataAPIView(APIView):
    def get(self, request, *args, **kwargs):
        load_dotenv()
        API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

        if not API_KEY:
            return Response(
                {"error": "Weather API key is missing. Please configure it."},
                status=status.HTTP_200_OK
            )

        url = f'https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric'
        response = requests.get(url)

        if response.status_code != 200:
            return Response(
                {"error": f"Failed to fetch weather data: {response.status_code} {response.text}"},
                status=status.HTTP_200_OK
            )

        return Response(response.json())


class AirPollutionDataAPIView(APIView):
    def get(self, request, *args, **kwargs):
        load_dotenv()
        API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

        if not API_KEY:
            return Response(
                {"error": "Air pollution API key is missing. Please configure it."},
                status=status.HTTP_200_OK
            )

        url = f'https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}'
        response = requests.get(url)

        if response.status_code != 200:
            return Response(
                {"error": f"Failed to fetch air pollution data: {response.status_code} {response.text}"},
                status=status.HTTP_200_OK
            )

        return Response(response.json())


class ToggleSchedulerAPIView(APIView):
    def get(self, request, *args, **kwargs):
        global scheduler_enabled
        action = request.query_params.get("action", "").lower()
        if action == "enable":
            scheduler_enabled = True
            return Response({"status": "Scheduler enabled"}, status=status.HTTP_200_OK)
        elif action == "disable":
            scheduler_enabled = False
            return Response({"status": "Scheduler disabled"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
