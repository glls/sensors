# Sensors — k3s Deployment

Local ARM64 deployment on two Raspberry Pi 4 nodes running k3s.

---

## Requirements

### Cluster nodes (DietPi / Debian 13, k3s v1.34.5+k3s1)

| Node | Role | Has Docker |
|------|------|-----------|
| `GL-pi4-ap.local` | k3s server (master) | no |
| `gl-rpi4tv.local` | k3s agent (worker) | yes — build node |

k3s bundles containerd — that's all a node needs to **run** containers.
Docker only lives on the worker because that's where we build images.

Verify from the master:
```sh
sudo k3s kubectl get nodes   # both nodes should appear as Ready
```

### Fixing k3s-agent not starting on reboot (gl-rpi4tv.local)

The agent starts before the network is ready — a systemd race condition common
on headless DietPi. Fix it by overriding the unit to wait for the network:

```sh
# On gl-rpi4tv.local:
sudo systemctl edit k3s-agent
```

Add these lines in the editor:
```ini
[Unit]
After=network-online.target
Wants=network-online.target
```

Then reload and enable:
```sh
sudo systemctl daemon-reload
sudo systemctl enable k3s-agent
sudo reboot
```

After reboot, confirm:
```sh
sudo systemctl status k3s-agent
```

### On your workstation (where you run kubectl from)

| Tool | Purpose | Install |
|------|---------|---------|
| **kubectl** | Talk to the cluster | `sudo apt install kubectl` or via [k3s kubeconfig](#kubeconfig) |

#### kubeconfig

k3s writes its kubeconfig to `/etc/rancher/k3s/k3s.yaml` on the server node.
Copy it to your workstation so `kubectl` knows where the cluster is:

```sh
# On your workstation:
mkdir -p ~/.kube
scp pi@<server-node-ip>:/etc/rancher/k3s/k3s.yaml ~/.kube/config

# Fix the server address (k3s defaults to 127.0.0.1 inside the file):
sed -i 's/127.0.0.1/<server-node-ip>/g' ~/.kube/config

# Confirm it works:
kubectl get nodes
```

---

## Key concept: k3s uses containerd, not Docker

k3s bundles **containerd** as its container runtime — Docker's image store is
separate and invisible to k3s. Images you build with `docker build` must be
explicitly imported into containerd before k3s can use them.

```
docker build → Docker store   (k3s can't see this)
                     ↓ docker save | k3s ctr images import -
              containerd store (k3s uses this)
```

---

## Step 1 — Build the image

Run this on the RPi node where the pod will land, from the project root:

```sh
docker build -t sensors:latest .
```

Verify:
```sh
docker images | grep sensors
```

---

## Step 2 — Import into k3s

```sh
docker save sensors:latest | sudo k3s ctr images import -
```

`docker save` streams the image as a tar to stdout.
`k3s ctr images import -` reads from stdin into containerd.

Verify containerd can see it:
```sh
sudo k3s ctr images ls | grep sensors
# expect: docker.io/library/sensors:latest
```

> **Two-node note:** k3s schedules pods on either node automatically.
> Import the image on **both** nodes to avoid `ImagePullBackOff` errors,
> or set up a [local registry](#optional-local-registry) so both nodes
> pull from a central place.

---

## Step 3 — Apply manifests

Apply in this order (dependencies first):

```sh
kubectl apply -f k8s/namespace.yaml    # create the 'sensors' namespace
kubectl apply -f k8s/secret.yaml       # DB password, Django secret key
kubectl apply -f k8s/configmap.yaml    # DB host, port, name, user, TZ
kubectl apply -f k8s/deployment.yaml   # the actual app pod
kubectl apply -f k8s/service.yaml      # internal stable address for the pod
kubectl apply -f k8s/ingress.yaml      # expose via Traefik at sensors.local
```

Or all at once (k8s handles dependency order internally):
```sh
kubectl apply -f k8s/
```

---

## Step 4 — Verify and debug

```sh
# Overview of everything in the namespace
kubectl -n sensors get all

# Watch pods come up (Pending → ContainerCreating → Running)
kubectl -n sensors get pods -w

# Detailed events for a pod — first place to look when something is wrong
kubectl -n sensors describe pod <pod-name>

# Stream app logs (like docker logs -f)
kubectl -n sensors logs -f deploy/sensors

# Shell into the running container (like docker exec -it)
kubectl -n sensors exec -it deploy/sensors -- /bin/sh

# Check the ingress got an address
kubectl -n sensors get ingress
```

---

## Step 5 — Access the app

Find your server node IP:
```sh
kubectl get nodes -o wide
```

Add to `/etc/hosts` on the machine you browse from:
```
192.168.x.x  sensors.local
```

Open http://sensors.local

WebSockets (`ws://sensors.local/ws/...`) work out of the box — Traefik
handles the HTTP upgrade automatically.

---

## Redeploy after code changes

```sh
# 1. Rebuild
docker build -t sensors:latest .

# 2. Re-import into containerd (repeat on both nodes if needed)
docker save sensors:latest | sudo k3s ctr images import -

# 3. Trigger a rolling restart
kubectl -n sensors rollout restart deployment/sensors

# 4. Watch it roll out
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

## Optional: local registry

Running a registry on your LAN means both nodes pull images automatically
without manual import steps — better workflow for multi-node setups.

```sh
# On one node (or a separate machine):
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# Build and push:
docker build -t 192.168.x.x:5000/sensors:latest .
docker push 192.168.x.x:5000/sensors:latest
```

Then in `deployment.yaml` update:
```yaml
image: 192.168.x.x:5000/sensors:latest
imagePullPolicy: Always
```

k3s needs to trust the insecure (HTTP) registry. Create on **each node**:
```sh
sudo mkdir -p /etc/rancher/k3s
sudo tee /etc/rancher/k3s/registries.yaml <<EOF
mirrors:
  "192.168.x.x:5000":
    endpoint:
      - "http://192.168.x.x:5000"
EOF
sudo systemctl restart k3s        # server node
sudo systemctl restart k3s-agent  # worker nodes
```

---

## Secrets note

`secret.yaml` stores credentials in plaintext — fine for local learning.
For production use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
or [External Secrets Operator](https://external-secrets.io).
