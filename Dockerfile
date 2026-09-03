FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

# Listening port. Override at runtime with -e APP_PORT=... (or APP_PORT in the
# k8s configmap, which must match the containerPort in deployment.yaml).
ENV APP_PORT=4040

EXPOSE ${APP_PORT}

# Shell form so ${APP_PORT} is expanded; exec keeps uvicorn as PID 1 so it still
# receives SIGTERM on pod shutdown.
CMD ["sh", "-c", "exec uvicorn sensors.asgi:application --host 0.0.0.0 --port ${APP_PORT} --lifespan=off"]
