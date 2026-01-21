-- Carrier-Level Database Schema

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    endpoint VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_endpoint (endpoint),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Customer accounts and billing
CREATE TABLE IF NOT EXISTS customer_accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    balance DECIMAL(10,4) DEFAULT 0.0000,
    credit_limit DECIMAL(10,4) DEFAULT 0.0000,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    last_billing_date DATE,
    next_billing_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- DIDs (Direct Inward Dialing numbers)
CREATE TABLE IF NOT EXISTS dids (
    did_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    did_number VARCHAR(20) UNIQUE NOT NULL,
    country_code VARCHAR(5),
    monthly_cost DECIMAL(10,4) DEFAULT 0.0000,
    per_minute_cost DECIMAL(10,6) DEFAULT 0.000000,
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_did_number (did_number),
    INDEX idx_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Trunks (upstream carriers)
CREATE TABLE IF NOT EXISTS trunks (
    trunk_id INT AUTO_INCREMENT PRIMARY KEY,
    trunk_name VARCHAR(100) UNIQUE NOT NULL,
    trunk_type ENUM('sip','iax2','dahdi') DEFAULT 'sip',
    host VARCHAR(255),
    username VARCHAR(100),
    password VARCHAR(100),
    capacity INT DEFAULT 100,
    current_calls INT DEFAULT 0,
    active TINYINT(1) DEFAULT 1,
    priority INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trunk_name (trunk_name),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Rate deck for pricing
CREATE TABLE IF NOT EXISTS rate_deck (
    rate_id INT AUTO_INCREMENT PRIMARY KEY,
    destination_prefix VARCHAR(20) NOT NULL,
    destination_name VARCHAR(255),
    rate_per_minute DECIMAL(10,6) NOT NULL,
    effective_date DATE,
    expiry_date DATE,
    active TINYINT(1) DEFAULT 1,
    INDEX idx_prefix (destination_prefix),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LCR (Least Cost Routing) routes
CREATE TABLE IF NOT EXISTS lcr_routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    destination_prefix VARCHAR(20) NOT NULL,
    trunk_name VARCHAR(100) NOT NULL,
    prefix VARCHAR(20),
    cost DECIMAL(10,6) NOT NULL,
    priority INT DEFAULT 10,
    active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_destination (destination_prefix),
    INDEX idx_customer (customer_id),
    INDEX idx_cost (cost)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Call Detail Records (CDR)
CREATE TABLE IF NOT EXISTS cdr (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    calldate DATETIME NOT NULL,
    clid VARCHAR(80),
    src VARCHAR(80),
    dst VARCHAR(80),
    dcontext VARCHAR(80),
    channel VARCHAR(80),
    dstchannel VARCHAR(80),
    lastapp VARCHAR(80),
    lastdata VARCHAR(80),
    duration INT DEFAULT 0,
    billsec INT DEFAULT 0,
    disposition VARCHAR(45),
    amaflags INT DEFAULT 0,
    accountcode VARCHAR(20),
    uniqueid VARCHAR(150),
    userfield VARCHAR(255),
    peeraccount VARCHAR(80),
    linkedid VARCHAR(150),
    sequence INT,
    INDEX idx_calldate (calldate),
    INDEX idx_src (src),
    INDEX idx_dst (dst),
    INDEX idx_accountcode (accountcode),
    INDEX idx_uniqueid (uniqueid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Call logs with billing information
CREATE TABLE IF NOT EXISTS call_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    src VARCHAR(80),
    dst VARCHAR(80),
    duration INT DEFAULT 0,
    billsec INT DEFAULT 0,
    disposition VARCHAR(45),
    cost DECIMAL(10,6) DEFAULT 0.000000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    INDEX idx_customer (customer_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Fraud detection
CREATE TABLE IF NOT EXISTS fraud_detection (
    fraud_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    fraud_type VARCHAR(50),
    fraud_score INT DEFAULT 0,
    details TEXT,
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    INDEX idx_customer (customer_id),
    INDEX idx_check_date (check_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Blacklist
CREATE TABLE IF NOT EXISTS blacklist (
    blacklist_id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    reason VARCHAR(255),
    added_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_phone (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- System events log
CREATE TABLE IF NOT EXISTS system_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50),
    severity ENUM('info','warning','error','critical') DEFAULT 'info',
    message TEXT,
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
