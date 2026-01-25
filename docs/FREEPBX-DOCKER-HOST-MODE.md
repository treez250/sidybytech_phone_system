# FreePBX / Asterisk — Correct Docker Configuration (Authoritative)

## ⚠️ Core Rule (NON-NEGOTIABLE)

FreePBX MUST run with:

```yaml
network_mode: host
```

**Anything else will break RTP and is not acceptable for a phone company.**

## 1️⃣ Docker Architecture Requirements

✅ Docker is allowed
❌ Docker bridge networking is NOT allowed
❌ No port mappings for SIP or RTP
✅ RTP must flow directly via host NIC
✅ Firewall is handled at the host, not Docker

## 2️⃣ docker-compose.yml (COPY / PASTE)

This is the only approved posture.

```yaml
version: "3.8"

services:
  freepbx:
    image: tiredofit/freepbx:latest
    container_name: freepbx
    network_mode: host
    restart: unless-stopped
    
    environment:
      - ASTERISK_UID=1000
      - ASTERISK_GID=1000
      - TZ=America/New_York
      - RTP_START=10000
      - RTP_FINISH=20000
      - DB_HOST=127.0.0.1
    
    volumes:
      - freepbx-data:/data
      - freepbx-logs:/var/log/asterisk

volumes:
  freepbx-data:
  freepbx-logs:
```

### ❌ DO NOT INCLUDE (explicitly forbidden)

```yaml
ports:
  - "5060:5060/udp"
  - "5060:5060/tcp"
  - "10000-20000:10000-20000/udp"
```

**If any ports are mapped, the configuration is wrong.**

## 3️⃣ Volume Requirements

```yaml
volumes:
  freepbx-data:
  freepbx-logs:
```

- `/data` must persist across container restarts
- Logs must be available for RTP debugging

## 4️⃣ Host Firewall Requirements

On the Docker host, allow:

- UDP 5060
- UDP 10000–20000
- TCP 5060 (optional)

No Docker firewall rules required.

## 5️⃣ FreePBX Internal Settings (MANDATORY)

Inside FreePBX GUI:

### Asterisk SIP Settings → PJSIP

- NAT: **No**
- External Address: **(blank)**
- External Media Address: **(blank)**
- External Signaling Address: **(blank)**
- RTP Start: **10000**
- RTP End: **20000**

### Extensions → Advanced

- Direct Media: **No**
- Rewrite Contact: **Yes**
- RTP Symmetric: **Yes**
- Media Encryption: **None**

### Codecs

Allow ONLY:
- **PCMU (ulaw)**

Disable all others

## 6️⃣ Validation Checklist (MUST PASS)

### Inside container

```bash
docker exec -it freepbx ip addr
```

✅ Must show host IP, not 172.x.x.x

### On host during a call

```bash
tcpdump -n udp portrange 10000-20000
```

✅ Must show unicast RTP packets (~160 bytes)
❌ Broadcast or length 4 packets mean failure

### Call behavior

✅ SIP registers instantly
✅ Audio works both directions
✅ No NAT configuration required on endpoints
✅ No Docker-specific RTP rules

## 7️⃣ What This Enables (Future-Proofing)

This configuration is required for:

- Asterisk ExternalMedia()
- Live RTP interception
- Azure Speech Services
- Real-time translation
- Call recording / analytics
- Compliance monitoring

## 8️⃣ Explicitly Unsupported Configurations

❌ Docker bridge networking
❌ RTP port mapping
❌ SIP ALG anywhere
❌ Multiple codec negotiation
❌ Docker-managed NAT

## Final Instruction

**FreePBX may run in Docker only with `network_mode: host`.**

Any bridge or port-mapped configuration is considered invalid and unsupported for RTP-based services.
