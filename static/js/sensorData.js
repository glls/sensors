window.sensorData = function sensorData() {
    const initial = window.INITIAL_SENSOR_DATA || {};

    return {
        wsConnected: false,
        outdoorSensor: null,
        indoorSensor: null,
        tempSensor1: null,
        tempSensor2: null,
        weatherData: null,
        pollutionData: null,

        init() {
            // Load initial data from server
            if (initial.outdoorSensor) this.outdoorSensor = this.formatSensorData(initial.outdoorSensor);
            if (initial.indoorSensor) this.indoorSensor = this.formatSensorData(initial.indoorSensor);
            if (initial.tempSensor1) this.tempSensor1 = this.formatSensorData(initial.tempSensor1);
            if (initial.tempSensor2) this.tempSensor2 = this.formatSensorData(initial.tempSensor2);

            this.connectWebSocket();
            this.fetchWeather();
            this.fetchPollution();

            // Refresh weather and pollution data every 10 minutes
            setInterval(() => {
                this.fetchWeather();
                this.fetchPollution();
            }, 10 * 60 * 1000);
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const socket = new WebSocket(protocol + '//' + window.location.host + '/ws/sensor_data/');

            socket.onopen = () => { this.wsConnected = true; };
            socket.onclose = () => {
                this.wsConnected = false;
                // Reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            socket.onerror = () => { this.wsConnected = false; };

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
        },

        fetchWeather() {
            fetch('/api/weather/')
                .then(r => r.json())
                .then(data => { this.weatherData = data; })
                .catch(err => console.error('Error fetching weather data:', err));
        },

        fetchPollution() {
            fetch('/api/air-pollution/')
                .then(r => r.json())
                .then(data => { this.pollutionData = data; })
                .catch(err => console.error('Error fetching air pollution data:', err));
        },

        formatSensorData(data) {
            return { ...data, time: this.formatTime(data.time) };
        },

        formatTime(time) {
            const d = new Date(time);
            return d.toLocaleDateString('en-GB', {
                weekday: 'short', day: '2-digit', month: '2-digit', year: '2-digit',
            }) + ' ' + d.toLocaleTimeString('en-GB', {
                hour: '2-digit', minute: '2-digit', hour12: false,
            });
        }
    };
};
