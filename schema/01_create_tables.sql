-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT 01: DDL TABLE CREATION & INTEGRITY CONSTRAINTS
-- Target Compatibility: SQLite / PostgreSQL / MySQL
-- ============================================================================

-- 1. OPERATORS
-- Represents companies that own and operate charging infrastructure
CREATE TABLE IF NOT EXISTS OPERATORS (
    operator_id INT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL UNIQUE
);

-- 2. STATIONS
-- Represents physical charging station locations managed by operators
CREATE TABLE IF NOT EXISTS STATIONS (
    station_id INT PRIMARY KEY,
    operator_id INT NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL CHECK (latitude BETWEEN -90.0 AND 90.0),
    longitude DECIMAL(9, 6) NOT NULL CHECK (longitude BETWEEN -180.0 AND 180.0),
    CONSTRAINT fk_station_operator
        FOREIGN KEY (operator_id) REFERENCES OPERATORS(operator_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 3. PORTS
-- Represents individual charging guns/points available at a station
CREATE TABLE IF NOT EXISTS PORTS (
    port_id INT PRIMARY KEY,
    station_id INT NOT NULL,
    connector_type VARCHAR(50) NOT NULL CHECK (connector_type IN ('CCS2', 'Type 2', 'CHAdeMO', 'GB/T', 'Tesla Supercharger')),
    status VARCHAR(30) NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'Occupied', 'Reserved', 'Under Maintenance', 'Faulted')),
    CONSTRAINT fk_port_station
        FOREIGN KEY (station_id) REFERENCES STATIONS(station_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 4. PRICES
-- Tariff rate per kWh for electricity consumption at each specific port
CREATE TABLE IF NOT EXISTS PRICES (
    price_id INT PRIMARY KEY,
    port_id INT NOT NULL UNIQUE,
    rate_per_kwh DECIMAL(6, 2) NOT NULL CHECK (rate_per_kwh > 0.0),
    CONSTRAINT fk_price_port
        FOREIGN KEY (port_id) REFERENCES PORTS(port_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 5. USERS
-- Registered EV drivers using the charging network
CREATE TABLE IF NOT EXISTS USERS (
    user_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE
);

-- 6. VEHICLES
-- Registered electric vehicles owned by users
CREATE TABLE IF NOT EXISTS VEHICLES (
    vehicle_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('2-Wheeler', '3-Wheeler', 'Sedan', 'SUV', 'Hatchback', 'Commercial Van', 'Bus')),
    connector_needed VARCHAR(50) NOT NULL CHECK (connector_needed IN ('CCS2', 'Type 2', 'CHAdeMO', 'GB/T', 'Tesla Supercharger')),
    CONSTRAINT fk_vehicle_user
        FOREIGN KEY (user_id) REFERENCES USERS(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 7. BOOKINGS
-- Slot reservations made by users for charging at a designated port
CREATE TABLE IF NOT EXISTS BOOKINGS (
    booking_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    port_id INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Confirmed', 'In Progress', 'Completed', 'Cancelled')),
    CONSTRAINT fk_booking_user
        FOREIGN KEY (user_id) REFERENCES USERS(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_booking_port
        FOREIGN KEY (port_id) REFERENCES PORTS(port_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 8. CHARGING_SESSIONS
-- Actual energy dispensing events linked to a booking
CREATE TABLE IF NOT EXISTS CHARGING_SESSIONS (
    session_id INT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    energy_kwh DECIMAL(6, 2) NOT NULL CHECK (energy_kwh >= 0.0),
    end_time TIMESTAMP NOT NULL,
    CONSTRAINT fk_session_booking
        FOREIGN KEY (booking_id) REFERENCES BOOKINGS(booking_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 9. PAYMENTS
-- Financial transactions settled for completed bookings and sessions
CREATE TABLE IF NOT EXISTS PAYMENTS (
    payment_id INT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    amount DECIMAL(8, 2) NOT NULL CHECK (amount >= 0.0),
    CONSTRAINT fk_payment_booking
        FOREIGN KEY (booking_id) REFERENCES BOOKINGS(booking_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 10. REVIEWS
-- Customer feedback ratings given to stations
CREATE TABLE IF NOT EXISTS REVIEWS (
    review_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    station_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT fk_review_user
        FOREIGN KEY (user_id) REFERENCES USERS(user_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_review_station
        FOREIGN KEY (station_id) REFERENCES STATIONS(station_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 11. COMPLAINTS
-- Maintenance and technical incident reports filed regarding specific ports
CREATE TABLE IF NOT EXISTS COMPLAINTS (
    complaint_id INT PRIMARY KEY,
    port_id INT NOT NULL,
    issue TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved', 'Closed')),
    CONSTRAINT fk_complaint_port
        FOREIGN KEY (port_id) REFERENCES PORTS(port_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 12. REFUNDS
-- Refund transactions issued for cancelled bookings or billing disputes
CREATE TABLE IF NOT EXISTS REFUNDS (
    refund_id INT PRIMARY KEY,
    payment_id INT NOT NULL,
    booking_id INT NOT NULL,
    amount DECIMAL(8, 2) NOT NULL CHECK (amount >= 0.0),
    reason TEXT NOT NULL,
    refund_time TIMESTAMP NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Processed' CHECK (status IN ('Processed', 'Pending', 'Rejected')),
    CONSTRAINT fk_refund_payment
        FOREIGN KEY (payment_id) REFERENCES PAYMENTS(payment_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_refund_booking
        FOREIGN KEY (booking_id) REFERENCES BOOKINGS(booking_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

