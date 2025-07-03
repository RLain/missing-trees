#!/bin/bash
# terraform/user_data.sh

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/${app_name}
cd /opt/${app_name}

# Create docker-compose.yml
cat > docker-compose.yml << EOF
services:
  missing-tree-api:
    build: .
    ports:
      - "3000:5000"
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    volumes:
      - ./app:/app
EOF

# Create Dockerfile for your repository structure
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn pointing to your app structure
# Adjust the module path based on your repository structure
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "src.app:app"]
EOF

apt-get install -y git
git clone --branch ${repository_branch} ${repository_url} app
cd app

# Set proper permissions
chown -R ubuntu:ubuntu /opt/${app_name}

# Build and run the application
docker-compose up -d

# Create a simple systemd service to ensure the app starts on boot
cat > /etc/systemd/system/${app_name}.service << EOF
[Unit]
Description=${app_name} Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${app_name}
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable ${app_name}.service