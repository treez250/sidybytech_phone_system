# Carrier-Level FreePBX/Asterisk System

A production-ready VoIP carrier platform built on FreePBX and Asterisk.

## Features

- Multi-tenant support
- SIP trunk management
- Call routing and least-cost routing (LCR)
- CDR (Call Detail Records) with billing integration
- High availability and failover
- Security hardening
- Rate limiting and fraud prevention
- Real-time monitoring and analytics

## Architecture

- Asterisk 20+ (core PBX engine)
- FreePBX (web management interface)
- MariaDB (database backend)
- Redis (caching and session management)
- Kamailio (SIP proxy/load balancer)
- RTPEngine (media proxy)
- Fail2ban (security)
- Prometheus + Grafana (monitoring)

## Quick Start

```bash
# Deploy with Docker Compose
docker-compose up -d

# Or use Ansible for bare metal
ansible-playbook -i inventory/production deploy.yml
```

## Configuration

See `docs/` directory for detailed configuration guides.

## Security

- Change all default passwords in `.env`
- Configure firewall rules
- Enable fail2ban
- Set up SSL certificates
- Review security hardening checklist

## License

Proprietary - All rights reserved
