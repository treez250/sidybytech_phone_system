-- Sample data for testing

-- Insert sample customer
INSERT INTO customers (company_name, endpoint, email, phone, active) VALUES
('Test Company Inc', 'test-customer-001', 'admin@testcompany.com', '+15551234567', 1),
('Demo Corp', 'demo-customer-001', 'contact@democorp.com', '+15559876543', 1);

-- Insert customer accounts
INSERT INTO customer_accounts (customer_id, balance, credit_limit, currency) VALUES
(1, 100.0000, 500.0000, 'USD'),
(2, 250.0000, 1000.0000, 'USD');

-- Insert sample DIDs
INSERT INTO dids (customer_id, did_number, country_code, monthly_cost, per_minute_cost, active) VALUES
(1, '+15551234567', '+1', 5.0000, 0.010000, 1),
(2, '+15559876543', '+1', 5.0000, 0.010000, 1);

-- Insert sample trunks
INSERT INTO trunks (trunk_name, trunk_type, host, username, password, capacity, active, priority) VALUES
('trunk-primary', 'sip', 'sip.carrier1.com', 'username1', 'password1', 100, 1, 1),
('trunk-backup', 'sip', 'sip.carrier2.com', 'username2', 'password2', 50, 1, 2),
('trunk-premium', 'sip', 'sip.premiumcarrier.com', 'username3', 'password3', 200, 1, 1);

-- Insert sample rate deck (US rates)
INSERT INTO rate_deck (destination_prefix, destination_name, rate_per_minute, effective_date, active) VALUES
('1', 'USA/Canada', 0.010000, CURDATE(), 1),
('44', 'United Kingdom', 0.025000, CURDATE(), 1),
('49', 'Germany', 0.030000, CURDATE(), 1),
('33', 'France', 0.028000, CURDATE(), 1),
('61', 'Australia', 0.035000, CURDATE(), 1),
('86', 'China', 0.040000, CURDATE(), 1),
('91', 'India', 0.045000, CURDATE(), 1),
('52', 'Mexico', 0.020000, CURDATE(), 1);

-- Insert LCR routes
INSERT INTO lcr_routes (customer_id, destination_prefix, trunk_name, prefix, cost, priority, active) VALUES
(1, '1', 'trunk-primary', '', 0.008000, 1, 1),
(1, '44', 'trunk-primary', '', 0.020000, 1, 1),
(1, '1', 'trunk-backup', '', 0.009000, 2, 1),
(2, '1', 'trunk-premium', '', 0.007000, 1, 1),
(2, '44', 'trunk-premium', '', 0.018000, 1, 1);

-- Insert sample system event
INSERT INTO system_events (event_type, severity, message) VALUES
('system_start', 'info', 'System initialized with sample data');
