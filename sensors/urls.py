from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include

from core.models import SensorDataAir, SensorDataIndoor, SensorDataTemp

def home(request):
    # add sensor names, load values on startup
    latest_air_data = SensorDataAir.objects.order_by('-time').first()
    # Fetch latest indoor data from the ens160 sensor
    latest_indoor_data = SensorDataIndoor.objects.order_by('-time').first()
    # Fetch latest temperature data from sensors 1 and 2
    latest_temp_sensor_1 = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time').first()
    latest_temp_sensor_2 = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time').first()

    context = {
        'latest_air_data': latest_air_data,
        'latest_indoor_data': latest_indoor_data,
        'latest_temp_sensor_1': latest_temp_sensor_1,
        'latest_temp_sensor_2': latest_temp_sensor_2,
    }
    return render(request, 'home.html', context)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),  # Root path
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
