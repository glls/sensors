import json

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include

from core.models import SensorDataAir, SensorDataIndoor, SensorDataTemp


def _serialize_air(obj):
    if not obj:
        return None
    return {
        'sensor_id': obj.sensor_id,
        'type': 'air',
        'pm10': obj.p1,
        'pm25': obj.p2,
        'temperature': obj.temperature,
        'humidity': obj.humidity,
        'pressure': obj.pressure,
        'signal': obj.signal,
        'time': obj.time.isoformat(),
    }


def _serialize_indoor(obj):
    if not obj:
        return None
    return {
        'sensor_id': obj.sensor_id,
        'type': 'indoor',
        'aqi': obj.aqi,
        'tvoc': obj.tvoc,
        'eco2': obj.eco2,
        'time': obj.time.isoformat(),
    }


def _serialize_temp(obj):
    if not obj:
        return None
    return {
        'sensor_id': obj.sensor_id,
        'type': 'temperature',
        'temperature': obj.temperature,
        'humidity': obj.humidity,
        'pressure': obj.pressure,
        'time': obj.time.isoformat(),
    }


def home(request):
    latest_air_data = SensorDataAir.objects.order_by('-time').first()
    latest_indoor_data = SensorDataIndoor.objects.order_by('-time').first()
    latest_temp_sensor_1 = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time').first()
    latest_temp_sensor_2 = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time').first()

    initial_data = json.dumps({
        'outdoorSensor': _serialize_air(latest_air_data),
        'indoorSensor': _serialize_indoor(latest_indoor_data),
        'tempSensor1': _serialize_temp(latest_temp_sensor_1),
        'tempSensor2': _serialize_temp(latest_temp_sensor_2),
    })

    return render(request, 'home.html', {'initial_data': initial_data})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),  # Root path
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
