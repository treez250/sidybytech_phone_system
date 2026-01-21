#!/bin/bash
# Quick installer - downloads everything directly

set -e

echo "=== Quick Install ==="

# Create directory
mkdir -p /root/freepbx-carrier
cd /root/freepbx-carrier

# Download files directly from GitHub raw
echo "Downloading files..."

curl -sL https://raw.githubusercontent.com/treez250/sidybytech_phone_system/main/setup-debian.sh -o setup-debian.sh
curl -sL https://raw.githubusercontent.com/treez250/sidybytech_phone_system/main/docker-compose.yml -o docker-compose.yml
curl -sL https://raw.githubusercontent.com/treez250/sidybytech_phone_system/main/.env.example -o .env.example
curl -sL https://raw.githubusercontent.com/treez250/sidybytech_phone_system/main/.gitignore -o .gitignore

# Make executable
chmod +x setup-debian.sh

echo "Files downloaded! Running setup..."
./setup-debian.sh
