# Snowflake CDR Sync Setup

## Overview

This syncs your FreePBX CDR data to Snowflake for advanced analytics, data warehousing, and BI tools.

## Architecture

```
FreePBX → MariaDB → Python Sync Script → Snowflake → Grafana/BI Tools
```

## Prerequisites

✅ Snowflake account (completed)
✅ Database created: `FREEPBX_CDR` (completed)
✅ Schema created: `CDR_DATA` (completed)
✅ Table created: `cdr` (completed)

## Configuration

### 1. Create Snowflake Configuration File

On your Debian server:

```bash
cd /root/sidybytech_phone_system/scripts
cp snowflake-sync.env.example snowflake-sync.env
nano snowflake-sync.env
```

### 2. Fill in Your Snowflake Details

```bash
# MySQL/MariaDB Configuration
MYSQL_HOST=pbx-mariadb
MYSQL_USER=root
MYSQL_PASSWORD=00rdjXDOZl8h10T5sWYQ
MYSQL_DATABASE=asterisk

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=pkaevew-uy86597
SNOWFLAKE_USER=YOUR_SNOWFLAKE_USERNAME
SNOWFLAKE_PASSWORD=YOUR_SNOWFLAKE_PASSWORD
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=FREEPBX_CDR
SNOWFLAKE_SCHEMA=CDR_DATA

# Sync Settings (sync last 24 hours of data)
SYNC_HOURS=24
```

### 3. Install Python Dependencies

```bash
# Install Python and pip
apt install -y python3 python3-pip

# Install required packages
pip3 install -r scripts/requirements-snowflake.txt
```

### 4. Test the Sync

```bash
# Load environment variables
source scripts/snowflake-sync.env

# Run sync manually
python3 scripts/sync-to-snowflake.py
```

You should see:
```
INFO - Starting CDR sync to Snowflake
INFO - Connected to MariaDB
INFO - Connected to Snowflake
INFO - Fetched X CDR records from MariaDB
INFO - Synced X records to Snowflake
INFO - Sync completed successfully
```

### 5. Verify Data in Snowflake

In Snowflake, run:

```sql
USE DATABASE FREEPBX_CDR;
USE SCHEMA CDR_DATA;

SELECT COUNT(*) FROM cdr;

SELECT * FROM cdr ORDER BY calldate DESC LIMIT 10;
```

You should see your CDR data!

## Automated Sync (Cron Job)

### Option 1: Hourly Sync

```bash
# Create cron job
crontab -e

# Add this line (sync every hour at minute 5)
5 * * * * cd /root/sidybytech_phone_system && source scripts/snowflake-sync.env && python3 scripts/sync-to-snowflake.py >> /var/log/snowflake-sync.log 2>&1
```

### Option 2: Daily Sync

```bash
# Sync once per day at 2 AM
0 2 * * * cd /root/sidybytech_phone_system && source scripts/snowflake-sync.env && python3 scripts/sync-to-snowflake.py >> /var/log/snowflake-sync.log 2>&1
```

### Check Sync Logs

```bash
tail -f /var/log/snowflake-sync.log
```

## Connect Grafana to Snowflake

### Option 1: Via ODBC (Advanced)

Requires installing Snowflake ODBC driver and configuring Grafana.

### Option 2: Query Snowflake via API (Recommended)

Use Snowflake's REST API or SQL API to query from Grafana.

### Option 3: Use Snowflake's Built-in Dashboards

Snowflake has native visualization tools you can use directly!

## Snowflake Queries for Analytics

### Call Volume by Day

```sql
SELECT 
    DATE(calldate) as call_date,
    COUNT(*) as total_calls,
    SUM(billsec) as total_seconds,
    ROUND(SUM(billsec)/60.0, 2) as total_minutes
FROM cdr
WHERE calldate >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY DATE(calldate)
ORDER BY call_date DESC;
```

### Top Destinations

```sql
SELECT 
    dst as destination,
    COUNT(*) as call_count,
    SUM(billsec) as total_seconds,
    AVG(billsec) as avg_duration
FROM cdr
WHERE calldate >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY dst
ORDER BY call_count DESC
LIMIT 20;
```

### Call Success Rate

```sql
SELECT 
    disposition,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM cdr
WHERE calldate >= DATEADD(day, -30, CURRENT_DATE())
GROUP BY disposition
ORDER BY count DESC;
```

### Hourly Call Distribution

```sql
SELECT 
    HOUR(calldate) as hour_of_day,
    COUNT(*) as call_count
FROM cdr
WHERE calldate >= DATEADD(day, -7, CURRENT_DATE())
GROUP BY HOUR(calldate)
ORDER BY hour_of_day;
```

## Troubleshooting

### Connection Failed

```bash
# Test MySQL connection
docker exec -it pbx-mariadb mysql -uroot -p00rdjXDOZl8h10T5sWYQ asterisk -e "SELECT COUNT(*) FROM cdr;"

# Test Snowflake connection (in Python)
python3 -c "import snowflake.connector; print('Snowflake module loaded')"
```

### No Records Synced

- Check if CDR data exists in MariaDB
- Verify SYNC_HOURS setting (default 24 hours)
- Check sync logs for errors

### Permission Errors

Make sure your Snowflake user has:
- USAGE on warehouse
- USAGE on database
- USAGE on schema
- INSERT on table

## Next Steps

1. ✅ Set up automated sync (cron job)
2. ✅ Create Snowflake dashboards
3. ✅ Connect BI tools (Tableau, Power BI, etc.)
4. ✅ Set up alerts for unusual patterns
5. ✅ Export data for billing/invoicing

## Cost Optimization

- Snowflake charges for compute (warehouse) time
- Sync during off-peak hours
- Use smaller warehouse for sync (X-Small is fine)
- Suspend warehouse when not in use
- Consider daily sync instead of hourly for cost savings

## Your Snowflake Setup

- **Account:** pkaevew-uy86597
- **Database:** FREEPBX_CDR
- **Schema:** CDR_DATA
- **Table:** cdr
- **Warehouse:** COMPUTE_WH

**All set! Your CDR data will flow to Snowflake for advanced analytics!** 🚀
