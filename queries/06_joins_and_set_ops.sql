-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 06_joins_and_set_ops.sql
-- Topic: Relational JOINs (All Types) & SET Operations (UNION, INTERSECT, EXCEPT)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. INNER JOIN
-- Retrieve complete session receipts: User, Station, Operator, Port, Energy, and Payment
-- ----------------------------------------------------------------------------
SELECT 
    b.booking_id,
    u.name AS user_name,
    u.phone AS user_phone,
    op.company_name AS operator_name,
    s.station_id,
    p.connector_type,
    pr.rate_per_kwh,
    cs.energy_kwh,
    pay.amount AS total_paid
FROM BOOKINGS b
INNER JOIN USERS u ON b.user_id = u.user_id
INNER JOIN PORTS p ON b.port_id = p.port_id
INNER JOIN STATIONS s ON p.station_id = s.station_id
INNER JOIN OPERATORS op ON s.operator_id = op.operator_id
INNER JOIN PRICES pr ON p.port_id = pr.port_id
INNER JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
INNER JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
ORDER BY b.booking_id
LIMIT 10;


-- ----------------------------------------------------------------------------
-- 2. LEFT OUTER JOIN
-- Retrieve all users and their registered vehicles (including users with no vehicle yet)
-- ----------------------------------------------------------------------------
SELECT 
    u.user_id,
    u.name,
    u.phone,
    v.vehicle_id,
    v.type AS vehicle_type,
    v.connector_needed
FROM USERS u
LEFT OUTER JOIN VEHICLES v ON u.user_id = v.user_id
ORDER BY u.user_id;


-- ----------------------------------------------------------------------------
-- 3. RIGHT OUTER JOIN / FULL OUTER JOIN
-- (Demonstrated in PostgreSQL / MySQL 8.0+ / Full relational standard)
-- Find all stations and all reviews, showing stations with no reviews and orphaned reviews if any.
-- In SQLite, simulated using LEFT JOIN unioned with RIGHT JOIN equivalent:
-- ----------------------------------------------------------------------------
SELECT 
    s.station_id,
    s.latitude,
    s.longitude,
    r.review_id,
    r.rating
FROM STATIONS s
LEFT JOIN REVIEWS r ON s.station_id = r.station_id
UNION
SELECT 
    s.station_id,
    s.latitude,
    s.longitude,
    r.review_id,
    r.rating
FROM REVIEWS r
LEFT JOIN STATIONS s ON r.station_id = s.station_id;


-- ----------------------------------------------------------------------------
-- 4. CROSS JOIN
-- Generate compatibility matrix between all vehicle types and all available connector types
-- ----------------------------------------------------------------------------
SELECT DISTINCT 
    v.type AS vehicle_type, 
    p.connector_type
FROM VEHICLES v
CROSS JOIN PORTS p
ORDER BY vehicle_type, connector_type;


-- ----------------------------------------------------------------------------
-- 5. SET OPERATIONS: UNION & UNION ALL
-- ----------------------------------------------------------------------------

-- A. UNION (Distinct set of user IDs who either made a booking OR wrote a review)
SELECT user_id FROM BOOKINGS
UNION
SELECT user_id FROM REVIEWS;

-- B. UNION ALL (Combined activity log preserving duplicate occurrences)
SELECT user_id, 'Made Booking' AS activity_type FROM BOOKINGS
UNION ALL
SELECT user_id, 'Wrote Review' AS activity_type FROM REVIEWS
ORDER BY user_id;


-- ----------------------------------------------------------------------------
-- 6. SET OPERATIONS: INTERSECT & EXCEPT
-- ----------------------------------------------------------------------------

-- A. INTERSECT: Find users who have both made a booking AND written a review
SELECT user_id FROM BOOKINGS
INTERSECT
SELECT user_id FROM REVIEWS;

-- B. EXCEPT: Find users who have created bookings but NEVER submitted any review
SELECT user_id FROM BOOKINGS
EXCEPT
SELECT user_id FROM REVIEWS;
