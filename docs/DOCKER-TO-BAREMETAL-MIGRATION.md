# Migrating from Docker FreePBX to Bare Metal

## Why Migrate?

Docker adds latency and complexity to RTP media processing. For production translation services with ExternalMedia(), bare metal is required.

## Migration Strategy

### Option 1: Fresh Install (Recommended)

1. Export your current extensions and settings from Docker FreePBX
2. Install bare metal FreePBX on the same server
3. Import extensions and settings
4. Update phone configurations to new IP (if changed)

### Option 2: Parallel Installation

1. Install bare metal FreePBX on a different IP
2. Configure and test
3. Switch phones over
4. Decommission Docker

## Step-by-Step Migration

### 1. Backup Current Docker FreePBX

```bash
# Backup FreePBX database
docker exec pbx-mariadb mysqldump -uroot -p00rdjXDOZl8h10T5sWYQ asterisk > /root/freepbx-backup.sql

# Backup CDR database
docker exec pbx-mariadb mysqldump -uroot -p00rdjXDOZl8h10T5sWYQ asteriskcdrdb > /root/freepbx-cdr-backup.sql

# Export extensions (from FreePBX web UI)
# Admin → Config Edit → Export
```

### 2. Stop Docker FreePBX

```bash
cd /root/sidybytech_phone_system
docker-compose down
```

### 3. Install Bare Metal FreePBX

```bash
cd /root/sidybytech_phone_system
chmod +x setup-freepbx-baremetal.sh
./setup-freepbx-baremetal.sh
```

This takes 20-30 minutes (Asterisk compilation).

### 4. Access FreePBX Web Interface

```
http://192.168.1.142
```

Complete the initial setup wizard.

### 5. Configure PJSIP Settings

Follow **docs/FREEPBX-BARE-METAL-SETUP.md** exactly:

- Direct Media: **No**
- RTP Symmetric: **Yes**
- RTP Port Range: **10000-20000**
- Codec: **PCMU only**

### 6. Restore Extensions

**Option A: Manual (Recommended for 2 extensions)**

Create extensions 100 and 101 manually with same passwords.

**Option B: Database Restore**

```bash
mysql -uroot asterisk < /root/freepbx-backup.sql
fwconsole reload
```

### 7. Update Phone Configurations

If IP changed, update phones:
- Server: 192.168.1.142
- Port: 5060
- Transport: UDP

### 8. Validate RTP

```bash
# Check Asterisk is listening
ss -lunp | grep asterisk

# Make a test call, then check RTP
tcpdump -n -i any udp and portrange 10000-20000
```

You should see:
```
UDP, length ~160
```

### 9. Test Audio

- Call from extension 100 to 101
- Verify audio both directions
- Check RTP in tcpdump

### 10. Restore CDR Data (Optional)

```bash
mysql -uroot asteriskcdrdb < /root/freepbx-cdr-backup.sql
```

## Validation Checklist

✅ FreePBX web UI accessible
✅ Extensions registered
✅ Audio works both directions
✅ RTP visible in tcpdump (length ~160)
✅ No Docker networking involved
✅ Asterisk listening on ports 10000-20000

## Rollback Plan

If something goes wrong:

```bash
cd /root/sidybytech_phone_system
docker-compose up -d
```

Your Docker setup is preserved and can be restarted anytime.

## After Migration

Once bare metal is working:

1. Remove Docker containers (optional):
   ```bash
   docker-compose down -v
   ```

2. Proceed with translation service setup:
   - Add ExternalMedia() dialplan
   - Install translation service
   - Configure Azure credentials
   - Test translation

## Timeline

- Backup: 5 minutes
- Installation: 20-30 minutes
- Configuration: 10 minutes
- Testing: 10 minutes

**Total: ~1 hour**

## Support

If you hit issues:
1. Check Asterisk logs: `tail -f /var/log/asterisk/full`
2. Check Apache logs: `tail -f /var/log/apache2/error.log`
3. Verify services: `systemctl status asterisk apache2 mariadb`
