"""
EV Charging Station DBMS - Mock Data Generator
Generates hundreds of realistic, referentially consistent records across all 11 tables.
Exports both an SQL file (01_populate_data.sql) and populates a local SQLite database (ev_charging.db).
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_OUTPUT_PATH = BASE_DIR / "data" / "01_populate_data.sql"
DB_PATH = BASE_DIR / "ev_charging.db"
SCHEMA_PATH = BASE_DIR / "schema" / "01_create_tables.sql"
INDEX_PATH = BASE_DIR / "schema" / "02_constraints_indexes.sql"

# Reference Datasets
OPERATOR_NAMES = [
    "ChargePoint Network Inc", "Electrify America", "EVgo Services", "Tesla Supercharge Corp",
    "Blink Charging Co", "Volta Charging Network", "Shell Recharge Solutions", "BP Pulse International",
    "Flo EV Charging", "SemaConnect Systems", "Ionity Network Europe", "TotalEnergies EV",
    "PowerFlex Charging", "Webasto E-Mobility", "ChargeLab Systems"
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Alexander", "Alice", "Ananya", "Benjamin", "Charlotte", "Daniel",
    "David", "Dhruv", "Elena", "Emily", "Ethan", "Fatima", "Gabriel", "Grace", "Hannah",
    "Ishaan", "James", "Jasmine", "John", "Julia", "Kavya", "Liam", "Lucas", "Maya",
    "Michael", "Mia", "Noah", "Olivia", "Pooja", "Rahul", "Rohan", "Sophia", "Thomas",
    "Vikram", "William", "Zara", "Oliver", "Emma", "Henry", "Ava", "Sebastian", "Isabella",
    "Mateo", "Mia", "Leo", "Amelia", "Jack", "Harper", "Julian", "Evelyn", "Levi", "Abigail"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts"
]

CONNECTOR_TYPES = ["CCS2", "Type 2", "CHAdeMO", "GB/T", "Tesla Supercharger"]
PORT_STATUSES = ["Available", "Occupied", "Reserved", "Under Maintenance", "Faulted"]
PORT_STATUS_WEIGHTS = [0.55, 0.25, 0.10, 0.05, 0.05]

VEHICLE_TYPES = ["2-Wheeler", "3-Wheeler", "Sedan", "SUV", "Hatchback", "Commercial Van", "Bus"]

COMPLAINT_ISSUES = [
    "Connector locking mechanism stuck in vehicle port",
    "Charging speed throttled below rated 150kW capacity",
    "Touchscreen terminal frozen on payment processing screen",
    "RFID card reader failed to authenticate customer card",
    "Physical damage observed on heavy charging cable insulation",
    "Emergency stop button was triggered and locked in pressed state",
    "App reported port Available but physical port display shows Error code 403",
    "Overheating error led to early session termination after 5 kWh",
    "Payment gateway timed out during final authorization",
    "LED indicator ring flashing red; unit non-responsive to mobile command"
]

def generate_all_data():
    operators = []
    stations = []
    ports = []
    prices = []
    users = []
    vehicles = []
    bookings = []
    sessions = []
    payments = []
    reviews = []
    complaints = []

    # 1. OPERATORS (15 rows)
    for op_id, name in enumerate(OPERATOR_NAMES, start=1):
        operators.append((op_id, name))

    # 2. STATIONS (45 rows) - Centered in diverse metropolitan areas
    station_id_counter = 1
    base_lat_lons = [
        (37.7749, -122.4194), # San Francisco
        (34.0522, -118.2437), # Los Angeles
        (40.7128, -74.0060),  # New York
        (51.5074, -0.1278),   # London
        (28.6139, 77.2090),   # New Delhi
        (19.0760, 72.8777),   # Mumbai
        (12.9716, 77.5946),   # Bengaluru
        (52.5200, 13.4050),   # Berlin
        (35.6762, 139.6503),  # Tokyo
    ]
    
    for op_id, _ in operators:
        # Each operator has 3 stations
        for _ in range(3):
            base_lat, base_lon = random.choice(base_lat_lons)
            lat = round(base_lat + random.uniform(-0.15, 0.15), 6)
            lon = round(base_lon + random.uniform(-0.15, 0.15), 6)
            stations.append((station_id_counter, op_id, lat, lon))
            station_id_counter += 1

    # 3. PORTS & 4. PRICES (180 ports across 45 stations, 4 ports per station)
    port_id_counter = 1
    price_id_counter = 1
    for st_id, _, _, _ in stations:
        num_ports = random.randint(3, 6)
        for _ in range(num_ports):
            c_type = random.choice(CONNECTOR_TYPES)
            p_status = random.choices(PORT_STATUSES, weights=PORT_STATUS_WEIGHTS)[0]
            ports.append((port_id_counter, st_id, c_type, p_status))
            
            # Base price depends on connector type speed
            if c_type in ["CCS2", "Tesla Supercharger"]:
                rate = round(random.uniform(0.38, 0.65), 2)
            elif c_type == "CHAdeMO":
                rate = round(random.uniform(0.32, 0.48), 2)
            else:
                rate = round(random.uniform(0.20, 0.35), 2)
                
            prices.append((price_id_counter, port_id_counter, rate))
            price_id_counter += 1
            port_id_counter += 1

    # 5. USERS (120 rows)
    used_phones = set()
    for u_id in range(1, 121):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        while True:
            phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            if phone not in used_phones:
                used_phones.add(phone)
                break
        users.append((u_id, name, phone))

    # 6. VEHICLES (150 rows)
    veh_id_counter = 1
    for u_id, _, _ in users:
        # Some users have 1 vehicle, some have 2
        num_v = random.choice([1, 1, 1, 2])
        for _ in range(num_v):
            v_type = random.choice(VEHICLE_TYPES)
            c_need = random.choice(CONNECTOR_TYPES)
            vehicles.append((veh_id_counter, u_id, v_type, c_need))
            veh_id_counter += 1

    # 7. BOOKINGS, 8. CHARGING_SESSIONS, 9. PAYMENTS (320 bookings)
    port_lookup = {p[0]: p for p in ports}
    price_lookup = {pr[1]: pr[2] for pr in prices} # port_id -> rate_per_kwh

    booking_id_counter = 1
    session_id_counter = 1
    payment_id_counter = 1

    base_time = datetime(2026, 6, 1, 8, 0, 0)

    for _ in range(320):
        u_id = random.choice(users)[0]
        port_id = random.choice(ports)[0]
        
        days_offset = random.randint(0, 85)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.choice([0, 15, 30, 45])
        start_time = base_time + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        status_choice = random.choices(["Completed", "Completed", "Completed", "In Progress", "Confirmed", "Cancelled"], weights=[0.65, 0.10, 0.05, 0.08, 0.07, 0.05])[0]
        bookings.append((booking_id_counter, u_id, port_id, start_time.strftime("%Y-%m-%d %H:%M:%S"), status_choice))
        
        # If completed or in progress, create session and payment
        if status_choice == "Completed":
            duration_minutes = random.randint(25, 90)
            end_time = start_time + timedelta(minutes=duration_minutes)
            energy = round(random.uniform(12.0, 78.5), 2)
            sessions.append((session_id_counter, booking_id_counter, energy, end_time.strftime("%Y-%m-%d %H:%M:%S")))
            
            # Payment based on energy * rate + fixed parking/service charge
            rate = price_lookup.get(port_id, 0.35)
            amount = round((energy * rate) + random.uniform(1.50, 3.00), 2)
            payments.append((payment_id_counter, booking_id_counter, amount))
            
            session_id_counter += 1
            payment_id_counter += 1
            
        booking_id_counter += 1

    # 10. REVIEWS (180 reviews)
    review_id_counter = 1
    user_station_pairs = set()
    for _ in range(180):
        u_id = random.choice(users)[0]
        st_id = random.choice(stations)[0]
        if (u_id, st_id) not in user_station_pairs:
            user_station_pairs.add((u_id, st_id))
            rating = random.choices([5, 4, 3, 2, 1], weights=[0.45, 0.30, 0.12, 0.08, 0.05])[0]
            reviews.append((review_id_counter, u_id, st_id, rating))
            review_id_counter += 1

    # 11. COMPLAINTS (60 complaints)
    complaint_id_counter = 1
    for _ in range(60):
        port_id = random.choice(ports)[0]
        issue = random.choice(COMPLAINT_ISSUES)
        c_status = random.choice(["Open", "In Progress", "Resolved", "Closed"])
        complaints.append((complaint_id_counter, port_id, issue, c_status))
        complaint_id_counter += 1

    return {
        "OPERATORS": operators,
        "STATIONS": stations,
        "PORTS": ports,
        "PRICES": prices,
        "USERS": users,
        "VEHICLES": vehicles,
        "BOOKINGS": bookings,
        "CHARGING_SESSIONS": sessions,
        "PAYMENTS": payments,
        "REVIEWS": reviews,
        "COMPLAINTS": complaints
    }

def write_sql_and_sqlite(data):
    # 1. Create SQL file
    sql_lines = [
        "-- ============================================================================",
        "-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK",
        "-- SCRIPT: DATA POPULATION (01_populate_data.sql)",
        "-- Populates all 11 tables with hundreds of referentially valid records",
        "-- ============================================================================\n"
    ]

    for table, rows in data.items():
        sql_lines.append(f"-- ----------------------------------------------------------------------------")
        sql_lines.append(f"-- Table: {table} ({len(rows)} rows)")
        sql_lines.append(f"-- ----------------------------------------------------------------------------")
        for r in rows:
            formatted_vals = []
            for val in r:
                if isinstance(val, str):
                    clean_val = val.replace("'", "''")
                    formatted_vals.append(f"'{clean_val}'")
                elif val is None:
                    formatted_vals.append("NULL")
                else:
                    formatted_vals.append(str(val))
            sql_lines.append(f"INSERT INTO {table} VALUES ({', '.join(formatted_vals)});")
        sql_lines.append("\n")

    SQL_OUTPUT_PATH.write_text("\n".join(sql_lines), encoding="utf-8")
    print(f"Generated SQL insert file at: {SQL_OUTPUT_PATH}")

    # 2. Populate SQLite database
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Apply Schema
    cursor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    cursor.executescript(INDEX_PATH.read_text(encoding="utf-8"))

    # Insert Data
    for table, rows in data.items():
        if not rows:
            continue
        placeholders = ", ".join(["?"] * len(rows[0]))
        cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)

    conn.commit()
    conn.close()
    print(f"Successfully populated SQLite database at: {DB_PATH}")

if __name__ == "__main__":
    datasets = generate_all_data()
    write_sql_and_sqlite(datasets)
