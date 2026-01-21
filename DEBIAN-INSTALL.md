# Debian Server Installation

## Quick Install (One Command)

SSH into your Debian server and run:

```bash
# Clone the repository
git clone https://github.com/treez250/carrier-freepbx.git
cd carrier-freepbx

# Run setup script
sudo ./setup-debian.sh
```

That's it! The script will:
- ✅ Install Docker and Docker Compose
- ✅ Configure firewall (UFW)
- ✅ Create swap space
- ✅ Generate secure passwords
- ✅ Start all services
- ✅ Initialize database
- ✅ Show you access URLs

## Manual Installation

If you prefer to do it step by step:

### 1. Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Docker
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker
sudo systemctl start docker
```

### 3. Install Docker Compose
```bash
sudo apt install docker-compose -y
```

### 4. Clone Repository
```bash
git clone https://github.com/treez250/carrier-freepbx.git
cd carrier-freepbx
```

### 5. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit and change all passwords
```

### 6. Create Swap (if needed)
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 7. Configure Firewall
```bash
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw allow 5060/udp
sudo ufw allow 5060/tcp
sudo ufw allow 5061/tcp
sudo ufw allow 10000:10200/udp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw enable
```

### 8. Start Services
```bash
sudo docker-compose up -d
```

### 9. Initialize Database
```bash
# Wait 2 minutes for services to start
sleep 120

# Load database
source .env
sudo docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql
sudo docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql
```

## System Requirements

### Minimum (Testing)
- 2GB RAM
- 1 CPU core
- 20GB disk
- Debian 11 or Ubuntu 20.04+

### Recommended (Production)
- 4GB RAM
- 2 CPU cores
- 50GB disk
- Debian 11/12 or Ubuntu 22.04

### For 50+ Concurrent Calls
- 8GB RAM
- 4 CPU cores
- 100GB disk

## After Installation

Access your services:
- **FreePBX:** http://your-server-ip
- **Grafana:** http://your-server-ip:3000
- **Prometheus:** http://your-server-ip:9090

## Troubleshooting

### Services won't start
```bash
sudo docker-compose logs -f
```

### Check service status
```bash
sudo docker-compose ps
```

### Restart everything
```bash
sudo docker-compose restart
```

### Check firewall
```bash
sudo ufw status
```

### Check disk space
```bash
df -h
```

### Check memory
```bash
free -h
```

## Security Notes

1. **Change all passwords** in .env file
2. **Restrict web access** to your IP only:
   ```bash
   sudo ufw delete allow 80/tcp
   sudo ufw allow from YOUR_IP to any port 80
   ```
3. **Enable SSL** with Let's Encrypt (see docs/SECURITY.md)
4. **Regular backups** (see docs/BACKUP.md)
5. **Monitor logs** for suspicious activity

## Next Steps

1. Complete FreePBX setup wizard
2. Configure your first SIP trunk
3. Add customer endpoints
4. Test call routing
5. Set up billing
6. Start making money!

See **docs/QUICK-START.md** for detailed next steps.
