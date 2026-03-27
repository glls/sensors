// Register zoom plugin - the UMD build exposes it as ChartZoom on window
if (typeof ChartZoom !== 'undefined') {
    Chart.register(ChartZoom);
} else if (typeof window['chartjs-plugin-zoom'] !== 'undefined') {
    Chart.register(window['chartjs-plugin-zoom']);
}

window.sensorData = function sensorData() {
    const initial = window.INITIAL_SENSOR_DATA || {};
    const MAX_HISTORY = 60;

    const COLORS = {
        orange: '#fb923c',
        blue: '#38bdf8',
        teal: '#2dd4bf',
        red: '#f87171',
        green: '#4ade80',
        purple: '#a78bfa',
    };

    // All non-reactive state lives here, outside Alpine's proxy
    const state = {
        lastTimes: { outdoor: null, indoor: null, temp1: null, temp2: null },
        history: {
            outdoor: { labels: [], datasets: {} },
            indoor: { labels: [], datasets: {} },
            temp1: { labels: [], datasets: {} },
            temp2: { labels: [], datasets: {} },
            weather: { labels: [], datasets: {} },
            pollution: { labels: [], datasets: {} },
        },
        charts: {},
    };

    function pushPoint(history, time, values) {
        const label = new Date(time).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
        history.labels.push(label);
        if (history.labels.length > MAX_HISTORY) history.labels.shift();

        for (const [key, val] of Object.entries(values)) {
            if (!history.datasets[key]) history.datasets[key] = [];
            history.datasets[key].push(val);
            if (history.datasets[key].length > MAX_HISTORY) history.datasets[key].shift();
        }
    }

    function buildChart(canvasId, history, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const datasets = config.lines.map(line => ({
            label: line.label,
            _key: line.key,
            data: history.datasets[line.key] || [],
            borderColor: line.color,
            backgroundColor: line.color + '20',
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.3,
            yAxisID: line.yAxis || 'y',
        }));

        const scales = {
            x: {
                ticks: { color: '#94a3b8', maxTicksLimit: 10 },
                grid: { color: 'rgba(71, 85, 105, 0.3)' },
            },
            y: {
                position: 'left',
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(71, 85, 105, 0.3)' },
            },
        };

        if (config.dualAxis) {
            scales.y1 = {
                position: 'right',
                ticks: { color: '#94a3b8' },
                grid: { drawOnChartArea: false },
            };
        }

        return new Chart(ctx, {
            type: 'line',
            data: { labels: history.labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                plugins: {
                    legend: {
                        labels: { color: '#f1f5f9', boxWidth: 12, padding: 10 },
                    },
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x',
                        },
                        zoom: {
                            wheel: { enabled: true, speed: 0.05 },
                            pinch: { enabled: true },
                            mode: 'x',
                        },
                        limits: {
                            x: { minRange: 5 },
                        },
                    },
                },
                scales,
            },
        });
    }

    function updateChart(chart, history) {
        if (!chart) return;
        chart.data.labels = [...history.labels];
        chart.data.datasets.forEach(ds => {
            ds.data = [...(history.datasets[ds._key] || [])];
        });
        chart.update('none');
    }

    function fmtLabel(isoTime, range) {
        const d = new Date(isoTime);
        return range === '1d'
            ? d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })
            : d.toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit' });
    }

    function buildHistory(rows, fields, range) {
        const h = { labels: [], datasets: {} };
        for (const row of rows) {
            h.labels.push(fmtLabel(row.time, range));
            for (const f of fields) {
                if (!h.datasets[f]) h.datasets[f] = [];
                h.datasets[f].push(row[f]);
            }
        }
        return h;
    }

    return {
        wsConnected: false,
        selectedRange: 'live',
        outdoorSensor: null,
        indoorSensor: null,
        tempSensor1: null,
        tempSensor2: null,
        weatherData: null,
        pollutionData: null,

        init() {
            // Load latest values
            if (initial.outdoorSensor) {
                this.outdoorSensor = this.formatSensorData(initial.outdoorSensor);
                state.lastTimes.outdoor = initial.outdoorSensor.time;
            }
            if (initial.indoorSensor) {
                this.indoorSensor = this.formatSensorData(initial.indoorSensor);
                state.lastTimes.indoor = initial.indoorSensor.time;
            }
            if (initial.tempSensor1) {
                this.tempSensor1 = this.formatSensorData(initial.tempSensor1);
                state.lastTimes.temp1 = initial.tempSensor1.time;
            }
            if (initial.tempSensor2) {
                this.tempSensor2 = this.formatSensorData(initial.tempSensor2);
                state.lastTimes.temp2 = initial.tempSensor2.time;
            }

            // Load chart history
            if (initial.outdoorHistory) {
                for (const d of initial.outdoorHistory) {
                    pushPoint(state.history.outdoor, d.time, {
                        pm10: d.pm10, pm25: d.pm25,
                        temperature: d.temperature, humidity: d.humidity, pressure: d.pressure,
                    });
                }
            }
            if (initial.indoorHistory) {
                for (const d of initial.indoorHistory) {
                    pushPoint(state.history.indoor, d.time, { aqi: d.aqi, tvoc: d.tvoc, eco2: d.eco2 });
                }
            }
            if (initial.temp1History) {
                for (const d of initial.temp1History) {
                    pushPoint(state.history.temp1, d.time, {
                        temperature: d.temperature, humidity: d.humidity, pressure: d.pressure,
                    });
                }
            }
            if (initial.temp2History) {
                for (const d of initial.temp2History) {
                    pushPoint(state.history.temp2, d.time, {
                        temperature: d.temperature, humidity: d.humidity, pressure: d.pressure,
                    });
                }
            }

            this.connectWebSocket();
            this.fetchWeather();
            this.fetchPollution();
            this.pollSensors();

            setInterval(() => {
                this.fetchWeather();
                this.fetchPollution();
            }, 10 * 60 * 1000);

            setInterval(() => this.pollSensors(), 30 * 1000);

            this.$nextTick(() => this.initCharts());
        },

        initCharts() {
            state.charts.outdoor = buildChart('outdoorChart', state.history.outdoor, {
                dualAxis: true,
                lines: [
                    { key: 'pm10', label: 'PM10', color: COLORS.red },
                    { key: 'pm25', label: 'PM2.5', color: COLORS.orange },
                    { key: 'temperature', label: 'Temp', color: COLORS.teal },
                    { key: 'humidity', label: 'Humidity', color: COLORS.blue },
                    { key: 'pressure', label: 'Pressure', color: COLORS.green, yAxis: 'y1' },
                ],
            });

            state.charts.indoor = buildChart('indoorChart', state.history.indoor, {
                dualAxis: true,
                lines: [
                    { key: 'tvoc', label: 'TVOC', color: COLORS.purple },
                    { key: 'eco2', label: 'eCO2', color: COLORS.teal, yAxis: 'y1' },
                ],
            });

            state.charts.temp1 = buildChart('temp1Chart', state.history.temp1, {
                dualAxis: true,
                lines: [
                    { key: 'temperature', label: 'Temp', color: COLORS.orange },
                    { key: 'humidity', label: 'Humidity', color: COLORS.blue },
                    { key: 'pressure', label: 'Pressure', color: COLORS.teal, yAxis: 'y1' },
                ],
            });

            state.charts.temp2 = buildChart('temp2Chart', state.history.temp2, {
                dualAxis: false,
                lines: [
                    { key: 'temperature', label: 'Temp', color: COLORS.orange },
                    { key: 'humidity', label: 'Humidity', color: COLORS.blue },
                ],
            });

            state.charts.weather = buildChart('weatherChart', state.history.weather, {
                dualAxis: true,
                lines: [
                    { key: 'temperature', label: 'Temp', color: COLORS.orange },
                    { key: 'humidity', label: 'Humidity', color: COLORS.blue },
                    { key: 'pressure', label: 'Pressure', color: COLORS.teal, yAxis: 'y1' },
                ],
            });

            state.charts.pollution = buildChart('pollutionChart', state.history.pollution, {
                dualAxis: false,
                lines: [
                    { key: 'pm2_5', label: 'PM2.5', color: COLORS.orange },
                    { key: 'pm10', label: 'PM10', color: COLORS.red },
                    { key: 'co', label: 'CO', color: COLORS.teal },
                    { key: 'no2', label: 'NO2', color: COLORS.purple },
                ],
            });
        },

        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const socket = new WebSocket(protocol + '//' + window.location.host + '/ws/sensor_data/');

            socket.onopen = () => { this.wsConnected = true; };
            socket.onclose = () => {
                this.wsConnected = false;
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            socket.onerror = () => { this.wsConnected = false; };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const liveCharts = this.selectedRange === 'live';

                if (data.type === 'air') {
                    this.outdoorSensor = this.formatSensorData(data);
                    state.lastTimes.outdoor = data.time;
                    if (liveCharts) {
                        pushPoint(state.history.outdoor, data.time, {
                            pm10: data.pm10, pm25: data.pm25,
                            temperature: data.temperature, humidity: data.humidity,
                            pressure: data.pressure,
                        });
                        updateChart(state.charts.outdoor, state.history.outdoor);
                    }
                } else if (data.type === 'indoor') {
                    this.indoorSensor = this.formatSensorData(data);
                    state.lastTimes.indoor = data.time;
                    if (liveCharts) {
                        pushPoint(state.history.indoor, data.time, {
                            aqi: data.aqi, tvoc: data.tvoc, eco2: data.eco2,
                        });
                        updateChart(state.charts.indoor, state.history.indoor);
                    }
                } else if (data.type === 'temperature' && data.sensor_id === 1) {
                    this.tempSensor1 = this.formatSensorData(data);
                    state.lastTimes.temp1 = data.time;
                    if (liveCharts) {
                        pushPoint(state.history.temp1, data.time, {
                            temperature: data.temperature, humidity: data.humidity,
                            pressure: data.pressure,
                        });
                        updateChart(state.charts.temp1, state.history.temp1);
                    }
                } else if (data.type === 'temperature' && data.sensor_id === 2) {
                    this.tempSensor2 = this.formatSensorData(data);
                    state.lastTimes.temp2 = data.time;
                    if (liveCharts) {
                        pushPoint(state.history.temp2, data.time, {
                            temperature: data.temperature, humidity: data.humidity,
                            pressure: data.pressure,
                        });
                        updateChart(state.charts.temp2, state.history.temp2);
                    }
                }
            };
        },

        pollSensors() {
            console.log('[poll] Fetching...');
            fetch('/api/sensors/latest/')
                .then(r => r.json())
                .then(data => {
                    console.log('[poll] OK');
                    if (data.outdoorSensor) {
                        const d = data.outdoorSensor;
                        if (state.lastTimes.outdoor !== d.time) {
                            state.lastTimes.outdoor = d.time;
                            this.outdoorSensor = this.formatSensorData(d);
                            pushPoint(state.history.outdoor, d.time, {
                                pm10: d.pm10, pm25: d.pm25,
                                temperature: d.temperature, humidity: d.humidity,
                                pressure: d.pressure,
                            });
                            updateChart(state.charts.outdoor, state.history.outdoor);
                        }
                    }
                    if (data.indoorSensor) {
                        const d = data.indoorSensor;
                        if (state.lastTimes.indoor !== d.time) {
                            state.lastTimes.indoor = d.time;
                            this.indoorSensor = this.formatSensorData(d);
                            pushPoint(state.history.indoor, d.time, {
                                aqi: d.aqi, tvoc: d.tvoc, eco2: d.eco2,
                            });
                            updateChart(state.charts.indoor, state.history.indoor);
                        }
                    }
                    if (data.tempSensor1) {
                        const d = data.tempSensor1;
                        if (state.lastTimes.temp1 !== d.time) {
                            state.lastTimes.temp1 = d.time;
                            this.tempSensor1 = this.formatSensorData(d);
                            pushPoint(state.history.temp1, d.time, {
                                temperature: d.temperature, humidity: d.humidity,
                                pressure: d.pressure,
                            });
                            updateChart(state.charts.temp1, state.history.temp1);
                        }
                    }
                    if (data.tempSensor2) {
                        const d = data.tempSensor2;
                        if (state.lastTimes.temp2 !== d.time) {
                            state.lastTimes.temp2 = d.time;
                            this.tempSensor2 = this.formatSensorData(d);
                            pushPoint(state.history.temp2, d.time, {
                                temperature: d.temperature, humidity: d.humidity,
                                pressure: d.pressure,
                            });
                            updateChart(state.charts.temp2, state.history.temp2);
                        }
                    }
                })
                .catch(err => console.error('[poll] Error:', err));
        },

        fetchWeather() {
            fetch('/api/weather/')
                .then(r => r.json())
                .then(data => {
                    this.weatherData = data;
                    if (data && !data.error) {
                        pushPoint(state.history.weather, new Date().toISOString(), {
                            temperature: data.main.temp,
                            humidity: data.main.humidity,
                            pressure: data.main.pressure,
                        });
                        updateChart(state.charts.weather, state.history.weather);
                    }
                })
                .catch(err => console.error('Error fetching weather data:', err));
        },

        fetchPollution() {
            fetch('/api/air-pollution/')
                .then(r => r.json())
                .then(data => {
                    this.pollutionData = data;
                    if (data && !data.error) {
                        const c = data.list[0].components;
                        pushPoint(state.history.pollution, new Date().toISOString(), {
                            pm2_5: c.pm2_5, pm10: c.pm10, co: c.co, no2: c.no2,
                        });
                        updateChart(state.charts.pollution, state.history.pollution);
                    }
                })
                .catch(err => console.error('Error fetching air pollution data:', err));
        },

        async changeRange(range) {
            this.selectedRange = range;
            if (range === 'live') {
                window.location.reload();
                return;
            }

            const [outdoor, indoor, temp1, temp2] = await Promise.all([
                fetch(`/api/history/?sensor=outdoor&range=${range}`).then(r => r.json()),
                fetch(`/api/history/?sensor=indoor&range=${range}`).then(r => r.json()),
                fetch(`/api/history/?sensor=temp1&range=${range}`).then(r => r.json()),
                fetch(`/api/history/?sensor=temp2&range=${range}`).then(r => r.json()),
            ]);

            state.history.outdoor = buildHistory(outdoor, ['pm10', 'pm25', 'temperature', 'humidity', 'pressure'], range);
            state.history.indoor  = buildHistory(indoor,  ['aqi', 'tvoc', 'eco2'], range);
            state.history.temp1   = buildHistory(temp1,   ['temperature', 'humidity', 'pressure'], range);
            state.history.temp2   = buildHistory(temp2,   ['temperature', 'humidity', 'pressure'], range);

            updateChart(state.charts.outdoor, state.history.outdoor);
            updateChart(state.charts.indoor,  state.history.indoor);
            updateChart(state.charts.temp1,   state.history.temp1);
            updateChart(state.charts.temp2,   state.history.temp2);
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
