import django_timescaledb.models as timescale_models
from django.db import models


class Sensor(models.Model):
    type = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    comments = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'sensors'
        managed = False

    def __str__(self):
        return self.name


class SensorDataTemp(timescale_models.HypertableModel):
    time = models.DateTimeField(primary_key=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField()

    class Meta:
        db_table = 'sensor_data_temp'
        managed = False
        indexes = [
            models.Index(fields=['sensor', 'time'], name='idx_sensor_data_temp_sensor_id_time'),
        ]
        ordering = ['-time']


class SensorDataAir(timescale_models.HypertableModel):
    time = models.DateTimeField(primary_key=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField()
    p1 = models.FloatField()
    p2 = models.FloatField()

    class Meta:
        db_table = 'sensor_data_air'
        managed = False
        indexes = [
            models.Index(fields=['sensor', 'time'], name='idx_sensor_data_air_sensor_id_time'),
        ]
        ordering = ['-time']


class SensorDataIndoor(timescale_models.HypertableModel):
    time = models.DateTimeField(primary_key=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    status = models.IntegerField()
    aqi = models.IntegerField()
    tvoc = models.IntegerField()
    eco2 = models.IntegerField()

    class Meta:
        db_table = 'sensor_data_indoor'
        managed = False
        indexes = [
            models.Index(fields=['sensor', 'time'], name='idx_sensor_data_indoor_sensor_id_time'),
        ]
        ordering = ['-time']
