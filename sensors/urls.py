"""
URL configuration for sensors project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include

from api.consumers import SensorDataConsumer
from core.models import SensorDataAir, SensorDataIndoor, SensorDataTemp


def home(request):
    latest_air_data = SensorDataAir.objects.order_by('-time').first()
    client_count = len(SensorDataConsumer.connected_clients)

    # Fetch latest indoor data from the ens160 sensor
    latest_indoor_data = SensorDataIndoor.objects.order_by('-time').first()
    print(latest_indoor_data)


    # Fetch latest temperature data from sensors 1 and 2
    latest_temp_sensor_1 = SensorDataTemp.objects.filter(sensor_id=1).order_by('-time').first()
    latest_temp_sensor_2 = SensorDataTemp.objects.filter(sensor_id=2).order_by('-time').first()

    context = {
        'latest_air_data': latest_air_data,
        'latest_indoor_data': latest_indoor_data,
        'latest_temp_sensor_1': latest_temp_sensor_1,
        'latest_temp_sensor_2': latest_temp_sensor_2,
        'client_count': client_count
    }
    return render(request, 'home.html', context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', home, name='home'),  # Root path

]
