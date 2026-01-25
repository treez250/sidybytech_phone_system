#!/usr/bin/env python3
"""
Sync FreePBX CDR data to Snowflake
Reads CDR records from MariaDB and pushes to Snowflake
"""

import os
import sys
import mysql.connector
import snowflake.connector
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST', 'pbx-mariadb')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'asterisk')

SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'FREEPBX_CDR')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA', 'CDR_DATA')

# Sync window (how far back to look for new records)
SYNC_HOURS = int(os.getenv('SYNC_HOURS', '24'))


def connect_mysql():
    """Connect to MariaDB"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        logger.info("Connected to MariaDB")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to MariaDB: {e}")
        sys.exit(1)


def connect_snowflake():
    """Connect to Snowflake"""
    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
        logger.info("Connected to Snowflake")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to Snowflake: {e}")
        sys.exit(1)


def get_cdr_records(mysql_conn):
    """Fetch CDR records from MariaDB"""
    cursor = mysql_conn.cursor(dictionary=True)
    
    # Get records from last SYNC_HOURS hours
    sync_time = datetime.now() - timedelta(hours=SYNC_HOURS)
    
    query = """
        SELECT 
            calldate, clid, src, dst, dcontext, channel, dstchannel,
            lastapp, lastdata, duration, billsec, disposition, amaflags,
            accountcode, uniqueid, userfield, peeraccount, linkedid, sequence,
            cnum, cnam, outbound_cnum, outbound_cnam, dst_cnam
        FROM cdr
        WHERE calldate >= %s
        ORDER BY calldate DESC
    """
    
    cursor.execute(query, (sync_time,))
    records = cursor.fetchall()
    cursor.close()
    
    logger.info(f"Fetched {len(records)} CDR records from MariaDB")
    return records


def sync_to_snowflake(snowflake_conn, records):
    """Insert CDR records into Snowflake"""
    if not records:
        logger.info("No records to sync")
        return
    
    cursor = snowflake_conn.cursor()
    
    # Use MERGE to avoid duplicates (based on uniqueid)
    merge_query = """
        MERGE INTO cdr AS target
        USING (
            SELECT 
                %s as calldate, %s as clid, %s as src, %s as dst,
                %s as dcontext, %s as channel, %s as dstchannel,
                %s as lastapp, %s as lastdata, %s as duration,
                %s as billsec, %s as disposition, %s as amaflags,
                %s as accountcode, %s as uniqueid, %s as userfield,
                %s as peeraccount, %s as linkedid, %s as sequence,
                %s as cnum, %s as cnam, %s as outbound_cnum,
                %s as outbound_cnam, %s as dst_cnam
        ) AS source
        ON target.uniqueid = source.uniqueid
        WHEN NOT MATCHED THEN
            INSERT (
                calldate, clid, src, dst, dcontext, channel, dstchannel,
                lastapp, lastdata, duration, billsec, disposition, amaflags,
                accountcode, uniqueid, userfield, peeraccount, linkedid, sequence,
                cnum, cnam, outbound_cnum, outbound_cnam, dst_cnam
            )
            VALUES (
                source.calldate, source.clid, source.src, source.dst,
                source.dcontext, source.channel, source.dstchannel,
                source.lastapp, source.lastdata, source.duration,
                source.billsec, source.disposition, source.amaflags,
                source.accountcode, source.uniqueid, source.userfield,
                source.peeraccount, source.linkedid, source.sequence,
                source.cnum, source.cnam, source.outbound_cnum,
                source.outbound_cnam, source.dst_cnam
            )
    """
    
    synced = 0
    for record in records:
        try:
            cursor.execute(merge_query, (
                record['calldate'], record['clid'], record['src'], record['dst'],
                record['dcontext'], record['channel'], record['dstchannel'],
                record['lastapp'], record['lastdata'], record['duration'],
                record['billsec'], record['disposition'], record['amaflags'],
                record['accountcode'], record['uniqueid'], record['userfield'],
                record['peeraccount'], record['linkedid'], record['sequence'],
                record['cnum'], record['cnam'], record['outbound_cnum'],
                record['outbound_cnam'], record['dst_cnam']
            ))
            synced += 1
        except Exception as e:
            logger.error(f"Failed to sync record {record['uniqueid']}: {e}")
    
    cursor.close()
    logger.info(f"Synced {synced} records to Snowflake")


def main():
    """Main sync process"""
    logger.info("Starting CDR sync to Snowflake")
    
    # Validate configuration
    if not all([MYSQL_PASSWORD, SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD]):
        logger.error("Missing required environment variables")
        sys.exit(1)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    snowflake_conn = connect_snowflake()
    
    try:
        # Fetch and sync records
        records = get_cdr_records(mysql_conn)
        sync_to_snowflake(snowflake_conn, records)
        
        logger.info("Sync completed successfully")
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)
    finally:
        mysql_conn.close()
        snowflake_conn.close()


if __name__ == "__main__":
    main()
