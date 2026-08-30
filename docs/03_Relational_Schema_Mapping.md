# Relational Schema Mapping & Functional Dependencies

## 1. ER to Relational Transformation

The conceptual ER model is converted to relational tables following standard transformation rules:
1. **Strong Entities**: Mapped directly to independent relations with their primary key.
2. **1:N Relationships**: Foreign key placed on the $N$-side relation referencing the $1$-side primary key.
3. **1:1 Relationships**: Foreign key placed on the dependent/total participation relation with a `UNIQUE` constraint.

---

## 2. Relational Schema Representation

```
OPERATORS (operator_id [PK], company_name [UQ])

STATIONS (station_id [PK], operator_id [FK -> OPERATORS.operator_id], latitude, longitude)

PORTS (port_id [PK], station_id [FK -> STATIONS.station_id], connector_type, status)

PRICES (price_id [PK], port_id [FK -> PORTS.port_id, UQ], rate_per_kwh)

USERS (user_id [PK], name, phone [UQ])

VEHICLES (vehicle_id [PK], user_id [FK -> USERS.user_id], type, connector_needed)

BOOKINGS (booking_id [PK], user_id [FK -> USERS.user_id], port_id [FK -> PORTS.port_id], start_time, status)

CHARGING_SESSIONS (session_id [PK], booking_id [FK -> BOOKINGS.booking_id, UQ], energy_kwh, end_time)

PAYMENTS (payment_id [PK], booking_id [FK -> BOOKINGS.booking_id, UQ], amount)

REVIEWS (review_id [PK], user_id [FK -> USERS.user_id], station_id [FK -> STATIONS.station_id], rating)

COMPLAINTS (complaint_id [PK], port_id [FK -> PORTS.port_id], issue, status)
```

---

## 3. Functional Dependencies ($F$) per Relation

1. **OPERATORS**:
   - $F_1 = \{ \text{operator\_id} \rightarrow \text{company\_name}, \; \text{company\_name} \rightarrow \text{operator\_id} \}$
   - Candidate Keys: $\{\text{operator\_id}\}, \{\text{company\_name}\}$

2. **STATIONS**:
   - $F_2 = \{ \text{station\_id} \rightarrow (\text{operator\_id}, \text{latitude}, \text{longitude}) \}$
   - Candidate Key: $\{\text{station\_id}\}$

3. **PORTS**:
   - $F_3 = \{ \text{port\_id} \rightarrow (\text{station\_id}, \text{connector\_type}, \text{status}) \}$
   - Candidate Key: $\{\text{port\_id}\}$

4. **PRICES**:
   - $F_4 = \{ \text{price\_id} \rightarrow (\text{port\_id}, \text{rate\_per\_kwh}), \; \text{port\_id} \rightarrow (\text{price\_id}, \text{rate\_per\_kwh}) \}$
   - Candidate Keys: $\{\text{price\_id}\}, \{\text{port\_id}\}$

5. **USERS**:
   - $F_5 = \{ \text{user\_id} \rightarrow (\text{name}, \text{phone}), \; \text{phone} \rightarrow (\text{user\_id}, \text{name}) \}$
   - Candidate Keys: $\{\text{user\_id}\}, \{\text{phone}\}$

6. **VEHICLES**:
   - $F_6 = \{ \text{vehicle\_id} \rightarrow (\text{user\_id}, \text{type}, \text{connector\_needed}) \}$
   - Candidate Key: $\{\text{vehicle\_id}\}$

7. **BOOKINGS**:
   - $F_7 = \{ \text{booking\_id} \rightarrow (\text{user\_id}, \text{port\_id}, \text{start\_time}, \text{status}) \}$
   - Candidate Key: $\{\text{booking\_id}\}$

8. **CHARGING_SESSIONS**:
   - $F_8 = \{ \text{session\_id} \rightarrow (\text{booking\_id}, \text{energy\_kwh}, \text{end\_time}), \; \text{booking\_id} \rightarrow (\text{session\_id}, \text{energy\_kwh}, \text{end\_time}) \}$
   - Candidate Keys: $\{\text{session\_id}\}, \{\text{booking\_id}\}$

9. **PAYMENTS**:
   - $F_9 = \{ \text{payment\_id} \rightarrow (\text{booking\_id}, \text{amount}), \; \text{booking\_id} \rightarrow (\text{payment\_id}, \text{amount}) \}$
   - Candidate Keys: $\{\text{payment\_id}\}, \{\text{booking\_id}\}$

10. **REVIEWS**:
    - $F_{10} = \{ \text{review\_id} \rightarrow (\text{user\_id}, \text{station\_id}, \text{rating}) \}$
    - Candidate Key: $\{\text{review\_id}\}$

11. **COMPLAINTS**:
    - $F_{11} = \{ \text{complaint\_id} \rightarrow (\text{port\_id}, \text{issue}, \text{status}) \}$
    - Candidate Key: $\{\text{complaint\_id}\}$

---

## 4. Integrity Constraints Summary
- **Entity Integrity**: Every table possesses a non-null, uniquely identifying Primary Key.
- **Referential Integrity**: All foreign keys enforce valid target references with `ON DELETE CASCADE` and `ON UPDATE CASCADE` to maintain relational consistency.
- **Domain Constraints**:
  - `PORTS.status` $\in$ `{'Available', 'Occupied', 'Reserved', 'Under Maintenance', 'Faulted'}`
  - `REVIEWS.rating` $\in [1, 5]$
  - `STATIONS.latitude` $\in [-90.0, 90.0]$, `STATIONS.longitude` $\in [-180.0, 180.0]$
  - `PRICES.rate_per_kwh` $> 0.0$
  - `CHARGING_SESSIONS.energy_kwh` $\ge 0.0$
  - `PAYMENTS.amount` $\ge 0.0$
