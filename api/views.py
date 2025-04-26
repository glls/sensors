from rest_framework import generics

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor
from .serializers import (
    SensorSerializer,
    SensorDataTempSerializer,
    SensorDataAirSerializer,
    SensorDataIndoorSerializer,
)


class SensorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class SensorDataTempListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataTemp.objects.all()
    serializer_class = SensorDataTempSerializer


class SensorDataAirListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataAir.objects.all()
    serializer_class = SensorDataAirSerializer


class SensorDataIndoorListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataIndoor.objects.all()
    serializer_class = SensorDataIndoorSerializer
