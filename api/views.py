from rest_framework import generics

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor
from .serializers import (
    SensorSerializer,
    SensorDataTempSerializer,
    SensorDataAirSerializer,
    SensorDataIndoorSerializer,
)


class SensorDataTempCreateView(generics.CreateAPIView):
    queryset = SensorDataTemp.objects.all()
    serializer_class = SensorDataTempSerializer


class SensorDataAirCreateView(generics.CreateAPIView):
    queryset = SensorDataAir.objects.all()
    serializer_class = SensorDataAirSerializer


class SensorDataIndoorCreateView(generics.CreateAPIView):
    queryset = SensorDataIndoor.objects.all()
    serializer_class = SensorDataIndoorSerializer


# Optional views for listing data (for debugging or other purposes)
class SensorListAPIView(generics.ListAPIView):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class SensorDataTempListAPIView(generics.ListAPIView):
    queryset = SensorDataTemp.objects.all()
    serializer_class = SensorDataTempSerializer


class SensorDataAirListAPIView(generics.ListAPIView):
    queryset = SensorDataAir.objects.all()
    serializer_class = SensorDataAirSerializer


class SensorDataIndoorListAPIView(generics.ListAPIView):
    queryset = SensorDataIndoor.objects.all()
    serializer_class = SensorDataIndoorSerializer

