-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 09_procedures_triggers.sql
-- Topic: Stored Procedures, Functions, and Business Triggers
-- Target: SQLite (Native Triggers) & PostgreSQL / MySQL (PL/pgSQL & Stored Routines)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SQLITE NATIVE TRIGGERS
-- ----------------------------------------------------------------------------

-- Trigger A: Automatically update PORT status to 'Reserved' when a new BOOKING is created
DROP TRIGGER IF EXISTS trg_port_reserved_on_booking;

CREATE TRIGGER trg_port_reserved_on_booking
AFTER INSERT ON BOOKINGS
FOR EACH ROW
WHEN NEW.status = 'Confirmed'
BEGIN
    UPDATE PORTS
    SET status = 'Reserved'
    WHERE port_id = NEW.port_id;
END;

-- Trigger B: Automatically restore PORT status to 'Available' when a BOOKING is marked 'Completed' or 'Cancelled'
DROP TRIGGER IF EXISTS trg_port_available_on_booking_end;

CREATE TRIGGER trg_port_available_on_booking_end
AFTER UPDATE OF status ON BOOKINGS
FOR EACH ROW
WHEN NEW.status IN ('Completed', 'Cancelled')
BEGIN
    UPDATE PORTS
    SET status = 'Available'
    WHERE port_id = NEW.port_id;
END;

-- Trigger C: Automatically mark PORT as 'Faulted' when an 'Open' high-severity complaint is lodged
DROP TRIGGER IF EXISTS trg_port_fault_on_complaint;

CREATE TRIGGER trg_port_fault_on_complaint
AFTER INSERT ON COMPLAINTS
FOR EACH ROW
WHEN NEW.status = 'Open'
BEGIN
    UPDATE PORTS
    SET status = 'Faulted'
    WHERE port_id = NEW.port_id;
END;


-- ----------------------------------------------------------------------------
-- 2. STORED FUNCTIONS & PROCEDURES (MySQL / PostgreSQL PL/pgSQL Specification)
-- ----------------------------------------------------------------------------

/*
-- POSTGRESQL / MYSQL STORED FUNCTION: Calculate Total Cost with Dynamic Tariff and Tax
CREATE OR REPLACE FUNCTION fn_calculate_charging_bill(
    p_energy_kwh DECIMAL,
    p_port_id INT
) RETURNS DECIMAL(8, 2) AS $$
DECLARE
    v_rate DECIMAL(6, 2);
    v_subtotal DECIMAL(8, 2);
    v_tax DECIMAL(8, 2);
    v_service_fee CONSTANT DECIMAL(8, 2) := 2.50;
BEGIN
    -- Fetch tariff rate for the port
    SELECT rate_per_kwh INTO v_rate FROM PRICES WHERE port_id = p_port_id;
    IF v_rate IS NULL THEN
        v_rate := 0.35; -- Default baseline fallback
    END IF;
    
    v_subtotal := (p_energy_kwh * v_rate) + v_service_fee;
    v_tax := v_subtotal * 0.05; -- 5% statutory electricity tax
    
    RETURN ROUND(v_subtotal + v_tax, 2);
END;
$$ LANGUAGE plpgsql;


-- POSTGRESQL / MYSQL STORED PROCEDURE: Complete Charging Session & Finalize Billing
CREATE OR REPLACE PROCEDURE sp_complete_charging_session(
    p_booking_id INT,
    p_energy_kwh DECIMAL,
    p_end_time TIMESTAMP
) AS $$
DECLARE
    v_port_id INT;
    v_amount DECIMAL(8, 2);
    v_new_session_id INT;
    v_new_payment_id INT;
BEGIN
    -- Get Port ID for the booking
    SELECT port_id INTO v_port_id FROM BOOKINGS WHERE booking_id = p_booking_id;
    
    -- Calculate bill amount
    v_amount := fn_calculate_charging_bill(p_energy_kwh, v_port_id);
    
    -- Insert Charging Session
    SELECT COALESCE(MAX(session_id), 0) + 1 INTO v_new_session_id FROM CHARGING_SESSIONS;
    INSERT INTO CHARGING_SESSIONS (session_id, booking_id, energy_kwh, end_time)
    VALUES (v_new_session_id, p_booking_id, p_energy_kwh, p_end_time);
    
    -- Insert Payment
    SELECT COALESCE(MAX(payment_id), 0) + 1 INTO v_new_payment_id FROM PAYMENTS;
    INSERT INTO PAYMENTS (payment_id, booking_id, amount)
    VALUES (v_new_payment_id, p_booking_id, v_amount);
    
    -- Mark booking as completed
    UPDATE BOOKINGS SET status = 'Completed' WHERE booking_id = p_booking_id;
    
    -- Release port back to Available
    UPDATE PORTS SET status = 'Available' WHERE port_id = v_port_id;
    
    COMMIT;
END;
$$ LANGUAGE plpgsql;
*/
