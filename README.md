## Flipkart Product Recommender Chatbot with LLMOps

An AI-powered product recommendation chatbot built using LLMs, deployed with Docker, Kubernetes and monitored using Prometheus & Grafana on Google Cloud.

## Demo

![Demo Screenshot](https://github.com/user-attachments/assets/c476cb8c-2635-41bf-9833-2d07e0b04039)

---

# Deployment Guide

## 1. Project Setup

### Upload Code to GitHub

First push your project code to your GitHub repository.

### Create Dockerfile

Add a `Dockerfile` in the root directory of the project to containerize the application.

### Kubernetes Configuration

Create a Kubernetes configuration file named:

```
llmops-k8s.yaml
```

### Create Google Cloud VM Instance

1. Open **Google Cloud Console**
2. Navigate to **Compute Engine → VM Instances**
3. Click **Create Instance**

Use the following configuration:

**Instance Configuration**

* Machine Series: **E2**
* Machine Type: **Standard**
* Memory: **16 GB RAM**

**Boot Disk**

* OS Image: **Ubuntu 24.04 LTS**
* Disk Size: **256 GB**

**Networking**

Enable both:

* HTTP Traffic
* HTTPS Traffic

After configuration click **Create Instance**.

### Connect to VM

Use the **SSH option** provided in Google Cloud Console to access the VM terminal.

---

# 2. VM Configuration

### Clone Repository

Clone your GitHub repository inside the VM.

```bash
git clone https://github.com/sneha-jagtap-patil/Flipkart_Product_Recommender_Chatbot_with-GCP.git
ls
cd <project-folder>
ls
```

You should now see all project files.

---

### Install Docker

Search for **Install Docker on Ubuntu** and follow the official documentation from Docker.

After installation test Docker with:

```bash
docker run hello-world
```

---

### Allow Docker Without sudo

Follow the **Post-installation steps for Linux** from Docker documentation to enable running Docker commands without `sudo`.

---

### Enable Docker at Startup

Run the following commands:

```bash
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

---

### Verify Docker Installation

```bash
systemctl status docker
docker ps
docker ps -a
```

Docker service should appear as **active (running)**.

---

# 3. Setup Minikube on VM

### Install Minikube

Download the Minikube binary for:

* OS: **Linux**
* Architecture: **x86**

Follow the installation instructions from the official Minikube website.

---

### Start Minikube Cluster

```bash
minikube start
```

Minikube uses Docker as its container runtime.

---

### Install kubectl

Install kubectl using snap:

```bash
sudo snap install kubectl --classic
```

Verify installation:

```bash
kubectl version --client
```

---

### Check Cluster Status

```bash
minikube status
kubectl get nodes
kubectl cluster-info
docker ps
```

You should see the **Minikube node running**.

---

# 4. Configure GitHub Access

Set Git configuration on the VM:

```bash
git config --global user.email "your-email"
git config --global user.name "your-username"

git add .
git commit -m "update"
git push origin main
```

When prompted:

* Username: your GitHub username
* Password: GitHub Personal Access Token

---

# 5. Build and Deploy Application

### Connect Docker to Minikube

```bash
eval $(minikube docker-env)
```

### Build Docker Image

```bash
docker build -t flask-app:latest .
```

### Create Kubernetes Secrets

```bash
kubectl create secret generic llmops-secrets \
  --from-literal=GROQ_API_KEY="" \
  --from-literal=ASTRA_DB_APPLICATION_TOKEN="" \
  --from-literal=ASTRA_DB_KEYSPACE="default_keyspace" \
  --from-literal=ASTRA_DB_API_ENDPOINT="" \
  --from-literal=HF_TOKEN="" \
  --from-literal=HUGGINGFACEHUB_API_TOKEN=""
```

---

### Deploy Application

```bash
kubectl apply -f flask-deployment.yaml
```

Check pods:

```bash
kubectl get pods
```

---

### Access Application

```bash
kubectl port-forward svc/flask-service 5000:80 --address 0.0.0.0
```

Open browser:

```
http://<VM-EXTERNAL-IP>:5000
```

Your application should now be running.

---

# 6. Monitoring with Prometheus and Grafana

Create monitoring namespace:

```bash
kubectl create namespace monitoring
kubectl get ns
```

---

### Deploy Prometheus

```bash
kubectl apply -f prometheus/prometheus-configmap.yaml
kubectl apply -f prometheus/prometheus-deployment.yaml
```

---

### Deploy Grafana

```bash
kubectl apply -f grafana/grafana-deployment.yaml
```

Check monitoring pods:

```bash
kubectl get pods -n monitoring
```

---

### Access Prometheus

```bash
kubectl port-forward --address 0.0.0.0 svc/prometheus-service -n monitoring 9090:9090
```

Open:

```
http://<VM-IP>:9090
```

---

### Access Grafana

```bash
kubectl port-forward --address 0.0.0.0 svc/grafana-service -n monitoring 3000:3000
```

Login Credentials

```
Username: admin
Password: admin
```

---

### Configure Grafana Data Source

1. Open **Settings → Data Sources**
2. Click **Add Data Source**
3. Select **Prometheus**

Use the following URL:

```
http://prometheus-service.monitoring.svc.cluster.local:9090
```

Click **Save & Test**.

If successful, you can start creating dashboards for monitoring application metrics.
