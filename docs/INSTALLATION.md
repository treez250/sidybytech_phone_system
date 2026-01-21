# Installation Guide

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM
- 50GB disk space
- Public IP address for SIP traffic
- Domain name (recommended)

## Quick Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd carrier-freepbx
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Edit `.env` and change all passwords and settings:
```bash
nano .env
```

4. Update your external IP in `.env`:
```bash
EXTERNAL_IP=your.public.ip.address
SIP_DOMAIN=voip.yourcompany.com
```

5. Start the services:
```bash
docker-compose up -d
```

6. Initialize the database:
```bash
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/schema.sql
docker exec -i pbx-mariadb mysql -uroot -p${MYSQL_ROOT_PASSWORD} asterisk < database/seed.sql
```

7. Access FreePBX web interface:
```
http://your-server-ip
```

## Post-Installation

1. Complete FreePBX initial setup wizard
2. Configure firewall rules
3. Set up SSL certificates
4. Configure your first trunk
5. Add customer endpoints
6. Test call routing

## Security Hardening

- Change all default passwords
- Enable fail2ban
- Configure iptables/firewall
- Set up SSL/TLS
- Enable rate limiting
- Review security checklist in docs/SECURITY.md

## Monitoring

Access monitoring dashboards:
- Grafana: http://your-server-ip:3000 (admin/password from .env)
- Prometheus: http://your-server-ip:9090

## Troubleshooting

Check logs:
```bash
docker-compose logs -f freepbx
docker-compose logs -f kamailio
```

Check service status:
```bash
docker-compose ps
```

Restart services:
```bash
docker-compose restart
```
