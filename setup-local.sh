#!/bin/bash
# Local setup script for macOS

echo "=== FreePBX Carrier System Setup ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo ""
    echo "Please install Docker Desktop for Mac:"
    echo "1. Download from: https://www.docker.com/products/docker-desktop"
    echo "2. Install and start Docker Desktop"
    echo "3. Run this script again"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate random passwords
    MYSQL_ROOT_PASS=$(openssl rand -base64 16)
    MYSQL_PASS=$(openssl rand -base64 16)
    REDIS_PASS=$(openssl rand -base64 16)
    GRAFANA_PASS=$(openssl rand -base64 16)
    
    # Update .env with generated passwords
    sed -i.bak "s/change_this_root_password_now/$MYSQL_ROOT_PASS/" .env
    sed -i.bak "s/change_this_asterisk_password/$MYSQL_PASS/" .env
    sed -i.bak "s/change_this_redis_password/$REDIS_PASS/" .env
    sed -i.bak "s/change_this_grafana_password/$GRAFANA_PASS/" .env
    sed -i.bak "s/your.public.ip.address/127.0.0.1/" .env
    sed -i.bak "s/voip.yourcompany.com/localhost/" .env
    
    rm .env.bak
    
    echo "✅ .env file created with random passwords"
    echo ""
fi

# Make scripts executable
chmod +x scripts/*.sh

echo "Starting services with Docker Compose..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d

echo ""
echo "Waiting for services to initialize (60 seconds)..."
sleep 60

echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "Initializing database..."
sleep 10

# Get MySQL password from .env
source .env

# Initialize database
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql 2>/dev/null
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql 2>/dev/null

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "🌐 Access your services:"
echo "   FreePBX:    http://localhost"
echo "   Grafana:    http://localhost:3000"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "📊 Grafana Login:"
echo "   Username: admin"
echo "   Password: ${GRAFANA_PASSWORD}"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f freepbx"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "⚠️  Note: This is a LOCAL development setup."
echo "   For production, deploy to a cloud server (see docs/CHEAP-DEPLOYMENT.md)"
echo ""
