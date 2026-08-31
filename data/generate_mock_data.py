"""
EV Charging Station DBMS - Indian Localized Mock Data Generator
Generates realistic, referentially consistent records across all 12 tables
with Indian charging networks, cities, INR tariff rates, Indian EV models, and phone formats.
Exports both an SQL file (01_populate_data.sql) and populates local SQLite database (ev_charging.db).
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
VIEWS_PATH = BASE_DIR / "queries" / "08_views.sql"
TRIGGERS_PATH = BASE_DIR / "queries" / "09_procedures_triggers.sql"

# Reference Indian Datasets
OPERATOR_NAMES = [
    "Tata Power EZ Charge",
    "Jio-bp pulse",
    "Statiq EV Charging",
    "Ather Grid Network",
    "ChargeZone (TecSo)",
    "Magenta EV ChargeGrid",
    "Fortum Charge & Drive India",
    "Zeon Charging Network",
    "BPCL eDrive",
    "HPCL Electric",
    "IOCL EV Power",
    "Relux Electric Solutions",
    "BluSmart Mobility Hubs",
    "Kazam EV Infrastructure",
    "Servotech Power Systems"
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Dhruv", "Ananya", "Rohan", "Priya", "Vikram", "Sneha", "Rajesh", "Pooja",
    "Amit", "Neha", "Arjun", "Kavya", "Rahul", "Deepa", "Sanjay", "Divya", "Harsh", "Ankit",
    "Meera", "Suresh", "Tanvi", "Kunal", "Ritu", "Bhavin", "Manish", "Jignesh", "Chirag", "Parth",
    "Pratik", "Hardik", "Jayesh", "Hetal", "Urvi", "Nidhi", "Swati", "Alok", "Shreya", "Varun",
    "Gaurav", "Simran", "Naveen", "Ishaan", "Rhea", "Manan", "Akash", "Tanya", "Rishi", "Payal"
]

LAST_NAMES = [
    "Patel", "Shah", "Sharma", "Makwana", "Mehta", "Joshi", "Verma", "Gupta", "Singh", "Desai",
    "Trivedi", "Rao", "Nair", "Iyer", "Reddy", "Kulkarni", "Chatterjee", "Banerjee", "Mukherjee", "Das",
    "Bhatia", "Kapoor", "Malhotra", "Agarwal", "Choudhary", "Dave", "Shukla", "Bhatt", "Prajapati", "Panchal",
    "Solanki", "Gohil", "Mishra", "Pandey", "Saxena", "Chauhan", "Rathore", "Yadav", "Vyas", "Soni"
]

# Major Indian Cities & EV Corridors (Lat, Lon, City Name, Key Areas)
INDIAN_HUBS = [
    {"city": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "areas": ["SG Highway", "Prahlad Nagar", "Vastrapur", "Sindhu Bhavan", "Ashram Road", "Chandkheda", "Science City"]},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "areas": ["BKC Bandra", "Andheri East", "Lower Parel", "Powai Hiranandani", "Navi Mumbai Vashi", "Thane West"]},
    {"city": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "areas": ["Indiranagar 100ft Rd", "Whitefield ITPL", "Koramangala 4th Block", "Electronic City Phase 1", "HSR Layout", "MG Road"]},
    {"city": "New Delhi & NCR", "lat": 28.6139, "lon": 77.2090, "areas": ["Connaught Place", "Cyber City Gurugram", "Sector 62 Noida", "Aerocity Terminal 3", "Saket District Centre"]},
    {"city": "Pune", "lat": 18.5204, "lon": 73.8567, "areas": ["Hinjawadi Phase 1", "Viman Nagar", "Baner High Street", "Kothrud", "Magarpatta City"]},
    {"city": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "areas": ["Hitec City Cyber Towers", "Gachibowli Financial District", "Jubilee Hills Checkpost", "Madhapur"]},
    {"city": "Chennai", "lat": 13.0827, "lon": 80.2707, "areas": ["OMR IT Expressway", "Guindy Industrial Area", "Anna Nagar West", "T. Nagar"]},
    {"city": "Surat", "lat": 21.1702, "lon": 72.8311, "areas": ["Dumas Road", "Vesu VIP Road", "Adajan", "Ghod Dod Road"]},
    {"city": "Jaipur", "lat": 26.9124, "lon": 75.7873, "areas": ["Malviya Nagar", "Mansarovar", "C-Scheme", "Tonk Road"]},
    {"city": "Kolkata", "lat": 22.5726, "lon": 88.3639, "areas": ["Salt Lake Sector V", "New Town Eco Park", "Park Street", "Rajarhat"]}
]

CONNECTOR_TYPES = ["CCS2", "Type 2", "GB/T", "CHAdeMO", "Tesla Supercharger"]
PORT_STATUSES = ["Available", "Occupied", "Reserved", "Under Maintenance", "Faulted"]
PORT_STATUS_WEIGHTS = [0.52, 0.28, 0.10, 0.05, 0.05]

VEHICLE_TYPES = ["2-Wheeler", "3-Wheeler", "Sedan", "SUV", "Hatchback", "Commercial Van", "Bus"]

INDIAN_EV_MODELS = [
    ("Tata Nexon EV Max", "SUV", "CCS2"),
    ("Tata Punch EV", "SUV", "CCS2"),
    ("Tata Tiago EV", "Hatchback", "CCS2"),
    ("Mahindra XUV400 EV", "SUV", "CCS2"),
    ("MG ZS EV", "SUV", "CCS2"),
    ("Hyundai Ioniq 5", "SUV", "CCS2"),
    ("BYD Atto 3", "SUV", "CCS2"),
    ("Ola S1 Pro Gen 2", "2-Wheeler", "Type 2"),
    ("Ather 450X Apex", "2-Wheeler", "Type 2"),
    ("TVS iQube Electric", "2-Wheeler", "Type 2"),
    ("Bajaj Chetak Premium", "2-Wheeler", "Type 2"),
    ("Mahindra Treo Zor", "3-Wheeler", "GB/T"),
    ("Tata Ace EV", "Commercial Van", "CCS2"),
    ("Olectra Electric City Bus", "Bus", "CCS2")
]

COMPLAINT_ISSUES = [
    "CCS2 gun lock latch mechanism jammed in Tata Nexon socket",
    "Charging speed throttled to 15kW on 60kW DC Fast charger",
    "Touchscreen terminal frozen during UPI QR code payment generation",
    "RFID card reader failed to authenticate customer wallet card",
    "Heavy wear and physical insulation tear on DC fast charging cable",
    "Emergency stop button was triggered and stuck in depressed state",
    "App reported port Available but physical dispenser shows Error 403",
    "Thermal cut-off triggered high temperature shutdown after 8.5 kWh",
    "Razorpay / Paytm UPI payment timed out during authorization",
    "Status LED ring flashing red error code; unresponsive to mobile trigger"
]

REFUND_REASONS = [
    "Charging terminated abruptly after 2 kWh due to grid fault",
    "Overbilled due to incorrect peak tariff calculation",
    "Port dispenser stalled; customer charged double on retry",
    "Session could not initiate; card debited prior to connection",
    "Slot cancelled 45 minutes prior to booking window"
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
    refunds = []

    # 1. OPERATORS (15 rows)
    for op_id, name in enumerate(OPERATOR_NAMES, start=1):
        operators.append((op_id, name))

    # 2. STATIONS (45 rows distributed across major Indian cities)
    station_id_counter = 1
    for op_id, _ in operators:
        # Each operator gets 3 stations located across different Indian hubs
        for _ in range(3):
            hub = random.choice(INDIAN_HUBS)
            lat = round(hub["lat"] + random.uniform(-0.06, 0.06), 6)
            lon = round(hub["lon"] + random.uniform(-0.06, 0.06), 6)
            stations.append((station_id_counter, op_id, lat, lon))
            station_id_counter += 1

    # 3. PORTS & 4. PRICES (180 ports across 45 stations, 3-6 ports per station)
    port_id_counter = 1
    price_id_counter = 1
    for st_id, _, _, _ in stations:
        num_ports = random.randint(3, 6)
        for _ in range(num_ports):
            # In India, CCS2 and Type 2 are most prevalent
            c_type = random.choices(CONNECTOR_TYPES, weights=[0.50, 0.30, 0.10, 0.05, 0.05])[0]
            p_status = random.choices(PORT_STATUSES, weights=PORT_STATUS_WEIGHTS)[0]
            ports.append((port_id_counter, st_id, c_type, p_status))
            
            # Realistic Indian INR Rates (₹/kWh)
            if c_type in ["CCS2", "Tesla Supercharger"]:
                rate = round(random.uniform(18.50, 24.00), 2)
            elif c_type == "CHAdeMO":
                rate = round(random.uniform(16.00, 20.00), 2)
            elif c_type == "GB/T":
                rate = round(random.uniform(14.00, 18.00), 2)
            else: # Type 2 AC
                rate = round(random.uniform(11.50, 15.50), 2)
                
            prices.append((price_id_counter, port_id_counter, rate))
            price_id_counter += 1
            port_id_counter += 1

    # 5. USERS (120 Indian Drivers)
    used_phones = set()
    sample_prefixes = ["98765", "98250", "94280", "87800", "70160", "99090", "91060", "97270", "98980", "93770"]
    
    # Specific pre-defined users for testing/demo
    demo_users = [
        ("Aarav Patel", "+91-98765-43210"),
        ("Dhruv Makwana", "+91-94280-11223"),
        ("Ananya Shah", "+91-98250-99887"),
        ("Priya Sharma", "+91-87800-44556"),
        ("Vikram Singh", "+91-70160-55667")
    ]
    
    for u_id in range(1, 121):
        if u_id <= len(demo_users):
            name, phone = demo_users[u_id - 1]
            used_phones.add(phone)
        else:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            while True:
                prefix = random.choice(sample_prefixes)
                suffix = random.randint(10000, 99999)
                phone = f"+91-{prefix}-{suffix}"
                if phone not in used_phones:
                    used_phones.add(phone)
                    break
        users.append((u_id, name, phone))

    # 6. VEHICLES (150 Indian registered EVs)
    veh_id_counter = 1
    for u_id, _, _ in users:
        num_v = random.choice([1, 1, 1, 2])
        for _ in range(num_v):
            model_info = random.choice(INDIAN_EV_MODELS)
            v_type = model_info[1]
            c_need = model_info[2]
            vehicles.append((veh_id_counter, u_id, v_type, c_need))
            veh_id_counter += 1

    # 7. BOOKINGS, 8. CHARGING_SESSIONS, 9. PAYMENTS (320 Bookings)
    price_lookup = {pr[1]: pr[2] for pr in prices} # port_id -> rate_per_kwh

    booking_id_counter = 1
    session_id_counter = 1
    payment_id_counter = 1

    base_time = datetime(2026, 6, 1, 8, 0, 0)

    for _ in range(320):
        u_id = random.choice(users)[0]
        port_id = random.choice(ports)[0]
        
        days_offset = random.randint(0, 88)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.choice([0, 15, 30, 45])
        start_time = base_time + timedelta(days=days_offset, hours=hours_offset, minutes=minutes_offset)
        
        status_choice = random.choices(["Completed", "Completed", "Completed", "In Progress", "Confirmed", "Cancelled"], weights=[0.65, 0.10, 0.05, 0.08, 0.07, 0.05])[0]
        bookings.append((booking_id_counter, u_id, port_id, start_time.strftime("%Y-%m-%d %H:%M:%S"), status_choice))
        
        # If completed or in progress, create session and payment
        if status_choice == "Completed":
            duration_minutes = random.randint(25, 80)
            end_time = start_time + timedelta(minutes=duration_minutes)
            energy = round(random.uniform(14.0, 52.5), 2)
            sessions.append((session_id_counter, booking_id_counter, energy, end_time.strftime("%Y-%m-%d %H:%M:%S")))
            
            # Payment in INR: Energy * Rate + ₹25 base connection charge + 5% GST
            rate = price_lookup.get(port_id, 18.50)
            subtotal = (energy * rate) + 25.00
            amount = round(subtotal * 1.05, 2)
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
            rating = random.choices([5, 4, 3, 2, 1], weights=[0.48, 0.32, 0.10, 0.06, 0.04])[0]
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

    # 12. REFUNDS (20 initial refund records linked to settled payments)
    refund_id_counter = 1
    sample_payments = random.sample(payments, 20)
    for pay in sample_payments:
        pay_id = pay[0]
        bk_id = pay[1]
        orig_amount = pay[2]
        # Partial or full refund in INR
        refund_amt = round(random.choice([orig_amount, orig_amount * 0.5, orig_amount * 0.75]), 2)
        reason = random.choice(REFUND_REASONS)
        ref_time = (base_time + timedelta(days=random.randint(10, 85), hours=random.randint(9, 20))).strftime("%Y-%m-%d %H:%M:%S")
        status = random.choice(["Processed", "Processed", "Processed", "Pending"])
        refunds.append((refund_id_counter, pay_id, bk_id, refund_amt, reason, ref_time, status))
        refund_id_counter += 1

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
        "COMPLAINTS": complaints,
        "REFUNDS": refunds
    }

def write_sql_and_sqlite(data):
    # 1. Create SQL file
    sql_lines = [
        "-- ============================================================================",
        "-- DATABASE MANAGEMENT SYSTEM: EV CHARGING STATION NETWORK (INDIA LOCALIZED)",
        "-- SCRIPT: DATA POPULATION (01_populate_data.sql)",
        "-- Populates all 12 tables with hundreds of referentially valid Indian records",
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

    # Apply Schema & Indexes
    cursor.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    cursor.executescript(INDEX_PATH.read_text(encoding="utf-8"))

    # Insert Data
    for table, rows in data.items():
        if not rows:
            continue
        placeholders = ", ".join(["?"] * len(rows[0]))
        cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)

    # Apply Views and Triggers
    if VIEWS_PATH.exists():
        cursor.executescript(VIEWS_PATH.read_text(encoding="utf-8"))
    if TRIGGERS_PATH.exists():
        cursor.executescript(TRIGGERS_PATH.read_text(encoding="utf-8"))

    conn.commit()
    conn.close()
    print(f"Successfully populated SQLite database at: {DB_PATH}")

if __name__ == "__main__":
    datasets = generate_all_data()
    write_sql_and_sqlite(datasets)
