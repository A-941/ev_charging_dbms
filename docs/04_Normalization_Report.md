# Database Normalization Report (1NF to 3NF / BCNF)

## 1. Normalization Objective & Anomaly Elimination
Database normalization is the systematic technique of organizing relational tables to minimize data redundancy and prevent data modification anomalies:
- **Insertion Anomaly**: Inability to record an operator or a station without first creating a fake user or booking.
- **Deletion Anomaly**: Deleting a user accidentally deleting the physical port pricing or station location records.
- **Update Anomaly**: Updating a station's latitude requiring modification across thousands of past booking rows, risking data inconsistency.

---

## 2. Unnormalized Initial State vs Normalized Decomposition

Consider an unnormalized universal relation that attempts to store all network activity in a single table:

$$\text{UNIVERSAL\_EV\_TABLE} = (\underline{\text{user\_id}}, \underline{\text{booking\_id}}, \text{user\_name}, \text{user\_phone}, \text{station\_id}, \text{operator\_id}, \text{company\_name}, \text{station\_lat}, \text{station\_lon}, \text{port\_id}, \text{connector\_type}, \text{port\_status}, \text{rate\_per\_kwh}, \text{energy\_kwh}, \text{amount}, \text{review\_rating}, \text{complaint\_issue})$$

### Anomalies in Universal Design:
- Redundant repetition of operator names, station coordinates, and pricing tariffs across every booking.
- Transitive and partial dependencies violate relational integrity.

---

## 3. Step-by-Step Normalization Process

### Step 1: First Normal Form (1NF)
**Criteria**:
1. All attributes contain only atomic (indivisible) scalar values.
2. No multi-valued attributes (e.g. comma-separated vehicle lists or multi-phone strings).
3. No repeating groups.
4. Each relation possesses a designated unique primary key.

**Transformation**:
- Multi-valued vehicle ownership is isolated into an independent `VEHICLES` relation where each row represents a single vehicle.
- Phone numbers are stored as single unique scalar strings.
- All 11 entities fulfill 1NF.

---

### Step 2: Second Normal Form (2NF)
**Criteria**:
1. The relation must be in **1NF**.
2. **No Partial Functional Dependencies**: No non-prime attribute may depend on a proper subset of any composite candidate key ($X \subset \text{Candidate Key} \implies X \not\rightarrow Y$).

**Analysis**:
- In our schema, all 11 relations utilize single-attribute primary keys (`operator_id`, `station_id`, `port_id`, `price_id`, `user_id`, `vehicle_id`, `booking_id`, `session_id`, `payment_id`, `review_id`, `complaint_id`).
- Since every primary key is atomic (consists of exactly 1 attribute), **a proper subset of the key does not exist**.
- Therefore, partial dependency cannot mathematically occur.
$$\therefore \text{All 11 relations are inherently in 2NF.}$$

---

### Step 3: Third Normal Form (3NF)
**Criteria**:
1. The relation must be in **2NF**.
2. **No Transitive Functional Dependencies**: For every non-trivial functional dependency $X \rightarrow Y$:
   - $X$ is a **Superkey**, OR
   - $Y$ is a **Prime Attribute** (part of a candidate key).

**Verification across all 11 relations**:

1. **OPERATORS** ($\text{operator\_id}, \text{company\_name}$):
   - $FD_1: \text{operator\_id} \rightarrow \text{company\_name}$ ($\text{operator\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

2. **STATIONS** ($\text{station\_id}, \text{operator\_id}, \text{latitude}, \text{longitude}$):
   - $FD_1: \text{station\_id} \rightarrow (\text{operator\_id}, \text{latitude}, \text{longitude})$ ($\text{station\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

3. **PORTS** ($\text{port\_id}, \text{station\_id}, \text{connector\_type}, \text{status}$):
   - $FD_1: \text{port\_id} \rightarrow (\text{station\_id}, \text{connector\_type}, \text{status})$ ($\text{port\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

4. **PRICES** ($\text{price\_id}, \text{port\_id}, \text{rate\_per\_kwh}$):
   - $FD_1: \text{price\_id} \rightarrow (\text{port\_id}, \text{rate\_per\_kwh})$ ($\text{price\_id}$ is Superkey)
   - $FD_2: \text{port\_id} \rightarrow (\text{price\_id}, \text{rate\_per\_kwh})$ ($\text{port\_id}$ is Candidate Key) $\implies$ **In 3NF / BCNF**.

5. **USERS** ($\text{user\_id}, \text{name}, \text{phone}$):
   - $FD_1: \text{user\_id} \rightarrow (\text{name}, \text{phone})$ ($\text{user\_id}$ is Superkey)
   - $FD_2: \text{phone} \rightarrow (\text{user\_id}, \text{name})$ ($\text{phone}$ is Candidate Key) $\implies$ **In 3NF / BCNF**.

6. **VEHICLES** ($\text{vehicle\_id}, \text{user\_id}, \text{type}, \text{connector\_needed}$):
   - $FD_1: \text{vehicle\_id} \rightarrow (\text{user\_id}, \text{type}, \text{connector\_needed})$ ($\text{vehicle\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

7. **BOOKINGS** ($\text{booking\_id}, \text{user\_id}, \text{port\_id}, \text{start\_time}, \text{status}$):
   - $FD_1: \text{booking\_id} \rightarrow (\text{user\_id}, \text{port\_id}, \text{start\_time}, \text{status})$ ($\text{booking\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

8. **CHARGING_SESSIONS** ($\text{session\_id}, \text{booking\_id}, \text{energy\_kwh}, \text{end\_time}$):
   - $FD_1: \text{session\_id} \rightarrow (\text{booking\_id}, \text{energy\_kwh}, \text{end\_time})$ ($\text{session\_id}$ is Superkey)
   - $FD_2: \text{booking\_id} \rightarrow (\text{session\_id}, \text{energy\_kwh}, \text{end\_time})$ ($\text{booking\_id}$ is Candidate Key) $\implies$ **In 3NF / BCNF**.

9. **PAYMENTS** ($\text{payment\_id}, \text{booking\_id}, \text{amount}$):
   - $FD_1: \text{payment\_id} \rightarrow (\text{booking\_id}, \text{amount})$ ($\text{payment\_id}$ is Superkey)
   - $FD_2: \text{booking\_id} \rightarrow (\text{payment\_id}, \text{amount})$ ($\text{booking\_id}$ is Candidate Key) $\implies$ **In 3NF / BCNF**.

10. **REVIEWS** ($\text{review\_id}, \text{user\_id}, \text{station\_id}, \text{rating}$):
    - $FD_1: \text{review\_id} \rightarrow (\text{user\_id}, \text{station\_id}, \text{rating})$ ($\text{review\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

11. **COMPLAINTS** ($\text{complaint\_id}, \text{port\_id}, \text{issue}, \text{status}$):
    - $FD_1: \text{complaint\_id} \rightarrow (\text{port\_id}, \text{issue}, \text{status})$ ($\text{complaint\_id}$ is Superkey) $\implies$ **In 3NF / BCNF**.

---

## 4. Normalization Properties Verification

### A. Lossless Join Decomposition
For any decomposition $R \rightarrow (R_1, R_2)$, the join is lossless if and only if:
$$(R_1 \cap R_2) \rightarrow R_1 \quad \text{or} \quad (R_1 \cap R_2) \rightarrow R_2$$
In our schema:
- $\text{STATIONS} \cap \text{PORTS} = \{\text{station\_id}\}$, and $\text{station\_id} \rightarrow \text{STATIONS}$.
- $\text{PORTS} \cap \text{PRICES} = \{\text{port\_id}\}$, and $\text{port\_id} \rightarrow \text{PRICES}$.
- $\text{BOOKINGS} \cap \text{PAYMENTS} = \{\text{booking\_id}\}$, and $\text{booking\_id} \rightarrow \text{PAYMENTS}$.

$$\therefore \text{All decomposed relations guarantee a 100\% Lossless Join decomposition.}$$

### B. Dependency Preservation
Every functional dependency in the original set $F$ is preserved within individual decomposed relations without needing cross-table joins to enforce constraints.

$$\therefore \text{The schema is Dependency Preserving and strictly in Boyce-Codd Normal Form (BCNF).}$$
