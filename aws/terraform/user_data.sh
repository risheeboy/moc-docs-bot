#!/bin/bash
set -e

# ECS Agent Setup Script for GPU instances
# This script runs when EC2 instances are launched

# Update system packages
yum update -y
yum install -y \
  aws-cli \
  docker \
  git \
  htop \
  iotop \
  nvtop \
  tmux \
  wget \
  curl

# Configure ECS agent
echo "ECS_CLUSTER=${ecs_cluster_name}" >> /etc/ecs/ecs.config
echo "ECS_ENABLE_CONTAINER_METADATA=true" >> /etc/ecs/ecs.config
echo "ECS_ENABLE_SPOT_INSTANCE_DRAINING=true" >> /etc/ecs/ecs.config
echo "ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=1h" >> /etc/ecs/ecs.config
echo "ECS_ENABLE_GPU_SUPPORT=true" >> /etc/ecs/ecs.config
echo "ECS_AVAILABLE_LOGGING_DRIVERS=[\"json-file\",\"awslogs\"]" >> /etc/ecs/ecs.config
echo "ECS_ENABLE_CONTAINER_INSTANCE_IAM_ROLE=true" >> /etc/ecs/ecs.config

# Install NVIDIA drivers and CUDA for GPU support
yum install -y gcc kernel-devel-$(uname -r)
yum install -y https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-repo-rhel8-11.8.0-1.x86_64.rpm
yum install -y cuda-drivers cuda-toolkit-11-8

# Add NVIDIA paths to environment
echo "export PATH=/usr/local/cuda-11.8/bin:$PATH" >> /etc/bashrc
echo "export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH" >> /etc/bashrc

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | rpm --import -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
  tee /etc/yum.repos.d/nvidia-docker.repo
yum install -y nvidia-container-toolkit

# Restart Docker and ECS agent
systemctl restart docker
systemctl restart --no-block ecs

# CloudWatch agent setup (optional)
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Log completion
echo "ECS GPU instance setup completed at $(date)" > /var/log/ecs-gpu-setup.log

# Health check endpoint (optional, for load balancer)
cat > /usr/local/bin/ecs-health-check.sh << 'EOF'
#!/bin/bash
if curl -f http://localhost:51678/v1/metadata | jq '.Status' | grep -q 'ACTIVE'; then
  exit 0
else
  exit 1
fi
EOF
chmod +x /usr/local/bin/ecs-health-check.sh
