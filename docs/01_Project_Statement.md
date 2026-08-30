# EV Charging Station Management System: Project Statement & Objectives

## 1. Project Overview & Motivation
With the global transition toward sustainable e-mobility and decarbonization of transportation, Electric Vehicles (EVs) are growing exponentially. However, EV adoption relies heavily on reliable, accessible, and well-managed charging infrastructure.

An **EV Charging Station Management System (EVCSMS)** serves as the backbone connecting station operators, charging equipment, power grids, and EV drivers. The system coordinates station discovery, hardware status tracking, slot reservation, charging session monitoring, dynamic pricing, automated billing, customer satisfaction reviews, and hardware fault ticketing.

---

## 2. Real-Time Use Cases & Applications

### Use Case 1: Driver Charging Discovery & Reservation
- Drivers search for nearby stations based on geolocation (Latitude/Longitude).
- Real-time availability check for specific connector types (CCS2, Type 2, CHAdeMO, GB/T, Tesla Supercharger).
- Advance slot booking to avoid queuing at busy public hubs.

### Use Case 2: Smart Charging Session Execution & Metering
- Real-time recording of energy delivered (in kWh) during an active session.
- Automatic session completion timestamping and duration tracking.

### Use Case 3: Dynamic Tariff & Automated Payment Settlement
- Calculation of total charging costs based on per-kWh rates specific to port types (e.g. DC ultra-fast chargers vs AC destination chargers).
- Instant digital payment generation and receipt tracking.

### Use Case 4: Infrastructure Asset & Maintenance Management
- Network operators manage hundreds of charging stations and individual charging guns (ports).
- Real-time port health status tracking (`Available`, `Occupied`, `Reserved`, `Under Maintenance`, `Faulted`).
- Fault logging and ticketing when hardware issues (cable damage, screen failure, connector lock faults) are reported.

### Use Case 5: Quality Assurance & Review Analytics
- Drivers rate stations from 1 to 5 stars.
- Station performance aggregation, customer satisfaction indexing, and operator ranking.

---

## 3. Core Database Objectives
1. **Data Integrity & Consistency**: Enforce strict relational integrity constraints, preventing double-booking of charging ports and ensuring atomic session billing.
2. **High-Performance Querying**: Optimize geospatial station lookups, port availability filtering, and transactional history queries using tailored B-Tree indexes.
3. **Comprehensive Normalization**: Design a 3rd Normal Form (3NF) / BCNF compliant schema that completely eliminates data redundancy, insertion anomalies, deletion anomalies, and update anomalies.
4. **End-to-End SQL Implementation**: Implement complete DDL, DML, DCL, TCL, advanced DQL joins/subqueries, views, triggers, and stored procedures.
