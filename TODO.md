# TODO

Tracker for the sensors app. Client-side tasks live in
[clients/README.md](clients/README.md).

## Pending

- [ ] **Guard `pollSensors()` against non-live ranges** -
  `static/js/sensorData.js:331`
  The 30s poll (`setInterval` at `sensorData.js:210`) appends live readings to
  the chart history regardless of the selected range. The WebSocket handler gets
  this right via `const liveCharts = this.selectedRange === 'live'`
  (`sensorData.js:285`), but the poll has no equivalent check - so while viewing
  1D/1W/1M/6M/1Y, raw readings pile onto the bucket-averaged series with
  mismatched `DD/MM` labels.
  Fix: bail out early, or gate only the `pushPoint`/`updateChart` calls if the
  value tiles should keep updating:
  ```js
  pollSensors() {
      if (this.selectedRange !== 'live') return;
      ...
  ```

- [ ] **Remove the dead scheduler code** - `api/views.py:148`,
  `core/utils/scheduler_control.py`
  `ToggleSchedulerAPIView` declares `global scheduler_enabled`
  (`api/views.py:150`), but `api/views.py` has no such module global and nothing
  reads it. The real flag lives in `core/utils/scheduler_control.py:7`, a
  different module - so `/api/scheduler/` reports
  `{"status": "Scheduler enabled"}` while changing nothing.
  `scheduler_control.py` is imported by nothing, starts a daemon thread at
  import time, and `import schedule` would fail anyway since `schedule` is not
  in `requirements.txt`.
  Fix: delete `core/utils/scheduler_control.py`, `ToggleSchedulerAPIView`, and
  the `scheduler/` route in `api/urls.py:23`. Reintroduce properly if a
  scheduler is ever actually needed.

- [ ] add user events

## Done

- [x] **Point Redis at the UNRAID server with its own db** - `sensors/settings.py`
  Default host moved from `localhost` to `192.168.33.5` and the channel layer
  pinned to db 1 (db 0 belongs to another app). Needed the
  `redis://host:port/db` URL form: the old `[(REDIS_HOST, 6379)]` tuple goes
  straight to `ConnectionPool(**kwargs)`, which has no `db` slot and always
  lands on db 0. Host, port and db are all env-configurable.

- [x] **Make the listening port configurable, default 4040** - `Dockerfile`,
  `k8s/`
  `APP_PORT` env var (`ENV APP_PORT=4040`) with a shell-form `CMD` using `exec`
  so uvicorn stays PID 1 and still receives SIGTERM. In k8s the port is named
  `http` so the probes and Service follow `containerPort` automatically.

- [x] **Document configuration and the standalone Docker workflow** -
  `README.md`, `clients/README.md`, `k8s/README.md`
  Env var reference, `docker build`/`docker run` instructions, Redis db
  rationale, a k8s ports table, and the previously undocumented client env vars.
