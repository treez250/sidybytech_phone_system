# Current System State - WORKING BASELINE

**Date:** January 25, 2026
**Server:** 192.168.1.180 (GPU server)
**Status:** ✅ WORKING

## What's Running

- **FreePBX 15.0.38** in Docker
- **Asterisk 17** (underlying PBX engine)
- **MariaDB 10.11** (embedded)
- **Grafana** (monitoring)
- **Prometheus** (metrics)
- **Redis** (cache)

## Network Configuration

- **Server IP:** 192.168.1.180
- **FreePBX Web:** http://192.168.1.180
- **SIP Port:** 5060 UDP/TCP
- **RTP Ports:** 10000-10200 UDP
- **Grafana:** http://192.168.1.180:3000

## Docker Setup

- **Compose File:** `docker-compose.yml` (commit 77a6987)
- **Network Mode:** Bridge (working correctly)
- **Volumes:** Persistent data in Docker volumes

## Credentials

- **FreePBX Admin:** admin / (set during setup)
- **Grafana:** admin / (from .env file)
- **MySQL Root:** (from .env file)

## What Works

✅ FreePBX web interface accessible
✅ Docker containers running
✅ Services healthy
✅ Ready for extension configuration

## What's Next

1. Create extensions 100 and 101
2. Configure PJSIP settings (Direct Media: No, RTP Symmetric: Yes, PCMU only)
3. Test basic calling
4. Add translation service

## 5 Rules for Success

1. ✅ Calls work right now (testing next)
2. ✅ RTP stays on same host (Docker on 192.168.1.180)
3. ✅ Docker networking is simple (bridge mode)
4. ⏳ Asterisk controls media (ExternalMedia next)
5. ✅ Environment frozen (git commit + snapshot)

## DO NOT CHANGE

- Server IP
- Docker compose file (unless adding translation)
- Network mode
- RTP port range

## Rollback Plan

If anything breaks:
```bash
cd ~/sidybytech_phone_system
git checkout 77a6987
sudo docker-compose down
sudo docker-compose up -d
```

Or restore VM snapshot.
