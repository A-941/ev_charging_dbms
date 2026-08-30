-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 05_dql_basic_advanced.sql
-- Topic: DQL (Data Query Language) - SELECT Queries
-- (WHERE, AGGREGATES, IN, LIKE, DISTINCT, ORDER BY, LIMIT/OFFSET, GROUP BY, HAVING)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SELECT WITH WHERE CLAUSE
-- Find all charging ports that are currently 'Available' and offer fast 'CCS2' charging
-- ----------------------------------------------------------------------------
SELECT port_id, station_id, connector_type, status
FROM PORTS
WHERE status = 'Available' AND connector_type = 'CCS2';


-- ----------------------------------------------------------------------------
-- 2. AGGREGATE FUNCTIONS (COUNT, SUM, AVG, MIN, MAX)
-- Calculate network-wide operational and financial summaries
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(session_id) AS total_completed_sessions,
    ROUND(SUM(energy_kwh), 2) AS total_energy_dispensed_kwh,
    ROUND(AVG(energy_kwh), 2) AS avg_energy_per_session_kwh,
    MIN(energy_kwh) AS min_session_energy,
    MAX(energy_kwh) AS max_session_energy
FROM CHARGING_SESSIONS;


-- ----------------------------------------------------------------------------
-- 3. IN, LIKE, AND DISTINCT OPERATORS
-- ----------------------------------------------------------------------------

-- A. IN Operator: Find vehicles requiring high-speed DC fast charging connectors
SELECT vehicle_id, user_id, type, connector_needed
FROM VEHICLES
WHERE connector_needed IN ('CCS2', 'Tesla Supercharger');

-- B. LIKE Operator: Search for complaints containing hardware or connector issues
SELECT complaint_id, port_id, issue, status
FROM COMPLAINTS
WHERE issue LIKE '%connector%' OR issue LIKE '%cable%';

-- C. DISTINCT Operator: Retrieve all unique combinations of vehicle types and required connectors
SELECT DISTINCT type, connector_needed
FROM VEHICLES
ORDER BY type;


-- ----------------------------------------------------------------------------
-- 4. ORDER BY, LIMIT, AND OFFSET (PAGINATION)
-- Retrieve top 5 most expensive charging sessions (Page 1 and Page 2)
-- ----------------------------------------------------------------------------

-- Page 1: Top 5 Highest Payments
SELECT payment_id, booking_id, amount
FROM PAYMENTS
ORDER BY amount DESC
LIMIT 5 OFFSET 0;

-- Page 2: Next 5 Payments (Rank 6 to 10)
SELECT payment_id, booking_id, amount
FROM PAYMENTS
ORDER BY amount DESC
LIMIT 5 OFFSET 5;


-- ----------------------------------------------------------------------------
-- 5. GROUP BY
-- Calculate total energy dispensed, session count, and total revenue per connector type
-- ----------------------------------------------------------------------------
SELECT 
    p.connector_type,
    COUNT(cs.session_id) AS session_count,
    ROUND(SUM(cs.energy_kwh), 2) AS total_kwh,
    ROUND(SUM(pay.amount), 2) AS total_revenue
FROM PORTS p
JOIN BOOKINGS b ON p.port_id = b.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
GROUP BY p.connector_type
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- 6. GROUP BY WITH HAVING CLAUSE
-- ----------------------------------------------------------------------------

-- A. Find high-performing stations having at least 3 reviews and an average rating >= 4.0
SELECT 
    s.station_id,
    op.company_name AS operator_name,
    COUNT(r.review_id) AS review_count,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM STATIONS s
JOIN OPERATORS op ON s.operator_id = op.operator_id
JOIN REVIEWS r ON s.station_id = r.station_id
GROUP BY s.station_id, op.company_name
HAVING COUNT(r.review_id) >= 3 AND AVG(r.rating) >= 4.0
ORDER BY average_rating DESC, review_count DESC;

-- B. Find ports with 2 or more logged complaints
SELECT 
    port_id,
    COUNT(complaint_id) AS total_complaints,
    SUM(CASE WHEN status IN ('Open', 'In Progress') THEN 1 ELSE 0 END) AS active_complaints
FROM COMPLAINTS
GROUP BY port_id
HAVING COUNT(complaint_id) >= 2
ORDER BY total_complaints DESC;
