from rest_framework import serializers

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = ['id', 'type', 'location', 'name', 'comments']
        read_only_fields = ['id']


class SensorDataTempSerializer(serializers.ModelSerializer):
    sensor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SensorDataTemp
        fields = ['time', 'sensor_id', 'temperature', 'humidity', 'pressure']

    def create(self, validated_data):
        sensor_id = validated_data.pop('sensor_id')
        try:
            sensor = Sensor.objects.get(id=sensor_id)
        except Sensor.DoesNotExist:
            raise serializers.ValidationError({"sensor_id": "Invalid sensor ID."})
        validated_data['sensor'] = sensor
        return SensorDataTemp.objects.create(**validated_data)


class SensorDataAirSerializer(serializers.ModelSerializer):
    sensor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SensorDataAir
        fields = ['time', 'sensor_id', 'temperature', 'humidity', 'pressure', 'p1', 'p2']

    def create(self, validated_data):
        sensor_id = validated_data.pop('sensor_id')
        try:
            sensor = Sensor.objects.get(id=sensor_id)
        except Sensor.DoesNotExist:
            raise serializers.ValidationError({"sensor_id": "Invalid sensor ID."})
        validated_data['sensor'] = sensor
        return SensorDataAir.objects.create(**validated_data)


class SensorDataIndoorSerializer(serializers.ModelSerializer):
    sensor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SensorDataIndoor
        fields = ['time', 'sensor_id', 'status', 'aqi', 'tvoc', 'eco2']

    def create(self, validated_data):
        sensor_id = validated_data.pop('sensor_id')
        try:
            sensor = Sensor.objects.get(id=sensor_id)
        except Sensor.DoesNotExist:
            raise serializers.ValidationError({"sensor_id": "Invalid sensor ID."})
        validated_data['sensor'] = sensor
        return SensorDataIndoor.objects.create(**validated_data)
