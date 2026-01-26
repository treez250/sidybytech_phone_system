# PJSIP Migration - Mixed Stack Fix

## 🔥 THE PROBLEM

**Symptom:** Extension 102 gets 503, extension 100 works but has auth flapping

**Root Cause:** Mixed SIP stack state
- FreePBX GUI configured for chan_sip
- Asterisk runtime using PJSIP
- Extensions split between both stacks
- Docker restart exposed the drift

**Smoking Gun Log:**
```
res_pjsip/pjsip_distributor.c Request 'REGISTER' from '<sip:100@192.168.1.180>' failed Failed to authenticate
-- Added contact 'sip:100@192.168.2.2:6197' to AOR '100'
== Endpoint 100 is now Reachable
```

This proves Asterisk is using PJSIP, not chan_sip.

---

## ✅ THE FIX (AUTHORITATIVE)

### Rule #1: Use PJSIP Only
- Modern, stable, required for RTP forking/translation
- Disable chan_sip completely
- Never mix stacks again

---

## 🧾 EXACT STEPS

### 1️⃣ FreePBX GUI - Lock to PJSIP

**Settings → Advanced Settings**

Set exactly:
- **SIP Channel Driver:** `chan_pjsip`
- **Chan SIP:** `Disabled`
- **PJSIP:** `Enabled`

**Save + Apply Config**

---

### 2️⃣ Convert ALL Extensions to PJSIP

For every extension (100, 102, etc.):

**Applications → Extensions → Edit Extension**

Change to:
- **Channel Type:** `PJSIP`
- **Transport:** `UDP`
- **Authentication:** `Inbound`
- **Media Encryption:** `None`
- **NAT:** `No`
- **Rewrite Contact:** `Yes`
- **Force rport:** `Yes`
- **Codecs:** `ulaw, alaw` (PCMU, PCMA)

**Save + Apply Config**

---

### 3️⃣ Hard Reload Asterisk

```bash
# Reload FreePBX config
docker exec -it pbx-freepbx fwconsole reload

# Restart Asterisk
docker exec -it pbx-freepbx fwconsole restart

# Enter CLI
docker exec -it pbx-freepbx asterisk -rvvvvv
```

---

### 4️⃣ Validate (THE CHECK)

At Asterisk CLI:

```
pjsip show endpoints
```

**Expected output:**
```
Endpoint:  100/100                                              Unavailable   0 of inf
Endpoint:  102/102                                              Unavailable   0 of inf
```

After phones register:
```
Endpoint:  100/100                                              Reachable     1 of inf
Endpoint:  102/102                                              Reachable     1 of inf
```

**This should return NOTHING (correct):**
```
sip show peers
```

If you see "No such command", chan_sip is disabled ✅

---

## 🎯 WHY THIS FIXES EVERYTHING

| Issue | Before | After |
|-------|--------|-------|
| 503 on 102 | Stack mismatch | Gone |
| Auth flapping | Dual registration | Gone |
| Audio issues | RTP confusion | Fixable |
| RTP translation | Impossible | Possible |
| Docker restarts | Expose drift | Stable |

---

## ⚠️ CRITICAL RULE GOING FORWARD

**Never mix chan_sip and PJSIP again. Ever.**

- FreePBX will let you do it
- Asterisk will punish you for it
- Docker will expose it randomly

---

## 📋 PJSIP SANITY CHECKLIST

Use this after ANY extension changes:

### Quick Check
```bash
docker exec -it pbx-freepbx asterisk -rx "pjsip show endpoints"
```

All extensions should show:
- ✅ Listed
- ✅ Reachable (after phone registers)
- ✅ Contact address matches phone IP

### Full Validation
```bash
# Should show all endpoints
docker exec -it pbx-freepbx asterisk -rx "pjsip show endpoints"

# Should show registrations
docker exec -it pbx-freepbx asterisk -rx "pjsip show registrations"

# Should show contacts
docker exec -it pbx-freepbx asterisk -rx "pjsip show contacts"

# Should return NOTHING or "No such command"
docker exec -it pbx-freepbx asterisk -rx "sip show peers"
```

---

## 🔍 DEBUGGING PJSIP ISSUES

### Extension Won't Register

```bash
# Check endpoint config
docker exec -it pbx-freepbx asterisk -rx "pjsip show endpoint 100"

# Check AOR (Address of Record)
docker exec -it pbx-freepbx asterisk -rx "pjsip show aor 100"

# Check auth
docker exec -it pbx-freepbx asterisk -rx "pjsip show auth 100"

# Watch registration attempts (in CLI)
pjsip set logger on
```

### Extension Registers But No Audio

```bash
# Check RTP settings
docker exec -it pbx-freepbx asterisk -rx "pjsip show endpoint 100"

# Look for:
# - direct_media: no
# - rtp_symmetric: yes
# - force_rport: yes
```

### Check What Stack is Active

```bash
# PJSIP (should work)
docker exec -it pbx-freepbx asterisk -rx "pjsip show endpoints"

# chan_sip (should fail or return nothing)
docker exec -it pbx-freepbx asterisk -rx "sip show peers"
```

---

## 📝 INCIDENT REPORT REFERENCE

This fix resolves the issue documented in:
- **INCIDENT-REPORTS.md** - Mixed stack state after Docker restore
- **CURRENT-STATE.md** - Updated to reflect PJSIP-only configuration

---

## 🚀 NEXT STEPS AFTER MIGRATION

Once all extensions are on PJSIP and working:

1. ✅ Test basic calling (100 ↔ 102)
2. ✅ Verify audio quality
3. ✅ Test external calls (if configured)
4. ✅ Add translation service (requires PJSIP)
5. ✅ Take snapshot (this is your new baseline)

---

## 💾 SNAPSHOT AFTER FIX

```bash
# Take VM snapshot
# Name: "PJSIP-only-baseline"
# Description: "All extensions migrated to PJSIP, chan_sip disabled"

# Or Docker backup
docker-compose down
tar -czf freepbx-pjsip-baseline.tar.gz /var/lib/docker/volumes/
docker-compose up -d
```

---

## 🎓 LESSONS LEARNED

1. **Mixed stacks are poison** - Pick one, disable the other
2. **GUI settings lie** - Always verify with CLI
3. **Docker exposes drift** - What worked bare-metal may break in containers
4. **PJSIP is the future** - chan_sip is deprecated
5. **Snapshot before changes** - Always have a rollback path

---

**Status:** ✅ PJSIP-only configuration is the correct, stable, long-term solution
