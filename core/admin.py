from django.contrib import admin
from .models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Sensor)
class SensorAdmin(ReadOnlyAdmin):
    list_display = ('name', 'type', 'location', 'comments')
    search_fields = ('name', 'location')

@admin.register(SensorDataTemp)
class SensorDataTempAdmin(ReadOnlyAdmin):
    list_display = ('time', 'sensor', 'temperature', 'humidity', 'pressure')
    list_filter = ('sensor',)
    date_hierarchy = 'time'

@admin.register(SensorDataAir)
class SensorDataAirAdmin(ReadOnlyAdmin):
    list_display = ('time', 'sensor', 'temperature', 'humidity', 'pressure', 'p1', 'p2')
    list_filter = ('sensor',)
    date_hierarchy = 'time'

@admin.register(SensorDataIndoor)
class SensorDataIndoorAdmin(ReadOnlyAdmin):
    list_display = ('time', 'sensor', 'status', 'aqi', 'tvoc', 'eco2')
    list_filter = ('sensor',)
    date_hierarchy = 'time'