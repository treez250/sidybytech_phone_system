#!/bin/bash
# Setup and test Snowflake sync

set -e

echo "=== Snowflake Sync Setup ==="
echo ""

# Install Python and pip
echo "📦 Installing Python dependencies..."
apt install -y python3 python3-pip

# Install required Python packages
echo "📦 Installing Snowflake and MySQL connectors..."
pip3 install --break-system-packages -r /root/sidybytech_phone_system/scripts/requirements-snowflake.txt

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🧪 Testing Snowflake sync..."
echo ""

# Load environment variables and run sync
cd /root/sidybytech_phone_system
source scripts/snowflake-sync.env
python3 scripts/sync-to-snowflake.py

echo ""
echo "✅ Sync test complete!"
echo ""
echo "Next steps:"
echo "1. Verify data in Snowflake web UI"
echo "2. Set up automated sync with: crontab -e"
echo "   Add: 5 * * * * cd /root/sidybytech_phone_system && source scripts/snowflake-sync.env && python3 scripts/sync-to-snowflake.py >> /var/log/snowflake-sync.log 2>&1"
echo ""
