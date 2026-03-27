# Sensors - k3s Deployment

Local ARM64 deployment on two Raspberry Pi 4 nodes running k3s.

---

## Cluster setup

| Node | Role | OS | Docker | kubectl |
|------|------|----|--------|---------|
| `GL-pi4-ap.local` (192.168.33.50) | k3s server (master) | DietPi v10.2.3 / Debian 13 | no | yes |
| `gl-rpi4tv.local` (192.168.33.33) | k3s agent (worker) | DietPi / Debian 12 (bookworm) | yes - build node | no |
| Pi 500 (workstation) | - | Debian 13 (trixie) | no | yes |

k3s version: **v1.34.5+k3s1**

- Build images on `gl-rpi4tv.local` (has Docker)
- Run `kubectl` from Pi 500, Windows workstation, or directly on `GL-pi4-ap.local`
- Both nodes on 1G ethernet, SSDs via USB
- External services on `192.168.33.5`: TimescaleDB (5432), Redis (6379)
- Local image registry on `gl-rpi4tv.local`: `192.168.33.33:5000`
- App accessible at: http://sensors.192.168.33.50.nip.io

Label the worker so it shows correctly:
```sh
kubectl label node gl-rpi4tv node-role.kubernetes.io/worker=worker
kubectl get nodes
```

---

## Requirements

### kubectl

Install matching the cluster version exactly. Works on Linux ARM64, Windows, or any workstation:
```sh
# Linux ARM64 (Pi 500):
curl -LO "https://dl.k8s.io/release/v1.34.5/bin/linux/arm64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Windows: download from https://dl.k8s.io/release/v1.34.5/bin/windows/amd64/kubectl.exe

kubectl version --client
```

### kubeconfig

k3s writes its kubeconfig to `/etc/rancher/k3s/k3s.yaml` on the master.

**Allow non-root access on the master** (do this once):
```sh
# On GL-pi4-ap.local:
echo 'write-kubeconfig-mode: "0644"' | sudo tee /etc/rancher/k3s/config.yaml
sudo systemctl restart k3s
```

**Copy to your workstation** (GL-pi4-ap uses Dropbear - use ssh+cat, not scp):
```sh
mkdir -p ~/.kube
ssh gl@GL-pi4-ap.local "cat /etc/rancher/k3s/k3s.yaml" > ~/.kube/config

# Fix the server address (k3s writes 127.0.0.1 inside the file):
sed -i 's/127.0.0.1/192.168.33.50/g' ~/.kube/config

kubectl get nodes   # both nodes should appear as Ready
```

---

## Key concept: k3s uses containerd, not Docker

k3s bundles **containerd** as its container runtime - Docker's image store is
separate and invisible to k3s. Images built with `docker build` must either be
imported into containerd or pulled from a registry.

With a local registry (our setup), the flow is:
```
docker build + push → local registry (192.168.33.33:5000)
                              ↓ pulled automatically by k3s on any node
                       containerd on gl-pi4-ap + gl-rpi4tv
```

---

## External services (192.168.33.5)

The app depends on two external services running outside the cluster:

| Service | Host | Port |
|---------|------|------|
| TimescaleDB | 192.168.33.5 | 5432 |
| Redis | 192.168.33.5 | 6379 |

Redis is used as the Django Channels layer - required for WebSockets to work
correctly across multiple replicas. Without it each pod has its own isolated
memory and WebSocket connections break when load balanced across pods.

---

## Local registry setup (gl-rpi4tv.local)

Run once to set up the registry:

```sh
# On gl-rpi4tv.local - start the registry container:
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# Tell Docker this registry is plain HTTP (not HTTPS):
sudo tee /etc/docker/daemon.json <<EOF
{
  "insecure-registries": ["192.168.33.33:5000"]
}
EOF
sudo systemctl restart docker
```

Configure k3s to trust it on **each node**:
```sh
sudo mkdir -p /etc/rancher/k3s
sudo tee /etc/rancher/k3s/registries.yaml <<EOF
mirrors:
  "192.168.33.33:5000":
    endpoint:
      - "http://192.168.33.33:5000"
EOF
sudo systemctl restart k3s-agent   # worker node
sudo systemctl restart k3s         # master node
```

---

## Step 1 - Clone and build

On `gl-rpi4tv.local`:
```sh
git clone git@github.com:glls/sensors.git
cd sensors
docker build -t sensors:latest .
docker tag sensors:latest 192.168.33.33:5000/sensors:latest
docker push 192.168.33.33:5000/sensors:latest
```

---

## Step 2 - Apply manifests

`kubectl apply` is declarative - you describe the desired state and it figures
out what needs to change. Run it multiple times safely; it will report:
- `created` - resource is new
- `configured` - resource existed but was updated
- `unchanged` - resource already matches the file, nothing to do

`kubectl apply -f k8s/` applies files in alphabetical order. The namespace must
exist before any other resource can be created inside it, so it is prefixed
`00-` to guarantee it sorts first.

From the project root (any workstation with kubectl):
```sh
kubectl apply -f k8s/
```

---

## Step 3 - Verify and debug

```sh
# Overview of everything in the namespace
kubectl -n sensors get all

# Watch pods come up (Pending → ContainerCreating → Running)
kubectl -n sensors get pods -w

# See which node each pod is on
kubectl -n sensors get pods -o wide

# Detailed events for a pod - first place to look when something is wrong
kubectl -n sensors describe pod <pod-name>

# Stream app logs with timestamps (like docker logs -f)
kubectl -n sensors logs -f deploy/sensors --timestamps

# Shell into the running container (like docker exec -it)
kubectl -n sensors exec -it deploy/sensors -- /bin/sh

# Resource usage
kubectl top pods -n sensors
kubectl top nodes
```

---

## Step 4 - Access the app

Traefik runs on the master node and is the single entry point for all traffic.
Both pods (on either node) are reachable through it.

```
Browser → 192.168.33.50 (Traefik on master)
               ↓ load balances across
    pod on gl-pi4-ap AND/OR pod on gl-rpi4tv
```

App URL: http://sensors.192.168.33.50.nip.io

nip.io is a public wildcard DNS - `anything.192.168.33.50.nip.io` resolves to
`192.168.33.50`. No /etc/hosts needed. Requires internet for DNS resolution.

> **Fritz.box note:** Fritz.box DNS rebind protection blocks nip.io by default.
> Fix: `fritz.box -> Home Network -> Network -> DNS Rebind Protection -> add nip.io`

---

## Scaling

```sh
# Scale to 2 replicas - pods land on both nodes
kubectl -n sensors scale deployment/sensors --replicas=2
kubectl -n sensors get pods -o wide -w

# Scale back to 1
kubectl -n sensors scale deployment/sensors --replicas=1
```

With Redis channel layer, WebSockets work correctly across multiple replicas -
any pod can handle any WebSocket connection since state is shared via Redis.

---

## Redeploy after code changes

On `gl-rpi4tv.local`:
```sh
git pull
docker build -t sensors:latest .
docker tag sensors:latest 192.168.33.33:5000/sensors:latest
docker push 192.168.33.33:5000/sensors:latest
```

From workstation:
```sh
kubectl -n sensors rollout restart deployment/sensors
kubectl -n sensors rollout status deployment/sensors
```

---

## Teardown

```sh
# Remove everything in the namespace at once
kubectl delete namespace sensors

# Or remove individual resources
kubectl delete -f k8s/
```

---

## Known issues & fixes

### WebSockets not working - uvicorn[standard] required

**Symptom:** HTTP works, WebSocket connections refused. Pod logs show:
```
WARNING: No supported WebSocket library detected.
WARNING: Unsupported upgrade request.
```

**Cause:** `uvicorn` alone is a minimal install - HTTP only. WebSocket support
requires the `[standard]` extras which adds the `websockets` library, plus
`uvloop` (faster event loop) and `httptools` (faster HTTP parsing).
Dev environments often have these installed globally, masking the missing dep.

**Fix:** Use `uvicorn[standard]` in `requirements.txt`:
```
uvicorn[standard]~=0.34.0
```

---

### WebSockets break with multiple replicas - use Redis channel layer

**Symptom:** WebSocket connections drop or don't receive updates when scaled
to 2+ replicas. HTTP works fine.

**Cause:** `InMemoryChannelLayer` is per-process. Each pod has its own isolated
memory - a WebSocket connected to pod A cannot receive messages sent via pod B.
Traefik load balances requests across pods, so connections land on different pods.

**Fix:** Use `channels_redis` so all pods share state via a central Redis instance:

`requirements.txt`:
```
channels-redis~=4.2.0
```

`settings.py`:
```python
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, 6379)],
        },
    },
}
```

`configmap.yaml`:
```yaml
REDIS_HOST: "192.168.33.5"
```

---

### gl-rpi4tv: SSD USB I/O errors on boot

**Symptom:** I/O errors on `sda`, k3s-agent fails to start after reboot.

**Cause:** JMicron JMS578 USB-SATA bridge (idVendor=152d, idProduct=0578) uses
the UAS driver by default, which is unstable on RPi4 under boot-time I/O load.

**Fix 1 - Disable UAS for this device** (append to the single line in `/boot/firmware/cmdline.txt`):
```
usb-storage.quirks=152d:0578:u
```

**Fix 2 - Raise USB port current** (new line in `/boot/firmware/config.txt`):
```
max_usb_current=1
```

Verify after reboot:
```sh
dmesg | grep -i "152d\|uas\|jmicron"
# Expected: "UAS is ignored for this device, using usb-storage instead"
```

---

### nip.io not resolving - Fritz.box DNS rebind protection

**Symptom:** `dig sensors.192.168.33.50.nip.io` returns `ANSWER: 0`.
Works fine when queried directly against `8.8.8.8`.

**Cause:** Fritz.box drops DNS responses where a public domain resolves to a
private IP (192.168.x.x) - DNS rebind protection.

**Fix 1 - Whitelist nip.io in Fritz.box** (recommended, fixes for whole network):
```
fritz.box -> Home Network -> Network -> DNS Rebind Protection
-> add "nip.io" to exceptions
```

**Fix 2 - Bypass Fritz.box DNS on the client machine:**
```sh
sudo nmcli con mod "$(nmcli -t -f NAME con show --active | head -1)" ipv4.dns "8.8.8.8"
sudo nmcli con up "$(nmcli -t -f NAME con show --active | head -1)"
```

---

## Secrets note

`secret.yaml` stores credentials in plaintext - fine for local learning.
For production use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
or [External Secrets Operator](https://external-secrets.io).
