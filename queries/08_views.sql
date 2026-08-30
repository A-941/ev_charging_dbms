-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 08_views.sql
-- Topic: Standard Views & Materialized Views (Analytics & Abstraction)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. VIEW: Real-Time Station Availability & Health Overview
-- Provides instant station status, connector counts, available ports, and average ratings
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_station_live_status;

CREATE VIEW v_station_live_status AS
SELECT 
    s.station_id,
    op.company_name AS operator_name,
    s.latitude,
    s.longitude,
    COUNT(p.port_id) AS total_ports,
    SUM(CASE WHEN p.status = 'Available' THEN 1 ELSE 0 END) AS available_ports,
    SUM(CASE WHEN p.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_ports,
    SUM(CASE WHEN p.status IN ('Faulted', 'Under Maintenance') THEN 1 ELSE 0 END) AS offline_ports,
    ROUND(AVG(r.rating), 1) AS avg_rating,
    COUNT(DISTINCT r.review_id) AS total_reviews
FROM STATIONS s
JOIN OPERATORS op ON s.operator_id = op.operator_id
LEFT JOIN PORTS p ON s.station_id = p.station_id
LEFT JOIN REVIEWS r ON s.station_id = r.station_id
GROUP BY s.station_id, op.company_name, s.latitude, s.longitude;


-- ----------------------------------------------------------------------------
-- 2. VIEW: User Booking & Billing History
-- Provides end-user dashboard summary
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_user_charging_history;

CREATE VIEW v_user_charging_history AS
SELECT 
    b.booking_id,
    u.user_id,
    u.name AS customer_name,
    u.phone AS customer_phone,
    s.station_id,
    op.company_name AS operator_name,
    p.connector_type,
    b.start_time,
    b.status AS booking_status,
    cs.energy_kwh,
    cs.end_time,
    pay.amount AS total_amount_paid
FROM BOOKINGS b
JOIN USERS u ON b.user_id = u.user_id
JOIN PORTS p ON b.port_id = p.port_id
JOIN STATIONS s ON p.station_id = s.station_id
JOIN OPERATORS op ON s.operator_id = op.operator_id
LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
LEFT JOIN PAYMENTS pay ON b.booking_id = pay.booking_id;


-- ----------------------------------------------------------------------------
-- 3. VIEW: Operator Monthly Performance & Revenue Summary
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_operator_financial_summary;

CREATE VIEW v_operator_financial_summary AS
SELECT 
    op.operator_id,
    op.company_name,
    COUNT(DISTINCT s.station_id) AS stations_managed,
    COUNT(DISTINCT p.port_id) AS total_ports_deployed,
    COUNT(DISTINCT cs.session_id) AS total_completed_sessions,
    ROUND(COALESCE(SUM(cs.energy_kwh), 0.0), 2) AS total_energy_sold_kwh,
    ROUND(COALESCE(SUM(pay.amount), 0.0), 2) AS gross_revenue
FROM OPERATORS op
LEFT JOIN STATIONS s ON op.operator_id = s.operator_id
LEFT JOIN PORTS p ON s.station_id = p.station_id
LEFT JOIN BOOKINGS b ON p.port_id = b.port_id
LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
LEFT JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
GROUP BY op.operator_id, op.company_name;


-- ----------------------------------------------------------------------------
-- 4. MATERIALIZED VIEW IMPLEMENTATION
-- In PostgreSQL:
-- CREATE MATERIALIZED VIEW mv_station_revenue_leaderboard AS
-- SELECT station_id, SUM(amount) AS total_revenue
-- FROM v_user_charging_history
-- GROUP BY station_id;
-- REFRESH MATERIALIZED VIEW mv_station_revenue_leaderboard;
--
-- In Cross-RDBMS (Table Cache Pattern with Refresh):
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS MV_STATION_METRICS (
    station_id INT PRIMARY KEY,
    total_energy_kwh DECIMAL(10, 2),
    total_revenue DECIMAL(10, 2),
    last_refreshed TIMESTAMP
);
