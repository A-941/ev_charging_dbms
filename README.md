# ⚡ Electric Vehicle (EV) Charging Station Network DBMS

An end-to-end Database Management System (DBMS) project designed strictly according to academic guidelines. Built around an **11-Entity Relational Model** in **Boyce-Codd / 3rd Normal Form (3NF)** with complete SQL demonstrations (DDL, DML, DCL, TCL, DQL, Joins, Set Ops, Subqueries, Views, Triggers) and **two interactive Front-End options (Flask Web App & Streamlit Dashboard)**.

---

## 📁 Project Directory Structure

```
ev_charging_dbms/
├── DBMS_Project_Guidelines.pdf         # Reference university project guidelines
├── er_diagram.jpeg                     # Entity Relationship Diagram (High-Res)
├── ev_charging.db                      # Pre-populated, ready-to-query SQLite database (1,300+ records)
├── schema/
│   ├── 01_create_tables.sql            # DDL: 11 Table definitions with domain integrity constraints
│   ├── 02_constraints_indexes.sql      # DDL: Secondary performance & geospatial indexes
│   └── 03_drop_cleanup.sql             # DDL: Safe teardown script (reverse FK dependency order)
├── data/
│   ├── generate_mock_data.py           # Automated mock generator creating 1,300+ valid records
│   └── 01_populate_data.sql            # Ready-to-run SQL insert statements
├── queries/
│   ├── 01_ddl_demonstrations.sql       # CREATE, ALTER, RENAME, TRUNCATE, DROP
│   ├── 02_dml_demonstrations.sql       # INSERT, UPDATE (cascade/no-cascade), DELETE (cascade)
│   ├── 03_dcl_demonstrations.sql       # GRANT, REVOKE & Role-Based Access Control
│   ├── 04_tcl_demonstrations.sql       # COMMIT, SAVEPOINT, ROLLBACK transaction scenarios
│   ├── 05_dql_basic_advanced.sql       # WHERE, AGGREGATE, IN, LIKE, DISTINCT, ORDER BY, GROUP BY + HAVING
│   ├── 06_joins_and_set_ops.sql        # INNER, LEFT, RIGHT/FULL JOIN, UNION, INTERSECT, EXCEPT
│   ├── 07_subqueries.sql               # Single-row, Multi-row, Correlated, EXISTS, ANY, ALL
│   ├── 08_views.sql                    # Live station status, user history, operator financials
│   └── 09_procedures_triggers.sql      # Auto-reserve, auto-release, fault triggers, bill functions
├── docs/
│   ├── 01_Project_Statement.md         # Problem background, stakeholders & real-world use cases
│   ├── 02_ER_Model_Analysis.md         # Entities, cardinalities, modalities, participation constraints
│   ├── 03_Relational_Schema_Mapping.md # Relational schema diagram & functional dependencies
│   ├── 04_Normalization_Report.md      # Mathematical 1NF -> 2NF -> 3NF/BCNF step-by-step proofs
│   └── 05_Comprehensive_Project_Report.md # Unified submission-ready master documentation
├── flask_app/                          # 🌐 Option A: Flask Web Application with HTML Forms
│   ├── app.py                          # Flask backend controller & SQL query engine
│   ├── static/                         # Static styling assets
│   └── templates/                      # Bootstrap 5 Jinja2 templates
│       ├── base.html                   # Master layout with responsive navbar & alerts
│       ├── index.html                  # Operational dashboard & live station view
│       ├── new_booking.html            # Driver slot reservation form
│       ├── new_payment.html            # Session completion & billing settlement form
│       ├── new_complaint.html          # Port maintenance ticketing form
│       ├── new_review.html             # Customer star rating form
│       └── queries.html                # Interactive SQL Query Workbench
└── app/                                # 📊 Option B: Streamlit Data Dashboard
    ├── app.py                          # Multi-tab Streamlit dashboard
    ├── db.py                           # Database connection & query helper layer
    └── requirements.txt                # Dependencies (streamlit, pandas, flask)
```

---

## 🚀 How to Run the Applications

### Option A: Launch the Flask Web Application (Recommended for Academic Submission)
From the project directory:
```bash
py flask_app/app.py
```
Then open your browser to **http://127.0.0.1:5000**.

### Option B: Launch the Streamlit Dashboard
From the project directory:
```bash
py -m streamlit run app/app.py
```

### Re-generate or Seed the Database
To regenerate the SQLite database with 1,300+ fresh records:
```bash
py data/generate_mock_data.py
```
