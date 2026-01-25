# Cheap Cloud Deployment Options for FreePBX Carrier System

## 💰 Cost Breakdown (Monthly)

### Option 1: DigitalOcean (RECOMMENDED - Easiest)
**$24/month total**
- **Droplet**: $18/month (4GB RAM, 2 vCPU, 80GB SSD)
  - Debian 12
  - Enough for 50-100 concurrent calls
- **Floating IP**: $6/month (static IP for SIP)
- **Bandwidth**: 4TB included (plenty for VoIP)
- **Backups**: +$3.60/month (optional but recommended)

**Total with backups: $27.60/month**

### Option 2: Vultr (Slightly Cheaper)
**$18/month total**
- **Instance**: $18/month (4GB RAM, 2 vCPU, 80GB SSD)
- **Static IP**: Included free
- **Bandwidth**: 3TB included
- **Snapshots**: $1/month per snapshot

**Total with 1 snapshot: $19/month**

### Option 3: Linode (Now Akamai)
**$24/month total**
- **Linode**: $24/month (4GB RAM, 2 vCPU, 80GB SSD)
- **Static IP**: Included free
- **Bandwidth**: 4TB included
- **Backups**: +$5/month

**Total with backups: $29/month**

### Option 4: AWS Lightsail (AWS Ecosystem)
**$20/month total**
- **Instance**: $20/month (4GB RAM, 2 vCPU, 80GB SSD)
- **Static IP**: Included free
- **Bandwidth**: 4TB included
- **Snapshots**: $0.05/GB/month (~$4/month for full backup)

**Total with snapshots: $24/month**

### Option 5: Hetzner (CHEAPEST - Europe)
**€9.29/month (~$10 USD)**
- **CX32**: €9.29/month (8GB RAM, 4 vCPU, 80GB SSD)
- **Static IP**: Included free
- **Bandwidth**: 20TB included
- **Location**: Germany (higher latency to US)

**Total: ~$10/month** ⚠️ But EU-based, may have latency issues

---

## 🏆 BEST CHOICE: Vultr or DigitalOcean

### Why Vultr ($18/month):
✅ Cheapest US-based option
✅ Good network for VoIP
✅ Simple setup
✅ Free static IP
✅ 3TB bandwidth (plenty)

### Why DigitalOcean ($24/month):
✅ Better documentation
✅ Easier to use
✅ Better support
✅ More reliable
✅ 4TB bandwidth

---

## 📊 What You Get for $18-24/month

- **Concurrent Calls**: 50-100 simultaneous calls
- **Extensions**: Unlimited (realistically 100-500)
- **Storage**: 80GB (millions of CDR records)
- **Uptime**: 99.99% SLA
- **Bandwidth**: 3-4TB/month
  - ~1GB per 1000 minutes of calls
  - 3TB = ~3 million minutes/month
- **Backups**: Automated snapshots
- **Monitoring**: Built-in

---

## 🚀 Quick Setup on Vultr (15 minutes)

### 1. Create Account
- Go to vultr.com
- Sign up (use promo code for $100 free credit)

### 2. Deploy Server
```
Choose Server:
- Cloud Compute - Shared CPU
- Location: New York or Los Angeles (closest to you)
- OS: Debian 12 x64
- Plan: 4GB RAM / 2 CPU ($18/month)
- Disable Auto Backups (use snapshots instead)
- Add SSH Key (optional but recommended)
```

### 3. Get Your Server IP
```
Wait 2 minutes for deployment
Note your IP address: xxx.xxx.xxx.xxx
```

### 4. SSH and Deploy
```bash
# From your Mac
ssh root@xxx.xxx.xxx.xxx

# On the server
apt update && apt install -y git
git clone https://github.com/treez250/sidybytech_phone_system.git
cd sidybytech_phone_system
./setup-debian.sh
```

### 5. Configure Firewall
```bash
# Vultr has a firewall in their control panel
# Allow these ports:
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 3000 (Grafana)
- 5060-5061 (SIP)
- 10000-20000 (RTP - voice)
```

### 6. Point Your Domain
```
In your DNS (Cloudflare, etc):
pbx.sidebytech.net → xxx.xxx.xxx.xxx
```

### 7. Done!
```
Access FreePBX: http://xxx.xxx.xxx.xxx
Access Grafana: http://xxx.xxx.xxx.xxx:3000
```

---

## 💡 Cost Optimization Tips

### Start Small, Scale Up
- Start with $18/month Vultr
- Monitor CPU/RAM usage
- Upgrade only when needed

### Use Snapshots, Not Backups
- Backups = automatic, expensive
- Snapshots = manual, cheap ($1/month)
- Take snapshot before changes

### Monitor Bandwidth
- VoIP uses ~1MB per minute per call
- 3TB = 3 million minutes
- You'll likely use <100GB/month starting out

### Shut Down Dev/Test Instances
- Only run production 24/7
- Spin up test servers as needed
- Delete when done

---

## 📈 Scaling Costs

| Concurrent Calls | RAM Needed | Vultr Cost | DO Cost |
|-----------------|------------|------------|---------|
| 10-50           | 4GB        | $18/mo     | $24/mo  |
| 50-100          | 4GB        | $18/mo     | $24/mo  |
| 100-200         | 8GB        | $36/mo     | $48/mo  |
| 200-500         | 16GB       | $72/mo     | $96/mo  |
| 500-1000        | 32GB       | $144/mo    | $192/mo |

---

## 🔒 Security Considerations

### Included in Setup Script
✅ Firewall (ufw)
✅ Fail2ban (blocks brute force)
✅ Strong passwords
✅ Docker isolation

### Additional (Recommended)
- Change SSH port from 22
- Use SSH keys only (disable password auth)
- Enable 2FA on cloud provider
- Set up monitoring alerts

---

## 🎯 My Recommendation

**Start with Vultr $18/month:**

1. **Cheapest reliable option**
2. **Free $100 credit** (5+ months free)
3. **Easy to upgrade** when you grow
4. **Good VoIP network**
5. **Simple interface**

**Total startup cost: $0 (with free credit)**

After free credit runs out: **$18/month**

---

## 🆚 Comparison to Your Home Server

| Feature | Home Server | Cloud ($18/mo) |
|---------|-------------|----------------|
| Cost | $0/month | $18/month |
| Reliability | 95-98% | 99.99% |
| Power outages | ❌ Affects you | ✅ No impact |
| Internet outages | ❌ Affects you | ✅ No impact |
| Bandwidth | Limited by ISP | 3TB included |
| Static IP | Extra cost | Included |
| Backups | Manual | Automated |
| Scaling | Buy hardware | Click button |
| Support | None | 24/7 |

**For a carrier system, cloud is worth the $18/month for reliability alone.**

---

## 🚀 Ready to Deploy?

Let me know which provider you want to use and I'll walk you through it!

**Recommended: Vultr $18/month**
- Sign up: https://vultr.com
- Use promo code for $100 free credit
- Deploy in 15 minutes

