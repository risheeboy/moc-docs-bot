# Prerequisites — System Requirements & Setup

**Version:** 1.0.0
**Target:** NIC/MeitY Data Centre Deployment
**Last Updated:** February 24, 2026

---

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Operating System](#operating-system)
3. [GPU & CUDA Setup](#gpu--cuda-setup)
4. [Docker Installation](#docker-installation)
5. [NVIDIA Container Toolkit](#nvidia-container-toolkit)
6. [Network Requirements](#network-requirements)
7. [Storage Requirements](#storage-requirements)
8. [Pre-Deployment Checklist](#pre-deployment-checklist)

---

## Hardware Requirements

### Minimum Configuration

```
CPU:           16 cores / 32 threads (Intel Xeon or ARM equivalent)
RAM:           64 GB DDR4/DDR5
GPU:           1x NVIDIA A100 (80GB) or 2x NVIDIA A40 (48GB each)
Storage (SSD): 500 GB (NVMe, for model cache and OS)
Storage (HDD): 10 TB (for document storage via MinIO)
Network:       10 Gbps dedicated link (for NIC/MeitY data centre)
```

### Recommended Configuration

```
CPU:           32+ cores / 64 threads (Intel Xeon Scalable 3rd Gen or higher)
RAM:           128 GB DDR4/DDR5 (ECC preferred)
GPU:           2x NVIDIA A100 (80GB each) with NVLink bridge
Storage (SSD): 1 TB NVMe (OS + model cache)
Storage (HDD): 20+ TB (redundancy for documents)
Network:       25 Gbps dedicated link + 1 Gbps failover
UPS:           48-hour battery for graceful shutdown
```

### GPU Model Compatibility

| Model | Memory | Inference Speed | Cost | Recommendation |
|---|---|---|---|---|
| NVIDIA H100 | 80GB | Fastest | Highest | Best for scale |
| NVIDIA A100 | 80GB | Very Fast | High | Recommended minimum |
| NVIDIA A40 | 48GB | Fast | Medium | Budget alternative (2x needed) |
| NVIDIA L40 | 48GB | Fast | Medium | Balanced option |

**NoteL** All models require CUDA Compute Capability 7.0+ (Volta generation or newer).

---

## Operating System

### Supported Versions

**Primary:**
- Ubuntu Server 22.04 LTS (recommended for NIC/MeitY)
- Ubuntu Server 20.04 LTS (still supported)

**Alternative:**
- Debian 12 (Bookworm)
- Red Hat Enterprise Linux 8.8+
- AlmaLinux 9

### OS Installation

1. Use Ubuntu 22.04 LTS minimal installation
2. Allocate 500 GB SSD to `/` (root)
3. Allocate 10+ TB HDD to `/mnt/data` (MinIO storage)
4. Install with LVM for flexibility
5. Enable automatic security updates

### Required System Packages

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required tools
sudo apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    linux-headers-generic \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    htop \
    iotop \
    net-tools \
    tmux \
    vim \
    jq

# Python development (if needed)
sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip
```

---

## GPU & CUDA Setup

### Check GPU

```bash
# Verify GPU is detected
lspci | grep -i nvidia

# Expected output:
# 1a:00.0 3D controller: NVIDIA Corporation A100-PCIE-40GB (rev a1)
```

### NVIDIA Driver Installation

**Minimum Version:** 535
**Recommended Version:** Latest (550+)

#### Method 1: Ubuntu Repository (Recommended for NIC/MeitY)

```bash
# Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install driver
sudo apt-get update
sudo apt-get install -y nvidia-driver-550

# Verify installation
nvidia-smi

# Expected output:
# +-------------------------+
# | NVIDIA-SMI 550.54.15    |
# | Driver Version: 550.54  |
# +-------------------------+
```

#### Method 2: NVIDIA CUDA Toolkit

```bash
# Download CUDA Toolkit 12.1 (matches LLM requirements)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-repo-ubuntu2204_12.1.0-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204_12.1.0-1_amd64.deb
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
sudo apt-get update

# Install CUDA
sudo apt-get install -y cuda-12-1

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.1/bin${PATH:+:${PATH}}' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc
source ~/.bashrc

# Verify
nvcc --version
# Expected: CUDA 12.1
```

### CUDA Environment Variables

Add to `/etc/environment` (for system-wide access):

```bash
CUDA_HOME=/usr/local/cuda-12.1
PATH=$CUDA_HOME/bin:$PATH
LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
CUDA_DEVICE_ORDER=PCI_BUS_ID
```

### cuDNN (Deep Learning Library)

Required for optimal LLM performance:

```bash
# Download cuDNN from NVIDIA (requires free account)
# https://developer.nvidia.com/cudnn

# For CUDA 12.1, download cuDNN 8.9.x

# Extract and install
tar -xzf cudnn-linux-x86_64-8.9.6.tar.xz
sudo cp cudnn-linux-x86_64-8.9.6/include/cudnn*.h /usr/local/cuda-12.1/include/
sudo cp -P cudnn-linux-x86_64-8.9.6/lib/libcudnn* /usr/local/cuda-12.1/lib64/
sudo chmod a+r /usr/local/cuda-12.1/include/cudnn*.h
sudo chmod a+r /usr/local/cuda-12.1/lib64/libcudnn*

# Verify
ldconfig -p | grep cudnn
```

### GPU Memory Configuration

For optimal vLLM performance:

```bash
# Create /etc/nvidia/nvidia-docker.json
sudo tee /etc/nvidia/nvidia-docker.json > /dev/null <<EOF
{
    "nvidia-docker-version": "1.0.1",
    "driver-capabilities": "compute,utility,graphics"
}
EOF

# Set GPU persistence mode (keeps GPU loaded)
sudo nvidia-smi -pm 1

# Set clock frequency to max (optional, increases power consumption)
sudo nvidia-smi -lgc 1410
```

---

## Docker Installation

### Install Docker Engine

```bash
# Remove old Docker versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install Docker repository
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify
docker --version
# Expected: Docker version 27.x or higher
```

### Configure Docker

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Apply new group membership (log out and back in, or run):
newgrp docker

# Configure Docker daemon for GPU access
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "runc",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

# Restart Docker daemon
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### Install Docker Compose

```bash
# Install Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker-compose --version
# Expected: Docker Compose version 2.23.x
```

---

## NVIDIA Container Toolkit

Required to use NVIDIA GPUs inside Docker containers.

### Install NVIDIA Container Runtime

```bash
# Add NVIDIA Container repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure containerd for GPU support
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker
sudo systemctl restart docker
```

### Verify GPU Access in Containers

```bash
# Test GPU access
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# Expected output: GPU information should display
```

---

## Network Requirements

### Connectivity

- **Public IP:** At least one static public IP for NGINX reverse proxy
- **Internal Network:** Private 10.x or 172.x network for inter-service communication
- **Bandwidth:** Minimum 10 Gbps (for NIC/MeitY data centre)
- **Latency:** <5ms to MeitY servers

### Firewall Rules

| Port | Service | Source | Direction |
|---|---|---|---|
| 443 | HTTPS (NGINX) | Internet | Inbound |
| 80 | HTTP redirect | Internet | Inbound |
| 8000 | API Gateway | Internal only | Inbound |
| 19530 | Milvus | Internal only | Inbound |
| 5432 | PostgreSQL | Internal only | Inbound |
| 6379 | Redis | Internal only | Inbound |
| 9000 | MinIO API | Internal only | Inbound |
| 9090 | Prometheus | Internal only | Inbound |
| 3000 | Grafana | Internal only | Inbound |

### DNS Configuration

Set up DNS records pointing to the NGINX server:

```
culture.gov.in          A 203.x.x.x (primary)
www.culture.gov.in      A 203.x.x.x (primary)
api.culture.gov.in      A 203.x.x.x (same as primary)
status.culture.gov.in   A 203.x.x.x (same as primary)
```

---

## Storage Requirements

### Partition Scheme

```
/              500 GB    NVMe SSD    (OS, Docker, logs)
/mnt/data      10+ TB    HDD        (MinIO documents storage)
/mnt/backup    2 TB      SSD        (Backup storage)
/mnt/models    500 GB    NVMe SSD   (Model weights cache)
```

### Setup

```bash
# Create partitions (adjust device names as needed)
sudo lsblk

# Format storage devices
sudo mkfs.ext4 /dev/nvme0n1p1  # For /mnt/data partition
sudo mkdir -p /mnt/data /mnt/backup /mnt/models

# Mount devices
sudo mount /dev/nvme0n1p1 /mnt/data
sudo mount /dev/nvme0n1p2 /mnt/backup
sudo mount /dev/nvme1n1p1 /mnt/models

# Add to /etc/fstab for persistence
echo "/dev/nvme0n1p1 /mnt/data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
echo "/dev/nvme0n1p2 /mnt/backup ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
echo "/dev/nvme1n1p1 /mnt/models ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab

# Set proper permissions
sudo chown $USER:$USER /mnt/data /mnt/backup /mnt/models
sudo chmod 755 /mnt/data /mnt/backup /mnt/models
```

---

## Pre-Deployment Checklist

Run this checklist before deployment:

```bash
#!/bin/bash

echo "=== RAG-QA System Pre-Deployment Checklist ==="

# 1. Operating System
echo "1. Checking OS version..."
lsb_release -d
[ $(uname -m) = "x86_64" ] && echo "✓ x86_64 architecture" || echo "✗ Non-x86_64 detected"

# 2. GPU
echo -e "\n2. Checking GPU..."
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv,noheader
[ $? -eq 0 ] && echo "✓ GPU detected" || echo "✗ GPU not accessible"

# 3. CUDA
echo -e "\n3. Checking CUDA..."
nvcc --version | grep "Cuda"
[ $? -eq 0 ] && echo "✓ CUDA installed" || echo "✗ CUDA not found"

# 4. Docker
echo -e "\n4. Checking Docker..."
docker --version
docker run --rm hello-world > /dev/null 2>&1
[ $? -eq 0 ] && echo "✓ Docker working" || echo "✗ Docker issue"

# 5. Docker GPU Support
echo -e "\n5. Checking NVIDIA Container Toolkit..."
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi > /dev/null 2>&1
[ $? -eq 0 ] && echo "✓ GPU access in containers working" || echo "✗ GPU container access failed"

# 6. Memory
echo -e "\n6. Checking available RAM..."
free -h
RAM_GB=$(free -g | awk 'NR==2 {print $2}')
[ $RAM_GB -ge 64 ] && echo "✓ Sufficient RAM ($RAM_GB GB)" || echo "✗ Insufficient RAM ($RAM_GB GB)"

# 7. Storage
echo -e "\n7. Checking storage..."
df -h /mnt/data /mnt/backup /mnt/models 2>/dev/null
[ -d /mnt/data ] && echo "✓ /mnt/data exists" || echo "✗ /mnt/data not found"
[ -d /mnt/backup ] && echo "✓ /mnt/backup exists" || echo "✗ /mnt/backup not found"

# 8. Network
echo -e "\n8. Checking network..."
ip addr show | grep inet
ping -c 1 8.8.8.8 > /dev/null 2>&1
[ $? -eq 0 ] && echo "✓ Internet connectivity" || echo "✗ No internet connection"

# 9. System time
echo -e "\n9. Checking system time..."
timedatectl status
echo "✓ Current time: $(date)"

# 10. Port availability
echo -e "\n10. Checking required ports..."
for port in 443 80 8000 19530 5432 6379 9000; do
  ! nc -z localhost $port 2>/dev/null
  [ $? -eq 0 ] && echo "✓ Port $port available" || echo "✗ Port $port in use"
done

echo -e "\n=== Checklist complete ==="
```

Save and run:
```bash
chmod +x checklist.sh
./checklist.sh
```

---

## Troubleshooting Common Issues

### GPU Not Detected

```bash
# 1. Check physical connection
lspci | grep -i nvidia

# 2. Reload drivers
sudo modprobe -r nvidia_drm nvidia
sudo modprobe nvidia

# 3. Check driver
nvidia-smi

# 4. If still failing, reinstall driver
sudo apt-get purge nvidia-driver-*
sudo apt-get install nvidia-driver-550
```

### CUDA Compilation Errors

```bash
# Update cuDNN
sudo apt-get install libcudnn8

# Check CUDA paths
echo $CUDA_HOME
echo $LD_LIBRARY_PATH

# Rebuild with explicit paths
export CUDA_HOME=/usr/local/cuda-12.1
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
```

### Docker GPU Access Fails

```bash
# Reinstall NVIDIA Container Toolkit
sudo apt-get remove nvidia-container-toolkit
sudo apt-get install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test again
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi
```

### Insufficient GPU Memory

Check vLLM configuration in docker-compose.yml:
- Reduce `gpu_memory_utilization` from 0.85 to 0.75
- Use smaller model (e.g., 7B instead of 13B)
- Enable quantization (AWQ)

---

**Next:** Proceed to [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step installation.
