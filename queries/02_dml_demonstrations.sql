-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 02_dml_demonstrations.sql
-- Topic: DML (Data Manipulation Language) - INSERT, UPDATE, DELETE (with/without cascade)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. INSERT DEMONSTRATIONS
-- ----------------------------------------------------------------------------

-- Single record insertion into USERS
INSERT INTO USERS (user_id, name, phone)
VALUES (999, 'Test User', '+1-555-019-9999');

-- Single record insertion into VEHICLES referencing the newly inserted user
INSERT INTO VEHICLES (vehicle_id, user_id, type, connector_needed)
VALUES (999, 999, 'SUV', 'CCS2');

-- Multi-row batch insertion into REVIEWS
INSERT INTO REVIEWS (review_id, user_id, station_id, rating)
VALUES 
    (9901, 999, 1, 5),
    (9902, 999, 2, 4);

-- ----------------------------------------------------------------------------
-- 2. UPDATE DEMONSTRATIONS (Without and With Cascade)
-- ----------------------------------------------------------------------------

-- A. Simple UPDATE without cascade: Updating a non-key attribute
UPDATE PORTS
SET status = 'Under Maintenance'
WHERE port_id = 1;

-- B. Bulk conditional UPDATE
UPDATE PRICES
SET rate_per_kwh = ROUND(rate_per_kwh * 1.05, 2)
WHERE port_id IN (
    SELECT port_id FROM PORTS WHERE connector_type = 'Tesla Supercharger'
);

-- C. UPDATE with CASCADE on Primary Key:
-- When foreign keys have ON UPDATE CASCADE configured:
-- Updating the primary key in OPERATORS cascades to STATIONS.operator_id automatically.
-- Demonstration (Wrap in temporary test or transaction):
-- UPDATE OPERATORS SET operator_id = 1001 WHERE operator_id = 15;
-- (All STATIONS referencing operator 15 now reference operator 1001).

-- ----------------------------------------------------------------------------
-- 3. DELETE DEMONSTRATIONS (Without and With Cascade)
-- ----------------------------------------------------------------------------

-- A. Simple DELETE without cascade: Deleting a leaf entity (Complaint)
DELETE FROM COMPLAINTS
WHERE complaint_id = 1;

-- B. DELETE with CASCADE:
-- Deleting user 999 will automatically delete vehicle 999 and reviews 9901, 9902
-- due to FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE.
DELETE FROM USERS
WHERE user_id = 999;

-- Verify deletion cascade:
-- SELECT * FROM VEHICLES WHERE user_id = 999; (Returns 0 rows)
-- SELECT * FROM REVIEWS WHERE user_id = 999;  (Returns 0 rows)
