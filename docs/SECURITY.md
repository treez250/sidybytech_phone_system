# Security Guide

## Critical Security Steps

### 1. Change All Default Passwords

Edit `.env` file and change:
- MYSQL_ROOT_PASSWORD
- MYSQL_PASSWORD
- REDIS_PASSWORD
- GRAFANA_PASSWORD
- FREEPBX_ADMIN_PASSWORD

### 2. Firewall Configuration

Allow only necessary ports:
```bash
# SIP
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 5061/tcp

# RTP
ufw allow 10000:10200/udp

# Web interface (restrict to your IP)
ufw allow from YOUR_IP to any port 80
ufw allow from YOUR_IP to any port 443

# Monitoring (restrict to your IP)
ufw allow from YOUR_IP to any port 3000
ufw allow from YOUR_IP to any port 9090
```

### 3. Enable Fail2Ban

Fail2ban is included in the FreePBX container. Monitor:
```bash
docker exec pbx-freepbx fail2ban-client status asterisk
```

### 4. SSL/TLS Certificates

Use Let's Encrypt for free SSL:
```bash
certbot certonly --standalone -d voip.yourcompany.com
```

Copy certificates to Asterisk:
```bash
cp /etc/letsencrypt/live/voip.yourcompany.com/fullchain.pem /path/to/asterisk/keys/asterisk.crt
cp /etc/letsencrypt/live/voip.yourcompany.com/privkey.pem /path/to/asterisk/keys/asterisk.key
```

### 5. Rate Limiting

Configure in extensions_custom.conf:
- MAX_CALL_RATE: Maximum calls per time period
- MAX_REGISTRATION_RATE: Maximum registrations per time period

### 6. IP Whitelisting

Add trusted IPs to pjsip_custom.conf ACL section.

### 7. Strong SIP Passwords

Generate strong passwords for all SIP accounts:
```bash
openssl rand -base64 32
```

### 8. Database Security

- Use strong passwords
- Restrict database access to localhost
- Enable binary logging for audit trail
- Regular backups

### 9. Monitoring and Alerts

- Enable Prometheus alerts
- Monitor fraud detection logs
- Review CDRs regularly
- Set up email/SMS alerts

### 10. Regular Updates

Keep all components updated:
```bash
docker-compose pull
docker-compose up -d
```

## Fraud Prevention

1. Enable fraud detection in dialplan
2. Set call rate limits per customer
3. Monitor unusual calling patterns
4. Implement geographic restrictions
5. Use prepaid billing when possible
6. Regular balance checks
7. Blacklist suspicious numbers

## Compliance

- Record keeping (CDRs)
- CALEA compliance (if applicable)
- GDPR/data protection
- Emergency services (E911)
- Number portability
- Caller ID regulations

## Incident Response

1. Monitor fraud alerts
2. Investigate suspicious activity
3. Block compromised accounts immediately
4. Review logs and CDRs
5. Update security measures
6. Document incidents
