-- ============================================================================
-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK
-- SCRIPT: 03_dcl_demonstrations.sql
-- Topic: DCL (Data Control Language) - GRANT, REVOKE & Role-Based Access Control
-- Target: PostgreSQL / MySQL / Enterprise RDBMS
-- ============================================================================

-- In enterprise relational DBMS (PostgreSQL / MySQL / Oracle), DCL commands 
-- govern security, table-level privileges, and role memberships.

-- ----------------------------------------------------------------------------
-- 1. ROLE DEFINITIONS
-- ----------------------------------------------------------------------------

-- Role 1: Station Operator / Vendor Manager (Can manage stations, ports, and pricing)
-- CREATE ROLE role_station_operator;

-- Role 2: Customer Mobile Application Backend (Can read stations, insert bookings/payments)
-- CREATE ROLE role_customer_service;

-- Role 3: Business Analytics & Reporting Auditor (Read-only on all analytical tables)
-- CREATE ROLE role_data_analyst;

-- ----------------------------------------------------------------------------
-- 2. GRANT DEMONSTRATIONS (Assigning Privileges)
-- ----------------------------------------------------------------------------

-- A. Grant full DML privileges on operational tables to Station Operator
-- GRANT SELECT, INSERT, UPDATE, DELETE ON OPERATORS, STATIONS, PORTS, PRICES, COMPLAINTS TO role_station_operator;

-- B. Grant selective privileges to Customer Mobile App
-- GRANT SELECT ON STATIONS, PORTS, PRICES TO role_customer_service;
-- GRANT SELECT, INSERT, UPDATE ON USERS, VEHICLES, BOOKINGS, CHARGING_SESSIONS, PAYMENTS, REVIEWS TO role_customer_service;

-- C. Grant read-only access to Data Analyst
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO role_data_analyst;

-- D. Grant with Grant Option (Delegated administration)
-- GRANT SELECT, UPDATE ON PRICES TO vendor_admin WITH GRANT OPTION;

-- ----------------------------------------------------------------------------
-- 3. REVOKE DEMONSTRATIONS (Revoking Privileges)
-- ----------------------------------------------------------------------------

-- A. Revoke DELETE permission from Customer Service to prevent accidental record loss
-- REVOKE DELETE ON USERS, BOOKINGS, PAYMENTS FROM role_customer_service;

-- B. Revoke pricing update privileges from standard operator
-- REVOKE UPDATE ON PRICES FROM role_station_operator;

-- C. Revoke all privileges when de-provisioning an employee
-- REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM old_employee_account;
