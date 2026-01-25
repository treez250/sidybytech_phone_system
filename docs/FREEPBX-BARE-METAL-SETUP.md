# FreePBX / Asterisk – Required Configuration (Authoritative)

This is FreePBX / Asterisk–only, copy-paste, no Azure, no Docker, no theory.

## 1. Deployment Posture (MANDATORY)

- FreePBX must run on a VM or bare metal
- **DO NOT run FreePBX in Docker**
- Single NIC, static IP
- No NAT between phones and FreePBX (same LAN or routed network)

**This is non-negotiable for RTP reliability and future media processing.**

## 2. Global SIP (PJSIP) Settings

**Admin → Asterisk SIP Settings → PJSIP Settings**

### General
- Enable SIP Over TCP: **Yes**
- Enable SIP Over UDP: **Yes**

### RTP Settings
- RTP Port Range Start: **10000**
- RTP Port Range End: **20000**
- Strict RTP: **Yes**

### IP Configuration
- NAT: **No**
- External Address: **(blank)**
- External Media Address: **(blank)**
- External Signaling Address: **(blank)**

**Apply Config.**

## 3. Extension Settings (ALL extensions)

**Connectivity → Extensions → Extension → Advanced**

Set exactly the following for **every extension**:

- Direct Media: **No**
- Rewrite Contact: **Yes**
- RTP Symmetric: **Yes**
- Force RTP: **Yes** (if present)
- Media Encryption: **None**

### Codecs (IMPORTANT)

Allow only:
- **PCMU (ulaw)**

Disable everything else for now.

**Apply Config.**

## 4. Transport (PJSIP)

**Connectivity → SIP Settings → PJSIP → Transports**

For UDP transport:
- Protocol: **UDP**
- Bind: **0.0.0.0**
- Allow Reload: **Yes**

No NAT options enabled.

## 5. Firewall (if enabled)

If FreePBX Firewall is enabled:

**Connectivity → Firewall → Services**

Allow:
- UDP 5060
- UDP 10000–20000

Or disable FreePBX firewall entirely during testing.

## 6. Restart Procedure (REQUIRED)

After any SIP or RTP change:

```bash
systemctl restart asterisk
```

**(Do not rely on reloads.)**

## 7. Validation Checklist (MUST PASS)

### Verify Asterisk listening on RTP ports

From the FreePBX host:

```bash
ss -lunp | grep asterisk
```

**Expected:** multiple UDP ports, not just one.

### Verify live RTP during a call

```bash
tcpdump -n -i any udp and portrange 10000-20000
```

**Expected during active call:**
```
UDP, length ~160
```

Broadcast packets or length 4 do not count.

## 8. Success Definition (do not proceed unless true)

✅ Phone ↔ Phone audio works both directions
✅ RTP visible as unicast UDP traffic
✅ No Docker networking involved
✅ No NAT hacks required

**Only after this is green do we introduce ExternalMedia() or any Azure integration.**

## 9. Explicit Exclusions (DO NOT CONFIGURE)

❌ Docker networking
❌ Direct Media = Yes
❌ AudioSocket
❌ AGI audio manipulation
❌ Multiple codecs during initial setup
❌ External IP fields when on-net

---

## Final Note

This FreePBX setup is intentionally conservative and boring.

It is designed to guarantee deterministic RTP behavior for real-time media interception later.
