import json

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.views.generic.base import RedirectView

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


def latest_sensors(request):
    from django.http import JsonResponse
    latest_air = SensorDataAir.objects.order_by('-time').first()
    latest_indoor = SensorDataIndoor.objects.order_by('-time').first()
    latest_temp1 = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time').first()
    latest_temp2 = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time').first()
    return JsonResponse({
        'outdoorSensor': _serialize_air(latest_air),
        'indoorSensor': _serialize_indoor(latest_indoor),
        'tempSensor1': _serialize_temp(latest_temp1),
        'tempSensor2': _serialize_temp(latest_temp2),
    })


def _serialize_air_list(qs):
    return [_serialize_air(obj) for obj in list(qs)[::-1]]


def _serialize_indoor_list(qs):
    return [_serialize_indoor(obj) for obj in list(qs)[::-1]]


def _serialize_temp_list(qs):
    return [_serialize_temp(obj) for obj in list(qs)[::-1]]


def home(request):
    latest_air_data = SensorDataAir.objects.order_by('-time').first()
    latest_indoor_data = SensorDataIndoor.objects.order_by('-time').first()
    latest_temp_sensor_1 = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time').first()
    latest_temp_sensor_2 = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time').first()

    # Last 60 readings for charts
    air_history = SensorDataAir.objects.order_by('-time')[:60]
    indoor_history = SensorDataIndoor.objects.order_by('-time')[:60]
    temp1_history = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time')[:60]
    temp2_history = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time')[:60]

    initial_data = json.dumps({
        'outdoorSensor': _serialize_air(latest_air_data),
        'indoorSensor': _serialize_indoor(latest_indoor_data),
        'tempSensor1': _serialize_temp(latest_temp_sensor_1),
        'tempSensor2': _serialize_temp(latest_temp_sensor_2),
        'outdoorHistory': _serialize_air_list(air_history),
        'indoorHistory': _serialize_indoor_list(indoor_history),
        'temp1History': _serialize_temp_list(temp1_history),
        'temp2History': _serialize_temp_list(temp2_history),
    })

    import time as _time
    from django.conf import settings
    return render(request, 'home.html', {'initial_data': initial_data, 'cache_bust': int(_time.time()), 'version': settings.VERSION})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),
    path('api/sensors/latest/', latest_sensors, name='latest-sensors'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
