#!/bin/bash
# Setup script for Debian/Ubuntu servers

set -e

echo "=== FreePBX Carrier System - Debian Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    echo "   sudo ./setup-debian.sh"
    exit 1
fi

echo "✅ Running as root"
echo ""

# Update system
echo "📦 Updating system packages..."
apt update
apt upgrade -y

# Install curl first if needed
if ! command -v curl &> /dev/null; then
    echo "📦 Installing curl..."
    apt install -y curl
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    apt install -y docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo "🔄 Starting Docker..."
    systemctl start docker
    sleep 5
fi

echo "✅ Docker is running"
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "🌐 Detected server IP: $SERVER_IP"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cp .env.example .env
    
    # Generate random passwords
    MYSQL_ROOT_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    MYSQL_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    REDIS_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    GRAFANA_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    KAMAILIO_PASS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-20)
    
    # Update .env with generated passwords and server IP
    sed -i "s/change_this_root_password_now/$MYSQL_ROOT_PASS/" .env
    sed -i "s/change_this_asterisk_password/$MYSQL_PASS/" .env
    sed -i "s/change_this_redis_password/$REDIS_PASS/" .env
    sed -i "s/change_this_grafana_password/$GRAFANA_PASS/" .env
    sed -i "s/change_this_kamailio_password/$KAMAILIO_PASS/" .env
    sed -i "s/your.public.ip.address/$SERVER_IP/" .env
    sed -i "s/voip.yourcompany.com/$SERVER_IP/" .env
    
    echo "✅ .env file created with random passwords"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Source .env for later use
source .env

# Create swap if not exists (important for low memory systems)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 4GB swap file..."
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✅ Swap file created"
else
    echo "✅ Swap file already exists"
fi
echo ""

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null || true

# Install UFW if not present
if ! command -v ufw &> /dev/null; then
    echo "🔒 Installing UFW firewall..."
    apt install -y ufw
fi

# Configure firewall
echo "🔒 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (CRITICAL!)
ufw allow 22/tcp

# Allow SIP
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 5061/tcp
ufw allow 5080/udp
ufw allow 5080/tcp

# Allow RTP
ufw allow 10000:10200/udp
ufw allow 20000:30000/udp

# Allow web interface
ufw allow 80/tcp
ufw allow 443/tcp

# Allow monitoring
ufw allow 3000/tcp
ufw allow 9090/tcp

# Enable firewall
ufw --force enable

echo "✅ Firewall configured"
echo ""

# Pull Docker images
echo "📥 Pulling Docker images (this may take a few minutes)..."
docker-compose pull

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to initialize (90 seconds)..."
sleep 90

echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "🗄️  Initializing database..."
sleep 10

# Initialize database with error handling
echo "Creating database schema..."
if docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql 2>/dev/null; then
    echo "✅ Schema created"
else
    echo "⚠️  Schema may already exist or database not ready yet"
fi

echo "Loading sample data..."
if docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql 2>/dev/null; then
    echo "✅ Sample data loaded"
else
    echo "⚠️  Sample data may already exist"
fi

echo ""
echo "============================================"
echo "🎉 Setup Complete!"
echo "============================================"
echo ""
echo "🌐 Access your services:"
echo "   FreePBX:    http://$SERVER_IP"
echo "   Grafana:    http://$SERVER_IP:3000"
echo "   Prometheus: http://$SERVER_IP:9090"
echo ""
echo "🔐 Credentials saved in .env file"
echo ""
echo "📊 Grafana Login:"
echo "   Username: admin"
echo "   Password: $GRAFANA_PASSWORD"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f freepbx"
echo "   Restart services: docker-compose restart"
echo "   Stop services:    docker-compose down"
echo "   Service status:   docker-compose ps"
echo ""
echo "🔒 Firewall status:"
ufw status numbered
echo ""
echo "📚 Next steps:"
echo "   1. Access FreePBX at http://$SERVER_IP"
echo "   2. Complete initial setup wizard"
echo "   3. Configure your first trunk (see docs/QUICK-START.md)"
echo "   4. Add customers and start billing!"
echo ""
echo "⚠️  IMPORTANT: Save your .env file - it contains all passwords!"
echo ""
