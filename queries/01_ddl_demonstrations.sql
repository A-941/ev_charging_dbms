-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 01_ddl_demonstrations.sql
-- Topic: DDL (Data Definition Language) - CREATE, ALTER, RENAME, TRUNCATE, DROP
-- ============================================================================

-- 1. CREATE TABLE with extensive domain and integrity constraints
CREATE TABLE IF NOT EXISTS STATION_MAINTENANCE_LOGS (
    log_id INT PRIMARY KEY,
    station_id INT NOT NULL,
    maintenance_date DATE NOT NULL,
    technician_name VARCHAR(100) NOT NULL,
    cost DECIMAL(8, 2) NOT NULL CHECK (cost >= 0.0),
    description TEXT,
    CONSTRAINT fk_log_station
        FOREIGN KEY (station_id) REFERENCES STATIONS(station_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- 2. ALTER TABLE: Add a new column
ALTER TABLE USERS ADD COLUMN email VARCHAR(120);

-- 3. ALTER TABLE: Add a default value / modify column (PostgreSQL / MySQL dialect)
-- ALTER TABLE USERS ALTER COLUMN email SET DEFAULT 'user@evnetwork.com';

-- 4. ALTER TABLE: Add a unique constraint to the new column
-- (Supported across ANSI SQL standard)
-- ALTER TABLE USERS ADD CONSTRAINT uq_user_email UNIQUE (email);

-- 5. RENAME TABLE demonstration
-- Create a temporary archive table and rename it
CREATE TABLE IF NOT EXISTS OLD_COMPLAINTS_TEMP (
    temp_id INT PRIMARY KEY,
    note TEXT
);

ALTER TABLE OLD_COMPLAINTS_TEMP RENAME TO ARCHIVED_COMPLAINTS_LOG;

-- 6. RENAME COLUMN demonstration
ALTER TABLE ARCHIVED_COMPLAINTS_LOG RENAME COLUMN note TO incident_note;

-- 7. TRUNCATE TABLE (Empties all records quickly without removing the table structure)
-- In MySQL / PostgreSQL:
-- TRUNCATE TABLE ARCHIVED_COMPLAINTS_LOG;
-- In SQLite:
DELETE FROM ARCHIVED_COMPLAINTS_LOG;

-- 8. DROP TABLE demonstration
DROP TABLE IF EXISTS ARCHIVED_COMPLAINTS_LOG;
