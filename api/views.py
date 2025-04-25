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


class LastSensorDataTempAPIView(APIView):
    """
    API view to retrieve the last temperature reading for a specific sensor.
    """

    def get(self, request, sensor_id, format=None):
        try:
            # Ensure the sensor exists
            sensor = get_object_or_404(Sensor, pk=sensor_id)

            # Get the latest reading for this sensor
            last_reading = SensorDataTemp.objects.filter(sensor=sensor).order_by('-time').first()

            if not last_reading:
                return Response({"detail": "No temperature data found for this sensor."},
                                status=status.HTTP_404_NOT_FOUND)

            serializer = SensorDataTempSerializer(last_reading)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error
            print(f"Error fetching last temperature data: {e}")
            return Response({"error": "An unexpected error occurred."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
