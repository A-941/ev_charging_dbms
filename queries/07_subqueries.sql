-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 07_subqueries.sql
-- Topic: Nested Subqueries (Scalar, Multi-Row, Correlated, EXISTS, ANY, ALL)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SCALAR SUBQUERY (Single-Value Subquery in SELECT)
-- Show each user with their total bookings count and lifetime spending calculated inline
-- ----------------------------------------------------------------------------
SELECT 
    u.user_id,
    u.name,
    (SELECT COUNT(*) FROM BOOKINGS b WHERE b.user_id = u.user_id) AS total_bookings,
    (SELECT COALESCE(SUM(p.amount), 0.0) 
     FROM PAYMENTS p 
     JOIN BOOKINGS b ON p.booking_id = b.booking_id 
     WHERE b.user_id = u.user_id) AS total_spent
FROM USERS u
ORDER BY total_spent DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 2. SINGLE-ROW SUBQUERY IN WHERE CLAUSE
-- Find all charging ports whose electricity tariff is higher than the network average
-- ----------------------------------------------------------------------------
SELECT 
    pr.price_id,
    pr.port_id,
    p.connector_type,
    pr.rate_per_kwh
FROM PRICES pr
JOIN PORTS p ON pr.port_id = p.port_id
WHERE pr.rate_per_kwh > (SELECT AVG(rate_per_kwh) FROM PRICES)
ORDER BY pr.rate_per_kwh DESC;


-- ----------------------------------------------------------------------------
-- 3. MULTI-ROW SUBQUERY WITH IN / NOT IN
-- Find all stations that currently have at least one port under 'Faulted' or 'Under Maintenance'
-- ----------------------------------------------------------------------------
SELECT station_id, operator_id, latitude, longitude
FROM STATIONS
WHERE station_id IN (
    SELECT DISTINCT station_id 
    FROM PORTS 
    WHERE status IN ('Faulted', 'Under Maintenance')
);


-- ----------------------------------------------------------------------------
-- 4. CORRELATED SUBQUERY
-- Find charging sessions where energy consumed exceeded the average consumption for that specific port
-- ----------------------------------------------------------------------------
SELECT 
    cs.session_id,
    cs.booking_id,
    b.port_id,
    cs.energy_kwh
FROM CHARGING_SESSIONS cs
JOIN BOOKINGS b ON cs.booking_id = b.booking_id
WHERE cs.energy_kwh > (
    SELECT AVG(cs_inner.energy_kwh)
    FROM CHARGING_SESSIONS cs_inner
    JOIN BOOKINGS b_inner ON cs_inner.booking_id = b_inner.booking_id
    WHERE b_inner.port_id = b.port_id
)
ORDER BY b.port_id, cs.energy_kwh DESC;


-- ----------------------------------------------------------------------------
-- 5. EXISTS AND NOT EXISTS SUBQUERIES
-- Find reliable stations that have NEVER had any complaints filed on any of their ports
-- ----------------------------------------------------------------------------
SELECT s.station_id, op.company_name, s.latitude, s.longitude
FROM STATIONS s
JOIN OPERATORS op ON s.operator_id = op.operator_id
WHERE NOT EXISTS (
    SELECT 1 
    FROM PORTS p
    JOIN COMPLAINTS c ON p.port_id = c.port_id
    WHERE p.station_id = s.station_id
);


-- ----------------------------------------------------------------------------
-- 6. ANY AND ALL OPERATORS (Standard SQL Dialect)
-- ----------------------------------------------------------------------------

-- A. Greater than ANY: Find ports with rate higher than at least one Type 2 port rate
-- (Standard ANSI SQL: `WHERE rate_per_kwh > ANY (SELECT rate_per_kwh FROM ...)` / In SQLite: `> (SELECT MIN(...))`)
SELECT pr.port_id, p.connector_type, pr.rate_per_kwh
FROM PRICES pr
JOIN PORTS p ON pr.port_id = p.port_id
WHERE pr.rate_per_kwh > (
    SELECT MIN(rate_per_kwh) 
    FROM PRICES pr2 
    JOIN PORTS p2 ON pr2.port_id = p2.port_id 
    WHERE p2.connector_type = 'Type 2'
);

-- B. Greater than ALL: Find ports whose rate is higher than EVERY Type 2 port rate
SELECT pr.port_id, p.connector_type, pr.rate_per_kwh
FROM PRICES pr
JOIN PORTS p ON pr.port_id = p.port_id
WHERE pr.rate_per_kwh > (
    SELECT MAX(rate_per_kwh) 
    FROM PRICES pr2 
    JOIN PORTS p2 ON pr2.port_id = p2.port_id 
    WHERE p2.connector_type = 'Type 2'
);
