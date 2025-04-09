from django.db import models
from timescale.db.models.models import TimescaleModel


class Sensor(models.Model):
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sensors'

    def __str__(self):
        return self.name


class SensorDataTemp(TimescaleModel):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'sensor_data_temp'
        # ordering = ['-time']


class SensorDataAir(TimescaleModel):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    temperature = models.FloatField()
    humidity = models.FloatField()
    pressure = models.FloatField()
    p1 = models.FloatField()
    p2 = models.FloatField()
    signal = models.IntegerField()

    class Meta:
        db_table = 'sensor_data_air'


class SensorDataIndoor(TimescaleModel):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, db_column='sensor_id')
    status = models.IntegerField()
    aqi = models.IntegerField()
    tvoc = models.IntegerField()
    eco2 = models.IntegerField()

    class Meta:
        db_table = 'sensor_data_indoor'
