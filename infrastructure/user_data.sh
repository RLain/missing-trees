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

# Create Dockerfile for the repository structure
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

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

# -------------------------------
# Install Nginx and set up SSL
# -------------------------------

# Install Nginx and OpenSSL
apt-get install -y nginx openssl

# Create SSL directory
mkdir -p /etc/ssl/${app_name}

# Get EC2 public IP for certificate SAN
public_ip=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

# Generate self-signed cert
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/${app_name}/selfsigned.key \
  -out /etc/ssl/${app_name}/selfsigned.crt \
  -subj "/CN=${app_name}" \
  -addext "subjectAltName=IP:$${public_ip}"

# Create Nginx config
cat > /etc/nginx/sites-available/${app_name} << EOF
server {
    listen 80;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/ssl/${app_name}/selfsigned.crt;
    ssl_certificate_key /etc/ssl/${app_name}/selfsigned.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the new site
ln -s /etc/nginx/sites-available/${app_name} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Restart Nginx
systemctl restart nginx