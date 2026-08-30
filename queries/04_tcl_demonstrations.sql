-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 04_tcl_demonstrations.sql
-- Topic: TCL (Transaction Control Language) - COMMIT, SAVEPOINT, ROLLBACK
-- ============================================================================

-- ----------------------------------------------------------------------------
-- SCENARIO 1: ATOMIC CHARGING BOOKING WITH SUCCESSFUL COMMIT
-- A user books a port, port status is updated to 'Reserved', and initial payment record is authorized.
-- ----------------------------------------------------------------------------

BEGIN TRANSACTION;

-- Step 1: Insert new booking
INSERT INTO BOOKINGS (booking_id, user_id, port_id, start_time, status)
VALUES (9901, 1, 10, '2026-09-01 10:00:00', 'Confirmed');

-- Step 2: Update port status to Reserved
UPDATE PORTS
SET status = 'Reserved'
WHERE port_id = 10;

-- Step 3: Insert pre-authorization payment record
INSERT INTO PAYMENTS (payment_id, booking_id, amount)
VALUES (9901, 9901, 25.00);

-- All operations succeed -> Commit changes permanently
COMMIT;


-- ----------------------------------------------------------------------------
-- SCENARIO 2: PARTIAL TRANSACTION WITH SAVEPOINT AND ROLLBACK TO SAVEPOINT
-- Create a booking, attempt a charging session start, encounter a fault, roll back only the session.
-- ----------------------------------------------------------------------------

BEGIN TRANSACTION;

-- Step 1: User creates booking
INSERT INTO BOOKINGS (booking_id, user_id, port_id, start_time, status)
VALUES (9902, 2, 12, '2026-09-01 11:30:00', 'Confirmed');

-- Step 2: Establish a checkpoint (Savepoint)
SAVEPOINT booking_created_checkpoint;

-- Step 3: Attempt to start charging session on a faulted hardware port
-- Simulated session start insertion:
INSERT INTO CHARGING_SESSIONS (session_id, booking_id, energy_kwh, end_time)
VALUES (9902, 9902, 0.0, '2026-09-01 11:32:00');

-- Hardware fault detected! Revert only the session initiation back to savepoint:
ROLLBACK TO SAVEPOINT booking_created_checkpoint;

-- Step 4: Update booking status to Cancelled due to hardware fault
UPDATE BOOKINGS
SET status = 'Cancelled'
WHERE booking_id = 9902;

-- Commit the cancelled booking record (without the faulted session)
COMMIT;


-- ----------------------------------------------------------------------------
-- SCENARIO 3: COMPLETE TRANSACTION ROLLBACK (FAILURE HANDLING)
-- If an unexpected constraint violation occurs, abort the entire transaction.
-- ----------------------------------------------------------------------------

BEGIN TRANSACTION;

-- Attempting an invalid operation
INSERT INTO USERS (user_id, name, phone)
VALUES (9999, 'Temporary User', '+1-000-000-0000');

-- Unexpected system abort / error:
-- Abort all uncommitted operations in this transaction
ROLLBACK;

-- Verify user 9999 does not exist in the database:
-- SELECT * FROM USERS WHERE user_id = 9999;
