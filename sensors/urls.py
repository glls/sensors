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


def history_data(request):
    from django.http import JsonResponse
    from django.db import connection

    sensor = request.GET.get('sensor', 'outdoor')
    range_param = request.GET.get('range', '1d')

    ranges = {
        '1d': ('1 day',    '1 hour'),
        '1w': ('7 days',   '6 hours'),
        '1m': ('30 days',  '1 day'),
        '6m': ('180 days', '1 week'),
        '1y': ('365 days', '2 weeks'),
    }

    if range_param not in ranges:
        return JsonResponse({'error': 'invalid range'}, status=400)

    interval, bucket = ranges[range_param]

    with connection.cursor() as cursor:
        if sensor == 'outdoor':
            cursor.execute(f"""
                SELECT time_bucket('{bucket}', time) AS b,
                       AVG(temperature), AVG(humidity), AVG(pressure), AVG(p1), AVG(p2)
                FROM sensor_data_air
                WHERE time >= NOW() - INTERVAL '{interval}'
                GROUP BY b ORDER BY b
            """)
            return JsonResponse([{
                'time':        row[0].isoformat(),
                'type':        'air',
                'temperature': round(row[1], 2) if row[1] is not None else None,
                'humidity':    round(row[2], 2) if row[2] is not None else None,
                'pressure':    round(row[3], 2) if row[3] is not None else None,
                'pm10':        round(row[4], 2) if row[4] is not None else None,
                'pm25':        round(row[5], 2) if row[5] is not None else None,
            } for row in cursor.fetchall()], safe=False)

        if sensor == 'indoor':
            cursor.execute(f"""
                SELECT time_bucket('{bucket}', time) AS b,
                       AVG(aqi), AVG(tvoc), AVG(eco2)
                FROM sensor_data_indoor
                WHERE time >= NOW() - INTERVAL '{interval}'
                GROUP BY b ORDER BY b
            """)
            return JsonResponse([{
                'time': row[0].isoformat(),
                'type': 'indoor',
                'aqi':  round(row[1], 1) if row[1] is not None else None,
                'tvoc': round(row[2], 1) if row[2] is not None else None,
                'eco2': round(row[3], 1) if row[3] is not None else None,
            } for row in cursor.fetchall()], safe=False)

        if sensor in ('temp1', 'temp2'):
            sensor_id = 1 if sensor == 'temp1' else 2
            cursor.execute(f"""
                SELECT time_bucket('{bucket}', time) AS b,
                       AVG(temperature), AVG(humidity), AVG(pressure)
                FROM sensor_data_temp
                WHERE time >= NOW() - INTERVAL '{interval}'
                AND sensor_id = %s
                GROUP BY b ORDER BY b
            """, [sensor_id])
            return JsonResponse([{
                'time':        row[0].isoformat(),
                'type':        'temperature',
                'temperature': round(row[1], 2) if row[1] is not None else None,
                'humidity':    round(row[2], 2) if row[2] is not None else None,
                'pressure':    round(row[3], 2) if row[3] is not None else None,
            } for row in cursor.fetchall()], safe=False)

    return JsonResponse({'error': 'invalid sensor'}, status=400)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),
    path('api/sensors/latest/', latest_sensors, name='latest-sensors'),
    path('api/history/', history_data, name='history-data'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
