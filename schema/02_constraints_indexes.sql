-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT 02: SECONDARY INDEXES & RELATIONAL PERFORMANCE OPTIMIZATIONS
-- ============================================================================

-- Indexes for frequent foreign key joins and search operations

-- 1. Index on Station by Operator
CREATE INDEX IF NOT EXISTS idx_stations_operator ON STATIONS(operator_id);

-- 2. Geospatial query index on Station coordinates (Latitude, Longitude)
CREATE INDEX IF NOT EXISTS idx_stations_location ON STATIONS(latitude, longitude);

-- 3. Index on Ports by Station and Status (for finding available ports quickly)
CREATE INDEX IF NOT EXISTS idx_ports_station_status ON PORTS(station_id, status);

-- 4. Index on Bookings by User and Start Time
CREATE INDEX IF NOT EXISTS idx_bookings_user_time ON BOOKINGS(user_id, start_time);

-- 5. Index on Bookings by Port and Status
CREATE INDEX IF NOT EXISTS idx_bookings_port_status ON BOOKINGS(port_id, status);

-- 6. Index on Charging Sessions by Booking
CREATE INDEX IF NOT EXISTS idx_sessions_booking ON CHARGING_SESSIONS(booking_id);

-- 7. Index on Reviews by Station (for computing average station rating)
CREATE INDEX IF NOT EXISTS idx_reviews_station ON REVIEWS(station_id);

-- 8. Index on Complaints by Port and Status
CREATE INDEX IF NOT EXISTS idx_complaints_port_status ON COMPLAINTS(port_id, status);
