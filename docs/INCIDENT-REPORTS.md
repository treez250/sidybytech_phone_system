# Incident Reports - Lessons Learned

## 🔥 INCIDENT REPORT #1
### FreePBX Framework Uninstall Catastrophic Failure

**Incident Date:** January 20, 2026

**System:**
- Debian 12
- FreePBX 16
- Apache + PHP 7.4 (mod_php)
- MariaDB
- Asterisk

### Summary (Executive-Level)
The FreePBX system became irreversibly inoperable after the Framework module was forcibly uninstalled using fwconsole. This action destroyed core database state required for FreePBX initialization. Although files and services remained present, the FreePBX application could no longer bootstrap, causing permanent GUI failure.

This failure cannot be recovered via reinstalling files or restoring partial configuration and requires a full rebuild.

### Timeline of Events

**Initial issue**
- GUI login/session errors appeared
- Suspected permission or PHP session issues

**Troubleshooting attempt**
Ran:
```bash
fwconsole ma uninstall framework --force
```
Intent: reset FreePBX core

**Immediate effect**
GUI began throwing fatal PHP errors:
- `Class 'FreePBX' not found`
- `Call to a member function get() on null`

**Subsequent actions**
- File permissions repaired
- Apache and PHP validated
- Sessions directory repaired
- `/etc/freepbx.conf` corrected
- Framework files confirmed present on disk

**Outcome**
- GUI permanently broken
- Framework object never instantiated
- `$moduleList` NULL in FreePBX runtime

### Root Cause

❌ **Critical Mistake:** Uninstalling the FreePBX Framework module

The Framework module is not a normal module. It is the application runtime itself.

Uninstalling it:
- Deletes critical rows in:
  - `modules`
  - `freepbx_settings`
  - `module_xml`
  - `notifications`
- Breaks dependency resolution
- Prevents `FreePBX.class.php` from initializing core objects

Once removed, FreePBX cannot rebuild its internal module registry, even if files are restored.

### Why Recovery Failed

| Attempted Fix | Why It Failed |
|--------------|---------------|
| Reinstall framework files | DB state already corrupted |
| Fix permissions | Permissions were not the issue |
| Fix PHP sessions | Session errors were secondary symptoms |
| Restore `/etc/freepbx.conf` | Framework bootstrap never ran |
| Restart Apache / PHP | Application layer already broken |

FreePBX does not have a supported recovery path for a removed framework module.

### Key Technical Indicator

Fatal error:
```
Call to a member function get() on null
```

This occurs because:
```php
$moduleList = FreePBX::create()->Modules;
```
returned NULL, meaning Framework never initialized.

### Impact
- GUI completely unusable
- No module management
- No safe database repair path
- System rebuild required

### Final Resolution
✅ Abandon system  
✅ Rebuild FreePBX from scratch  
✅ Restore configs only after clean install

### Permanent Lesson Learned

🔒 **The FreePBX Framework module must NEVER be uninstalled.**

Not to "reset." Not to "fix." Not even with `--force`.

---

## 🔥 INCIDENT REPORT #2
### Permission Drift & False-Positive Debug Spiral

**Incident Date:** January 20, 2026 (later same day)

### Summary
After the initial framework failure, secondary PHP warnings and permission-related errors led to an extended debugging effort focused on filesystem permissions and PHP sessions. These errors were symptoms, not causes, and masked the real underlying issue: a broken application core.

### Timeline of Events

**Post-framework failure**
GUI throws session warnings

PHP reports:
```
session_start(): Permission denied
include_once(/etc/freepbx.conf): Permission denied
```

**Corrective actions**
Repaired:
- `/var/lib/php/sessions`
- `/etc/freepbx.conf`
- Apache user permissions

Verified:
- PHP CLI and Apache consistency
- AppArmor not blocking
- www-data could read/write sessions

**Result**
- Session tests succeeded
- Permissions verified correct
- Fatal errors persisted

### Root Cause

❌ **False Attribution:** Permission errors were secondary failures caused by the FreePBX framework not loading.

When Framework fails:
- Configuration loading short-circuits
- Session handling breaks
- Error handling cascades misleading warnings

### Why This Was Hard to Diagnose

- PHP errors looked legitimate
- Permissions were actually wrong at one point
- Fixing permissions removed some warnings
- Core fatal error remained unchanged
- This created a false sense of progress

### Key Insight

In FreePBX, permission errors after framework failure are downstream noise, not root cause.

### What Was Actually Working (Important)

✔ Apache  
✔ PHP  
✔ MariaDB  
✔ Sessions  
✔ Filesystem  
✔ AppArmor  

❌ FreePBX runtime

### Impact
- Several hours lost chasing non-root causes
- Increased system entropy
- Reduced confidence in recovery

### Final Resolution
Recognized as unrecoverable application state, stopped debugging, rolled back, and planned clean rebuild.

---

## Combined Lessons Learned (These Matter)

### 1️⃣ Snapshot BEFORE:
- Module changes
- Permission changes
- fwconsole operations

### 2️⃣ Never uninstall:
- framework
- core
- sip
- settings
- voicemail

### 3️⃣ If you see:
```
Class 'FreePBX' not found
```
➡️ **Stop immediately. Rebuild.**

### 4️⃣ Debug order for FreePBX:
1. Framework present?
2. Framework enabled?
3. Database intact?
4. THEN permissions

---

## Final Takeaway (Plain English)

You didn't "mess up twice."

You:
1. Hit a known FreePBX kill switch
2. Then hit a classic post-mortem trap where symptoms look like causes

This is earned knowledge — the kind that makes future builds rock-solid.

---

## Prevention Checklist

### Before ANY fwconsole operation:
- [ ] Snapshot taken
- [ ] Backup database
- [ ] Document current state
- [ ] Verify module is not core dependency

### Never Run These Commands:
```bash
# NEVER DO THIS
fwconsole ma uninstall framework
fwconsole ma uninstall core
fwconsole ma disable framework
```

### Safe Recovery Path:
1. Restore from snapshot
2. If no snapshot: rebuild from scratch
3. Never try to "fix" a broken framework

---

## This Build's Approach

Our new Docker-based system avoids these issues by:
- ✅ Containerized isolation
- ✅ Easy snapshots via Docker volumes
- ✅ Infrastructure as code
- ✅ One-command rebuild
- ✅ No manual module management
- ✅ Database in separate container

**Recovery time:** 10 minutes vs hours of debugging

---

## 🔥 INCIDENT REPORT #3
### Docker Host Mode Network Catastrophe - Database Wipe

**Incident Date:** January 25, 2026

**System:**
- FreePBX 15.0.38 in Docker
- Asterisk 17
- MariaDB 10.11 (separate container)
- Docker Compose bridge network

### Summary (Executive-Level)
While troubleshooting audio issues (no RTP between extensions), the FreePBX container was switched from bridge network to `network_mode: host`. This broke database connectivity, causing FreePBX to perform a fresh install and wipe the asterisk database. All extensions (100, 102) were lost. The system was recovered by reverting to bridge network mode.

### Timeline of Events

**Initial Problem**
- Extensions 100 and 102 registered successfully
- Calls connected but NO AUDIO
- Root cause identified: `direct_media=true` (should be false for Docker/NAT)

**Troubleshooting Attempts**
1. Changed `direct_media=false` in `/etc/asterisk/pjsip.endpoint.conf` ✅
2. Changed external IPs in `/etc/asterisk/pjsip.transports.conf` ✅
3. Restarted Asterisk - settings didn't persist ❌
4. **CRITICAL ERROR:** Changed `docker-compose.yml` to use `network_mode: host` ❌❌❌

**Immediate Effect**
```yaml
# BEFORE (working)
freepbx:
  networks:
    - pbx-network
  environment:
    - DB_HOST=mariadb

# AFTER (broken)
freepbx:
  network_mode: host
  environment:
    - DB_HOST=127.0.0.1  # MariaDB not on localhost!
```

**What Happened:**
- FreePBX container switched to host network
- MariaDB still on bridge network at `172.18.0.x`
- FreePBX couldn't reach database at `127.0.0.1:3306`
- FreePBX detected "no database" and started fresh install
- Fresh install created empty asterisk database
- All extensions, trunks, settings WIPED

**Discovery:**
```bash
sudo ls -la /var/lib/docker/volumes/sidybytech_phone_system_mariadb-data/_data/asterisk/
total 12
drwx------ 2 lxd docker 4096 Jan 25 23:33 .
drwxr-xr-x 6 lxd docker 4096 Jan 26 02:35 ..
-rw-rw---- 1 lxd docker   67 Jan 25 23:33 db.opt
```

Only `db.opt` file exists - all tables gone.

### Root Cause

❌ **Critical Mistake:** Using `network_mode: host` for FreePBX while MariaDB on bridge network

**Why This Failed:**
1. `network_mode: host` removes container from Docker networks
2. FreePBX can't reach MariaDB via service name or bridge IP
3. `DB_HOST=127.0.0.1` points to host machine, not MariaDB container
4. FreePBX sees "no database connection"
5. FreePBX runs first-time setup wizard
6. Setup wizard creates fresh empty database
7. All existing data overwritten

### The Real Audio Problem (Unrelated to Docker Networking)

The audio issue was NOT a Docker networking problem. It was:

**Root Cause of No Audio:**
- Phone 100 on `192.168.2.2` (subnet A)
- Phone 102 on `192.168.1.172` (subnet B)
- Different subnets = RTP packets can't route
- `direct_media=true` made phones try to connect directly
- No route between subnets = no audio

**Correct Fix:**
- Move phone 100 to 192.168.1.x network (same subnet as phone 102)
- OR configure routing between 192.168.1.x and 192.168.2.x
- Keep `direct_media=false` in Asterisk
- Keep Docker in bridge mode

**Wrong Fix (What We Did):**
- Changed Docker to host mode ❌
- This doesn't help RTP routing between phones
- This breaks database connectivity
- This wipes the database

### Why Recovery Failed Initially

| Attempted Fix | Why It Failed |
|--------------|---------------|
| Restart containers | Database already wiped |
| Check volumes | Volume exists but empty database |
| Revert docker-compose | Too late - data already gone |
| Look for backups | No backups, no snapshots |

### Impact
- All extensions lost (100, 102)
- All PJSIP configurations lost
- All custom Asterisk settings lost
- System downtime: ~2 hours
- Data loss: Complete (no backups)

### Final Resolution

✅ **Step 1:** Revert `docker-compose.yml` to bridge network
```yaml
freepbx:
  networks:
    - pbx-network
  environment:
    - DB_HOST=mariadb  # Service name, not localhost
```

✅ **Step 2:** Restart containers
```bash
sudo docker-compose down
sudo docker-compose up -d
```

✅ **Step 3:** Recreate extensions from scratch
- Extension 100 (Rob) - PJSIP, direct_media=no
- Extension 102 (Droid) - PJSIP, direct_media=no

✅ **Step 4:** Fix actual audio problem
- Move phone 100 to 192.168.1.x network
- Verify both phones on same subnet
- Test audio

### Key Technical Indicators

**Sign you're about to break everything:**
```yaml
freepbx:
  network_mode: host  # 🚨 DANGER
  environment:
    - DB_HOST=127.0.0.1  # 🚨 WRONG
```

**Correct configuration:**
```yaml
freepbx:
  networks:
    - pbx-network  # ✅ CORRECT
  environment:
    - DB_HOST=mariadb  # ✅ CORRECT (service name)
```

### Permanent Lessons Learned

🔒 **NEVER use `network_mode: host` for FreePBX when database is in separate container**

**Why:**
- Breaks Docker service discovery
- Breaks container networking
- Requires manual IP management
- No benefit for audio issues
- High risk of data loss

🔒 **Audio issues are NOT Docker networking issues**

**Audio problems are caused by:**
- Phone subnet mismatches
- `direct_media=true` (should be false)
- Firewall blocking RTP ports
- NAT configuration issues

**Audio problems are NOT caused by:**
- Docker bridge vs host mode
- Container networking
- Docker Compose configuration

🔒 **Always take snapshots before network changes**

**Before changing docker-compose.yml:**
```bash
# Backup database
docker exec pbx-mariadb mysqldump -u root -p asterisk > backup.sql

# Or backup entire volumes
docker-compose down
tar -czf backup.tar.gz /var/lib/docker/volumes/sidybytech_phone_system_*
docker-compose up -d
```

### Prevention Checklist

#### Before ANY Docker network changes:
- [ ] Snapshot VM (if virtualized)
- [ ] Backup database: `mysqldump asterisk`
- [ ] Backup Docker volumes
- [ ] Document current working state
- [ ] Test in dev environment first

#### Never Do These:
```yaml
# NEVER DO THIS with external database
freepbx:
  network_mode: host
  environment:
    - DB_HOST=127.0.0.1
```

#### Always Do These:
```yaml
# ALWAYS DO THIS
freepbx:
  networks:
    - pbx-network
  environment:
    - DB_HOST=mariadb  # Use service name
```

### Audio Troubleshooting Order (Correct)

1. **Check phone network:** Same subnet?
2. **Check Asterisk settings:** `direct_media=false`?
3. **Check RTP ports:** 10000-10200 open?
4. **Check NAT:** `force_rport=yes`, `rewrite_contact=yes`?
5. **Check codecs:** Both phones using same codec?
6. **NEVER:** Change Docker networking

### This Build's New Approach

To prevent this from happening again:

✅ **Automated backups:**
```bash
# Add to cron
0 2 * * * docker exec pbx-mariadb mysqldump -u root -p${MYSQL_ROOT_PASSWORD} asterisk > /backup/asterisk-$(date +\%Y\%m\%d).sql
```

✅ **Pre-change snapshots:**
- Always backup before config changes
- Test in dev environment
- Document rollback procedure

✅ **Network validation:**
- Keep FreePBX on bridge network
- Use service names for DB_HOST
- Never use host mode with external database

✅ **Audio troubleshooting:**
- Check phone subnets FIRST
- Fix network routing, not Docker
- Keep Docker simple

**Recovery time:** 10 minutes to fix Docker config, 5 minutes to recreate 2 extensions

**Data loss:** Complete (no backups available)

**Lesson:** Snapshots aren't optional. They're mandatory.

---

## Combined Lessons Learned (Updated)

### 1️⃣ Snapshot BEFORE:
- Module changes
- Permission changes
- fwconsole operations
- **Docker network changes** ⭐ NEW
- **ANY docker-compose.yml edits** ⭐ NEW

### 2️⃣ Never uninstall:
- framework
- core
- sip
- settings
- voicemail

### 3️⃣ Never use host mode:
- When database is in separate container
- To "fix" audio issues
- Without understanding the implications
- Without backups

### 4️⃣ Audio troubleshooting order:
1. Check phone subnets (same network?)
2. Check `direct_media=false`
3. Check RTP ports open
4. Check NAT settings
5. NEVER change Docker networking

### 5️⃣ If you see:
```
Class 'FreePBX' not found
```
➡️ **Stop immediately. Rebuild.**

```yaml
network_mode: host
```
➡️ **Stop immediately. Revert.**

### 6️⃣ Backup strategy:
- Daily database dumps
- Weekly volume backups
- Before ANY config changes
- Test restore procedure

---

## Final Takeaway (Plain English)

**What happened:**
Tried to fix audio by changing Docker networking. Docker networking wasn't the problem. Change broke database connection. Database got wiped. Lost everything.

**What we learned:**
- Audio issues = phone network issues, not Docker issues
- Host mode = dangerous with external database
- Backups = not optional
- Test changes in dev first

**What's different now:**
- Docker config locked down
- Backup procedures in place
- Audio troubleshooting checklist
- Never touching network mode again

This is the kind of mistake you only make once. Now we know better.
