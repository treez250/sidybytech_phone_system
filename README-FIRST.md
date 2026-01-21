# 🚀 Fresh Debian Install - Quick Deploy

## After Rolling Back to Snapshot

SSH into your fresh Debian server and run these commands:

```bash
# Install git if needed
sudo apt update
sudo apt install -y git

# Clone repository
git clone https://github.com/treez250/carrier-freepbx.git
cd carrier-freepbx

# Run automated setup (installs everything)
sudo ./setup-debian.sh
```

**That's it!** The script handles everything:
- Docker installation
- Firewall configuration  
- Service deployment
- Database initialization
- Password generation

## Time Required
- Snapshot rollback: 2-5 minutes
- Setup script: 5-10 minutes
- **Total: ~10-15 minutes to production-ready system**

## What You'll Get

After setup completes, you'll have:
- ✅ FreePBX web interface
- ✅ Asterisk PBX engine
- ✅ MariaDB database
- ✅ Redis caching
- ✅ Kamailio SIP proxy
- ✅ RTPEngine media proxy
- ✅ Prometheus monitoring
- ✅ Grafana dashboards
- ✅ Fraud detection
- ✅ Billing system
- ✅ Firewall configured
- ✅ All passwords auto-generated

## Access URLs

The script will show you:
```
FreePBX:    http://your-server-ip
Grafana:    http://your-server-ip:3000
Prometheus: http://your-server-ip:9090
```

## Credentials

All passwords are saved in `.env` file on the server.

## If Something Goes Wrong

Just roll back to snapshot again and retry. That's the beauty of snapshots!

## Next Steps After Install

See `docs/QUICK-START.md` for:
- Configuring your first trunk
- Adding customers
- Testing calls
- Setting up billing
