# Cheapest Deployment Guide

## Budget Options (Ranked by Cost)

### Option 1: Ultra Budget - $5-10/month
**Provider:** DigitalOcean, Vultr, or Linode
- **Specs:** 2GB RAM, 1 CPU, 50GB SSD
- **Cost:** $6-12/month
- **Capacity:** 5-10 simultaneous calls
- **Best for:** Testing, small office

### Option 2: Budget - $20-30/month
**Provider:** Hetzner (Best value!)
- **Specs:** 4GB RAM, 2 CPU, 80GB SSD
- **Cost:** €4.51/month (~$5 USD) - CX21
- **Capacity:** 20-30 simultaneous calls
- **Best for:** Small carrier operations

### Option 3: AWS Lightsail - $20/month
- **Specs:** 4GB RAM, 2 CPU, 80GB SSD
- **Cost:** $20/month
- **Capacity:** 20-30 simultaneous calls
- **Benefit:** Easy AWS integration

## Recommended: Hetzner Cloud (Cheapest!)

### Step 1: Create Hetzner Account
1. Go to https://www.hetzner.com/cloud
2. Sign up for account
3. Add payment method

### Step 2: Create Server
```bash
# Server specs:
- Location: Nuremberg, Germany (or closest to you)
- Image: Ubuntu 22.04
- Type: CX21 (2 vCPU, 4GB RAM) - €4.51/month
- Volume: None needed initially
- Network: Default
- SSH Key: Add your public key
```

### Step 3: Initial Server Setup
```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create swap (important for 4GB RAM)
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Step 4: Deploy FreePBX
```bash
# Clone your repo
git clone https://github.com/treez250/carrier-freepbx.git
cd carrier-freepbx

# Setup environment
cp .env.example .env
nano .env  # Change passwords and set EXTERNAL_IP

# Get your public IP
curl ifconfig.me

# Update .env with your IP
EXTERNAL_IP=your.server.ip
SIP_DOMAIN=your.server.ip  # or domain if you have one

# Start services
docker-compose up -d

# Wait 2-3 minutes for services to start
docker-compose ps

# Initialize database
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql
```

### Step 5: Configure Firewall
```bash
# Install UFW
apt install ufw -y

# Allow SSH (IMPORTANT - do this first!)
ufw allow 22/tcp

# Allow SIP
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 5061/tcp

# Allow RTP
ufw allow 10000:10200/udp

# Allow web interface (restrict to your IP for security)
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable
```

### Step 6: Access FreePBX
```
http://your-server-ip
```

## Cost Breakdown (Monthly)

### Hetzner Setup (Recommended)
- Server (CX21): €4.51 (~$5)
- Bandwidth: Included (20TB)
- **Total: ~$5/month**

### Additional Costs to Consider
- Domain name: $10-15/year (~$1/month)
- SSL certificate: FREE (Let's Encrypt)
- DID numbers: $1-5/month per number
- Upstream trunk: Pay-as-you-go (varies)
- Backups: €3.20/month (optional)

### Total Minimum Cost: $6-10/month

## Cost Optimization Tips

### 1. Use Prepaid Billing
- Charge customers upfront
- Avoid credit risk
- Better cash flow

### 2. Choose Cheap Upstream Carriers
- VoIP.ms: $0.009/min USA
- Twilio: $0.013/min USA
- Bandwidth.com: $0.004/min USA (wholesale)

### 3. Minimize DID Costs
- Only buy DIDs you need
- Use toll-free sparingly
- Consider virtual numbers

### 4. Optimize Bandwidth
- Use G.729 codec (saves 50% bandwidth vs ulaw)
- Disable video if not needed
- Use VAD (Voice Activity Detection)

### 5. Automate Everything
- Automated billing (included)
- Automated fraud detection (included)
- Automated backups

## Scaling Up Later

When you grow:
- **10-50 calls:** Upgrade to CX31 (€8.21/month)
- **50-100 calls:** Upgrade to CX41 (€15.79/month)
- **100+ calls:** Consider dedicated server

## Free Alternatives (Not Recommended for Production)

### Oracle Cloud Free Tier
- 2 VMs with 1GB RAM each (too small)
- Free forever
- **Issue:** Not enough resources for carrier operations

### AWS Free Tier
- t2.micro (1GB RAM)
- Free for 12 months only
- **Issue:** Too small, not sustainable

## Backup Strategy (Cheap)

### Option 1: Hetzner Backup
- €3.20/month for automated backups
- 7 backup slots

### Option 2: Manual Backups
```bash
# Backup script (free)
#!/bin/bash
docker exec pbx-mariadb mysqldump -u root -p${MYSQL_ROOT_PASSWORD} asterisk > backup-$(date +%Y%m%d).sql
# Upload to your own storage
```

### Option 3: Backblaze B2
- $0.005/GB/month storage
- First 10GB free
- Very cheap for small databases

## Monitoring (Free)

All included in your setup:
- Prometheus (free)
- Grafana (free)
- Built-in fraud detection

## Next Steps

1. Create Hetzner account
2. Deploy server ($5/month)
3. Configure FreePBX
4. Get upstream trunk account
5. Buy your first DID
6. Add your first customer
7. Start making money!

## Revenue Model

Example pricing:
- Charge customers: $0.02/min
- Your cost: $0.01/min
- Profit: $0.01/min

With just 1000 minutes/month:
- Revenue: $20
- Cost: $10 (trunk) + $5 (server) = $15
- Profit: $5

With 10,000 minutes/month:
- Revenue: $200
- Cost: $100 (trunk) + $5 (server) = $105
- Profit: $95

Scale from there!
