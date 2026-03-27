# Sensors - k3s Deployment

Local ARM64 deployment on two Raspberry Pi 4 nodes running k3s.

---

## Cluster setup

| Node | Role | OS | Docker | kubectl |
|------|------|----|--------|---------|
| `GL-pi4-ap.local` | k3s server (master) | DietPi v10.2.3 / Debian 13 | no | yes |
| `gl-rpi4tv.local` | k3s agent (worker) | DietPi / Debian 12 (bookworm) | yes - build node | no |
| Pi 500 (workstation) | - | Debian 13 (trixie) | no | yes |

k3s version: **v1.34.5+k3s1**

- Build images on `gl-rpi4tv.local` (has Docker)
- Run `kubectl` from Pi 500 or directly on `GL-pi4-ap.local`
- Both nodes on 1G ethernet, SSDs via USB

Label the worker so it shows correctly:
```sh
kubectl label node gl-rpi4tv node-role.kubernetes.io/worker=worker
kubectl get nodes
```

---

## Requirements

### kubectl (Pi 500 workstation)

Install matching the cluster version exactly:
```sh
curl -LO "https://dl.k8s.io/release/v1.34.5/bin/linux/arm64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/
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
sed -i 's/127.0.0.1/<GL-pi4-ap-IP>/g' ~/.kube/config

kubectl get nodes   # both nodes should appear as Ready
```

---

## Known issues & fixes

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

## Key concept: k3s uses containerd, not Docker

k3s bundles **containerd** as its container runtime - Docker's image store is
separate and invisible to k3s. Images built with `docker build` must be
explicitly imported into containerd before k3s can use them.

```
docker build → Docker store   (k3s can't see this)
                     ↓ docker save | k3s ctr images import -
              containerd store (k3s uses this)
```

---

## Step 1 - Clone and build

On `gl-rpi4tv.local`:
```sh
git clone git@github.com:glls/sensors.git
cd sensors
docker build -t sensors:latest .
docker images | grep sensors
```

---

## Step 2 - Import into k3s

On `gl-rpi4tv.local`:
```sh
docker save sensors:latest | sudo k3s ctr images import -
```

Verify containerd can see it:
```sh
sudo k3s ctr images ls | grep sensors
# expect: docker.io/library/sensors:latest
```

> **Two-node note:** k3s schedules pods on either node automatically.
> Import the image on **both** nodes to avoid `ImagePullBackOff` errors,
> or set up a [local registry](#optional-local-registry).

If building on a separate machine, pipe directly over SSH:
```sh
docker save sensors:latest | ssh gl@gl-rpi4tv.local "sudo k3s ctr images import -"
```

---

## Step 3 - Apply manifests

From the project root (Pi 500 or master):
```sh
kubectl apply -f k8s/namespace.yaml    # create the 'sensors' namespace
kubectl apply -f k8s/secret.yaml       # DB password, Django secret key
kubectl apply -f k8s/configmap.yaml    # DB host, port, name, user, TZ
kubectl apply -f k8s/deployment.yaml   # the actual app pod
kubectl apply -f k8s/service.yaml      # internal stable address for the pod
kubectl apply -f k8s/ingress.yaml      # expose via Traefik at sensors.local
```

Or all at once:
```sh
kubectl apply -f k8s/
```

---

## Step 4 - Verify and debug

```sh
# Overview of everything in the namespace
kubectl -n sensors get all

# Watch pods come up (Pending → ContainerCreating → Running)
kubectl -n sensors get pods -w

# Detailed events for a pod - first place to look when something is wrong
kubectl -n sensors describe pod <pod-name>

# Stream app logs (like docker logs -f)
kubectl -n sensors logs -f deploy/sensors

# Shell into the running container (like docker exec -it)
kubectl -n sensors exec -it deploy/sensors -- /bin/sh

# Check the ingress got an address
kubectl -n sensors get ingress
```

---

## Step 5 - Access the app

Find node IPs:
```sh
kubectl get nodes -o wide
```

Add to `/etc/hosts` on the machine you browse from:
```
192.168.x.x  sensors.local
```

Open http://sensors.local

WebSockets (`ws://sensors.local/ws/...`) work out of the box - Traefik
handles the HTTP upgrade automatically.

---

## Redeploy after code changes

On `gl-rpi4tv.local`:
```sh
# 1. Rebuild
docker build -t sensors:latest .

# 2. Re-import into containerd
docker save sensors:latest | sudo k3s ctr images import -
```

From workstation:
```sh
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
without manual import steps - better workflow for multi-node setups.

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

`secret.yaml` stores credentials in plaintext - fine for local learning.
For production use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
or [External Secrets Operator](https://external-secrets.io).
