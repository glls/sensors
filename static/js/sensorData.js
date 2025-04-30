window.sensorData = function sensorData() {
    return {
        clientCount: 0,
        outdoorSensor: null,
        indoorSensor: null,
        tempSensor1: null,
        tempSensor2: null,
        weatherData: null,
        pollutionData: null,
        init() {
            const socket = new WebSocket('ws://' + window.location.host + '/ws/sensor_data/');
            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'air') {
                    this.outdoorSensor = this.formatSensorData(data);
                } else if (data.type === 'indoor') {
                    this.indoorSensor = this.formatSensorData(data);
                } else if (data.type === 'temperature' && data.sensor_id === 1) {
                    this.tempSensor1 = this.formatSensorData(data);
                } else if (data.type === 'temperature' && data.sensor_id === 2) {
                    this.tempSensor2 = this.formatSensorData(data);
                }
            };

            // Fetch weather data
            fetch('/api/weather/')
                .then(response => response.json())
                .then(data => {
                    this.weatherData = data;
                })
                .catch(error => console.error('Error fetching weather data:', error));

            // Fetch air pollution data
            fetch('/api/air-pollution/')
                .then(response => response.json())
                .then(data => {
                    this.pollutionData = data;
                })
                .catch(error => console.error('Error fetching air pollution data:', error));
        },
        formatSensorData(data) {
            data.time = this.formatTime(data.time);
            return data;
        },
        formatTime(time) {
            const sensorTime = new Date(time);
            return sensorTime.toLocaleDateString('en-GB', {
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                year: '2-digit',
            }) + ' ' + sensorTime.toLocaleTimeString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
            });
        }
    };
};