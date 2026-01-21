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
