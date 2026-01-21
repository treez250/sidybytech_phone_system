#!/bin/bash
# Billing Cron Job - Run daily to process CDRs and update balances

MYSQL_USER="asteriskuser"
MYSQL_PASS="${MYSQL_PASSWORD}"
MYSQL_DB="asterisk"
LOG_FILE="/var/log/asterisk/billing.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

log "Starting billing process..."

# Process unbilled CDRs
mysql -u $MYSQL_USER -p$MYSQL_PASS $MYSQL_DB <<EOF
-- Calculate costs for calls
INSERT INTO call_logs (customer_id, src, dst, duration, billsec, disposition, cost, created_at)
SELECT 
    c.customer_id,
    cdr.src,
    cdr.dst,
    cdr.duration,
    cdr.billsec,
    cdr.disposition,
    ROUND((cdr.billsec / 60.0) * COALESCE(rd.rate_per_minute, 0.01), 6) as cost,
    cdr.calldate
FROM cdr
LEFT JOIN customers c ON cdr.accountcode = c.endpoint
LEFT JOIN rate_deck rd ON LEFT(cdr.dst, LENGTH(rd.destination_prefix)) = rd.destination_prefix
WHERE cdr.calldate >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    AND cdr.disposition = 'ANSWERED'
    AND NOT EXISTS (
        SELECT 1 FROM call_logs cl 
        WHERE cl.src = cdr.src 
        AND cl.dst = cdr.dst 
        AND cl.created_at = cdr.calldate
    )
ORDER BY rd.destination_prefix DESC;

-- Update customer balances
UPDATE customer_accounts ca
SET balance = balance - (
    SELECT COALESCE(SUM(cost), 0)
    FROM call_logs cl
    WHERE cl.customer_id = ca.customer_id
    AND cl.created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
);

-- Log billing summary
INSERT INTO system_events (event_type, severity, message, details)
SELECT 
    'billing_processed',
    'info',
    CONCAT('Processed ', COUNT(*), ' calls'),
    JSON_OBJECT(
        'total_calls', COUNT(*),
        'total_revenue', SUM(cost),
        'date', CURDATE()
    )
FROM call_logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY);
EOF

log "Billing process completed"

# Send low balance alerts
mysql -u $MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -N -e "
SELECT c.email, c.company_name, ca.balance 
FROM customers c
JOIN customer_accounts ca ON c.customer_id = ca.customer_id
WHERE ca.balance < 10.0 AND c.active = 1
" | while read email company balance; do
    log "Low balance alert for $company: $balance"
    # Send email notification
    # echo "Your account balance is low: \$$balance" | mail -s "Low Balance Alert" $email
done

exit 0
