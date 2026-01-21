# Quick Start Guide - Get Running in 30 Minutes

## Prerequisites
- Server with Ubuntu 22.04 (Hetzner CX21 recommended - $5/month)
- Your server's public IP address
- SSH access to server

## Step-by-Step Setup

### 1. Prepare Server (5 minutes)
```bash
# SSH into server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
apt install docker-compose -y

# Add swap space
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 2. Deploy FreePBX (10 minutes)
```bash
# Clone repository
git clone https://github.com/treez250/carrier-freepbx.git
cd carrier-freepbx

# Configure environment
cp .env.example .env

# Edit .env file - CHANGE THESE:
nano .env
```

**Required changes in .env:**
```bash
MYSQL_ROOT_PASSWORD=YourStrongPassword123!
MYSQL_PASSWORD=AnotherStrongPass456!
REDIS_PASSWORD=RedisSecurePass789!
GRAFANA_PASSWORD=GrafanaPass012!
EXTERNAL_IP=your.server.ip.address
SIP_DOMAIN=your.server.ip.address
```

```bash
# Start all services
docker-compose up -d

# Wait 2-3 minutes for services to initialize
sleep 180

# Check services are running
docker-compose ps
```

### 3. Initialize Database (2 minutes)
```bash
# Create database schema
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql

# Load sample data
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql
```

### 4. Configure Firewall (3 minutes)
```bash
# Install firewall
apt install ufw -y

# Allow SSH (CRITICAL - do first!)
ufw allow 22/tcp

# Allow SIP signaling
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 5061/tcp

# Allow RTP media
ufw allow 10000:10200/udp

# Allow web interface
ufw allow 80/tcp
ufw allow 443/tcp

# Allow monitoring
ufw allow 3000/tcp
ufw allow 9090/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

### 5. Access FreePBX (2 minutes)
Open browser and go to:
```
http://your-server-ip
```

**Initial FreePBX Setup:**
1. Create admin account
2. Set timezone
3. Skip module updates for now
4. Click "Finish"

### 6. Configure Your First Trunk (5 minutes)

**Option A: VoIP.ms (Recommended for USA/Canada)**
1. Sign up at https://voip.ms
2. Add funds ($10 minimum)
3. In FreePBX: Connectivity → Trunks → Add SIP (chan_pjsip) Trunk
4. Settings:
   - Trunk Name: voipms
   - Outbound CallerID: Your DID
   - SIP Server: atlanta.voip.ms (or closest)
   - Username: Your VoIP.ms account
   - Secret: Your VoIP.ms password

**Option B: Twilio**
1. Sign up at https://twilio.com
2. Get SIP credentials
3. Configure similar to above

### 7. Add Your First Customer (3 minutes)

In FreePBX:
1. Applications → Extensions → Add Extension
2. Extension Number: 1001
3. Display Name: Test Customer
4. Secret: Generate strong password
5. Submit

Or via database:
```bash
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk <<EOF
INSERT INTO customers (company_name, endpoint, email, active) 
VALUES ('My First Customer', 'customer-001', 'customer@example.com', 1);

INSERT INTO customer_accounts (customer_id, balance, credit_limit) 
VALUES (LAST_INSERT_ID(), 50.00, 100.00);
EOF
```

### 8. Test Your System (5 minutes)

**Test with softphone:**
1. Download Zoiper or Linphone
2. Configure:
   - Server: your-server-ip
   - Username: 1001 (or customer-001)
   - Password: (from step 7)
   - Port: 5060
3. Register
4. Make test call

**Check logs:**
```bash
# Asterisk logs
docker exec pbx-freepbx asterisk -rx "core show channels"

# Docker logs
docker-compose logs -f freepbx
```

## You're Live! 🎉

Your carrier-grade VoIP system is now running!

## What's Included

✅ FreePBX web interface
✅ Asterisk 20+ PBX engine
✅ MariaDB database
✅ Redis caching
✅ Prometheus monitoring
✅ Grafana dashboards
✅ Fraud detection
✅ Billing system
✅ CDR tracking
✅ Fail2ban security

## Access Your Services

- **FreePBX:** http://your-server-ip
- **Grafana:** http://your-server-ip:3000 (admin/password from .env)
- **Prometheus:** http://your-server-ip:9090

## Next Steps

1. **Buy a DID number** from your trunk provider
2. **Set up inbound routing** in FreePBX
3. **Add more customers** and start billing
4. **Configure SSL** with Let's Encrypt
5. **Set up backups** (see docs/BACKUP.md)
6. **Review security** (see docs/SECURITY.md)

## Common Issues

**Services won't start:**
```bash
docker-compose logs
# Check for port conflicts or memory issues
```

**Can't connect to FreePBX:**
```bash
# Check firewall
ufw status
# Check if service is running
docker-compose ps
```

**No audio in calls:**
```bash
# Verify RTP ports are open
ufw status | grep 10000
# Check EXTERNAL_IP is set correctly in .env
```

**Database connection failed:**
```bash
# Restart MariaDB
docker-compose restart mariadb
# Wait 30 seconds
docker-compose restart freepbx
```

## Support

- Check logs: `docker-compose logs -f`
- Restart services: `docker-compose restart`
- Full reset: `docker-compose down && docker-compose up -d`

## Cost Summary

- Server: $5/month (Hetzner)
- Trunk: Pay-as-you-go (~$0.01/min)
- DIDs: $1-5/month per number
- **Total: ~$10-15/month to start**

Now go make some money! 💰
