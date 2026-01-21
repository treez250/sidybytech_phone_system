#!/bin/bash
# Fraud Alert Script

CALLER=$1
CUSTOMER_ID=$2
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log to file
echo "[$TIMESTAMP] FRAUD ALERT: Caller=$CALLER, Customer=$CUSTOMER_ID" >> /var/log/asterisk/fraud.log

# Insert into database
mysql -u asteriskuser -p${MYSQL_PASSWORD} asterisk <<EOF
INSERT INTO fraud_detection (customer_id, fraud_type, fraud_score, details, check_date)
VALUES ('$CUSTOMER_ID', 'high_call_rate', 100, 'Caller: $CALLER exceeded rate limit', NOW());
EOF

# Send email alert (configure with your SMTP settings)
# echo "Fraud detected for customer $CUSTOMER_ID from $CALLER at $TIMESTAMP" | \
#   mail -s "FRAUD ALERT" security@yourcompany.com

# Optional: Send webhook notification
# curl -X POST https://your-monitoring-system.com/alerts \
#   -H "Content-Type: application/json" \
#   -d "{\"type\":\"fraud\",\"customer\":\"$CUSTOMER_ID\",\"caller\":\"$CALLER\",\"timestamp\":\"$TIMESTAMP\"}"

exit 0
