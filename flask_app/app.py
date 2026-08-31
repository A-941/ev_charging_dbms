"""
VoltGrid India - EV Charging Station DBMS Web Application
Features:
1. Role-Based Access Control (RBAC) with Flask sessions and @login_required / @admin_required decorators.
2. 100% Free Live Ahmedabad EV Station Location Finder powered by OpenStreetMap Nominatim & Overpass API.
3. Full-width horizontal dashboard with real-time port telemetry (Available, Occupied, Reserved, Faulted).
4. Merged Session Lifecycle & Refund Management (Slot reservation -> Energy settlement in INR -> Instant receipts & Refund log).
5. Admin-exclusive SQL Query Workbench with Indian syllabus demonstration queries.
"""

import math
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify

from ev_api_service import get_nearest_ahmedabad_stations, REAL_AHMEDABAD_EV_HUBS

app = Flask(__name__)
app.secret_key = "voltgrid_india_ahmedabad_ev_dbms_secret_2026"

DB_PATH = Path(__file__).resolve().parent.parent / "ev_charging.db"

# Popular Indian EV Models
INDIAN_EV_MODELS = [
    {"name": "Tata Nexon EV Max / Long Range", "type": "SUV", "connector": "CCS2"},
    {"name": "Tata Punch EV", "type": "SUV", "connector": "CCS2"},
    {"name": "Tata Tiago EV", "type": "Hatchback", "connector": "CCS2"},
    {"name": "Mahindra XUV400 EV", "type": "SUV", "connector": "CCS2"},
    {"name": "MG ZS EV Executive", "type": "SUV", "connector": "CCS2"},
    {"name": "Hyundai Ioniq 5 / Kia EV6", "type": "SUV", "connector": "CCS2"},
    {"name": "BYD Atto 3 / Seal", "type": "Sedan", "connector": "CCS2"},
    {"name": "Ola S1 Pro (Gen 2)", "type": "2-Wheeler", "connector": "Type 2"},
    {"name": "Ather 450X / 450 Apex", "type": "2-Wheeler", "connector": "Type 2"},
    {"name": "TVS iQube ST Electric", "type": "2-Wheeler", "connector": "Type 2"},
    {"name": "Bajaj Chetak Premium", "type": "2-Wheeler", "connector": "Type 2"},
    {"name": "Mahindra Treo Zor E-Cargo", "type": "3-Wheeler", "connector": "GB/T"},
    {"name": "Tata Ace EV Commercial", "type": "Commercial Van", "connector": "CCS2"}
]

# Popular Ahmedabad Localities for Quick Filtering
AHMEDABAD_HOTSPOTS = [
    "Sindhu Bhavan Road", "Prahlad Nagar", "Vastrapur", "SG Highway",
    "Maninagar", "Motera (Stadium)", "Chandkheda", "Ashram Road",
    "Navrangpura (C.G. Road)", "South Bopal", "Sabarmati Riverfront", "Thaltej"
]

def get_db_connection():
    """Returns a SQLite connection with Foreign Keys and Row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -----------------------------------------------------------------------------
# CONTEXT PROCESSOR & RBAC DECORATORS
# -----------------------------------------------------------------------------
@app.context_processor
def inject_user_context():
    """Injects user authentication and authorization details into all Jinja templates."""
    user_id = session.get("user_id")
    role = session.get("role")
    name = session.get("name")
    phone = session.get("phone")
    return {
        "current_user": {
            "id": user_id,
            "name": name,
            "phone": phone,
            "role": role,
            "is_authenticated": user_id is not None,
            "is_admin": role == "admin"
        },
        "indian_ev_models": INDIAN_EV_MODELS,
        "ahmedabad_hotspots": AHMEDABAD_HOTSPOTS
    }

def login_required(f):
    """Route decorator: Requires user to be logged in (either User or Admin)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("⚠️ Please log in to access this feature.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Route decorator: Requires user to be logged in with role == 'admin'."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("🔒 Please log in as an Administrator.", "warning")
            return redirect(url_for("login", next=request.url))
        if session.get("role") != "admin":
            flash("⛔ Access Denied: This administrative feature (SQL Workbench / System Management) is strictly restricted to Admin accounts.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES (LOGIN / LOGOUT / REGISTER)
# -----------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_type = request.form.get("login_type", "user")
        next_url = request.args.get("next") or url_for("index")

        conn = get_db_connection()
        try:
            # 1. Admin Login
            if login_type == "admin":
                username = request.form.get("admin_username", "").strip()
                password = request.form.get("admin_password", "").strip()
                
                if (username.lower() in ["admin", "operator", "root", "manager"]) and (password in ["admin123", "admin", "voltgrid2026", "password"]):
                    session["user_id"] = 0
                    session["name"] = "System Administrator"
                    session["phone"] = "+91-99999-00000"
                    session["role"] = "admin"
                    flash("⚡ Welcome, System Administrator! Full platform controls and SQL Workbench are unlocked.", "success")
                    return redirect(next_url)
                else:
                    flash("❌ Invalid Admin credentials. Demo credentials: username 'admin' / password 'admin123'", "danger")
                    return redirect(url_for("login", tab="admin"))

            # 2. Quick Demo User Switch
            elif login_type == "quick_user":
                target_user_id = int(request.form.get("demo_user_id", 1))
                user_row = conn.execute("SELECT user_id, name, phone FROM USERS WHERE user_id = ?", (target_user_id,)).fetchone()
                if user_row:
                    session["user_id"] = user_row["user_id"]
                    session["name"] = user_row["name"]
                    session["phone"] = user_row["phone"]
                    session["role"] = "user"
                    flash(f"👋 Logged in as {user_row['name']} ({user_row['phone']}).", "success")
                    return redirect(next_url)

            # 3. Regular Driver Login by Phone or Name
            elif login_type == "user":
                search_term = request.form.get("user_identifier", "").strip()
                if not search_term:
                    flash("❌ Please enter your phone number or name.", "warning")
                    return redirect(url_for("login"))

                user_row = conn.execute("""
                    SELECT user_id, name, phone FROM USERS 
                    WHERE phone = ? OR phone LIKE ? OR LOWER(name) = LOWER(?)
                    LIMIT 1
                """, (search_term, f"%{search_term}%", search_term)).fetchone()

                if user_row:
                    session["user_id"] = user_row["user_id"]
                    session["name"] = user_row["name"]
                    session["phone"] = user_row["phone"]
                    session["role"] = "user"
                    flash(f"👋 Welcome back, {user_row['name']}!", "success")
                    return redirect(next_url)
                else:
                    flash(f"❓ No account found for '{search_term}'. You can register below in seconds.", "info")
                    return redirect(url_for("login", tab="register", prefill=search_term))

            # 4. New User Registration
            elif login_type == "register":
                new_name = request.form.get("new_name", "").strip()
                new_phone = request.form.get("new_phone", "").strip()
                vehicle_type = request.form.get("vehicle_type", "SUV")
                connector_needed = request.form.get("connector_needed", "CCS2")

                if not new_name or not new_phone:
                    flash("❌ Name and phone number are required.", "danger")
                    return redirect(url_for("login", tab="register"))

                # Ensure Indian phone format prefix
                if not new_phone.startswith("+91") and not new_phone.startswith("+"):
                    clean_digits = "".join(filter(str.isdigit, new_phone))
                    if len(clean_digits) == 10:
                        new_phone = f"+91-{clean_digits[:5]}-{clean_digits[5:]}"
                    else:
                        new_phone = f"+91-{new_phone}"

                # Check if phone already exists
                existing = conn.execute("SELECT user_id, name FROM USERS WHERE phone = ?", (new_phone,)).fetchone()
                if existing:
                    session["user_id"] = existing["user_id"]
                    session["name"] = existing["name"]
                    session["phone"] = new_phone
                    session["role"] = "user"
                    flash(f"👋 Phone already registered! Logged in as {existing['name']}.", "info")
                    return redirect(next_url)

                next_uid = conn.execute("SELECT COALESCE(MAX(user_id), 0) + 1 FROM USERS").fetchone()[0]
                next_vid = conn.execute("SELECT COALESCE(MAX(vehicle_id), 0) + 1 FROM VEHICLES").fetchone()[0]

                conn.execute("INSERT INTO USERS (user_id, name, phone) VALUES (?, ?, ?)", (next_uid, new_name, new_phone))
                conn.execute("INSERT INTO VEHICLES (vehicle_id, user_id, type, connector_needed) VALUES (?, ?, ?, ?)",
                             (next_vid, next_uid, vehicle_type, connector_needed))
                conn.commit()

                session["user_id"] = next_uid
                session["name"] = new_name
                session["phone"] = new_phone
                session["role"] = "user"
                flash(f"🎉 Account created successfully! Welcome to VoltGrid India, {new_name}.", "success")
                return redirect(next_url)

        except Exception as e:
            conn.rollback()
            flash(f"❌ Login error: {str(e)}", "danger")
        finally:
            conn.close()

    # GET request - fetch demo users for quick select
    conn = get_db_connection()
    try:
        sample_users = conn.execute("SELECT user_id, name, phone FROM USERS ORDER BY user_id ASC LIMIT 5").fetchall()
    finally:
        conn.close()

    tab = request.args.get("tab", "user")
    prefill = request.args.get("prefill", "")
    return render_template("login.html", sample_users=sample_users, active_tab=tab, prefill=prefill)

@app.route("/logout")
def logout():
    """Clears user session and logs out."""
    name = session.get("name", "User")
    session.clear()
    flash(f"🔒 You have been logged out. See you next time, {name}!", "info")
    return redirect(url_for("index"))

# -----------------------------------------------------------------------------
# 1. API ROUTE: LIVE AHMEDABAD EV STATIONS (FREE OVERPASS & NOMINATIM)
# -----------------------------------------------------------------------------
@app.route("/api/nearest-stations", methods=["GET", "POST"])
def api_nearest_stations():
    """
    100% Free API endpoint returning nearest Ahmedabad EV charging stations
    sorted by distance (km) using Haversine calculation, OpenStreetMap Overpass live nodes,
    and Nominatim geocoding.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        user_lat = data.get("lat")
        user_lon = data.get("lon")
        locality = data.get("locality") or data.get("query")
        connector = data.get("connector", "ALL")
    else:
        user_lat = request.args.get("lat")
        user_lon = request.args.get("lon")
        locality = request.args.get("locality") or request.args.get("query") or "Sindhu Bhavan Road"
        connector = request.args.get("connector", "ALL")

    try:
        lat_float = float(user_lat) if user_lat is not None and str(user_lat).strip() != "" else None
        lon_float = float(user_lon) if user_lon is not None and str(user_lon).strip() != "" else None
    except (ValueError, TypeError):
        lat_float = None
        lon_float = None

    response_data = get_nearest_ahmedabad_stations(
        user_lat=lat_float,
        user_lon=lon_float,
        locality_query=locality,
        connector_filter=connector,
        max_results=12
    )

    return jsonify(response_data)

# -----------------------------------------------------------------------------
# 2. HOME / REDESIGNED HORIZONTAL DASHBOARD ROUTE
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    try:
        # High-level network statistics in INR
        stats = {
            "operators": conn.execute("SELECT COUNT(*) FROM OPERATORS").fetchone()[0],
            "stations": conn.execute("SELECT COUNT(*) FROM STATIONS").fetchone()[0],
            "ports": conn.execute("SELECT COUNT(*) FROM PORTS").fetchone()[0],
            "available_ports": conn.execute("SELECT COUNT(*) FROM PORTS WHERE status = 'Available'").fetchone()[0],
            "occupied_ports": conn.execute("SELECT COUNT(*) FROM PORTS WHERE status = 'Occupied'").fetchone()[0],
            "reserved_ports": conn.execute("SELECT COUNT(*) FROM PORTS WHERE status = 'Reserved'").fetchone()[0],
            "faulted_ports": conn.execute("SELECT COUNT(*) FROM PORTS WHERE status IN ('Faulted', 'Under Maintenance')").fetchone()[0],
            "bookings": conn.execute("SELECT COUNT(*) FROM BOOKINGS").fetchone()[0],
            "sessions": conn.execute("SELECT COUNT(*) FROM CHARGING_SESSIONS").fetchone()[0],
            "energy_kwh": conn.execute("SELECT ROUND(COALESCE(SUM(energy_kwh), 0), 1) FROM CHARGING_SESSIONS").fetchone()[0],
            "revenue": conn.execute("SELECT ROUND(COALESCE(SUM(amount), 0), 2) FROM PAYMENTS").fetchone()[0],
            "refunds_count": conn.execute("SELECT COUNT(*) FROM REFUNDS").fetchone()[0] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='REFUNDS'").fetchone() else 0,
            "open_complaints": conn.execute("SELECT COUNT(*) FROM COMPLAINTS WHERE status = 'Open'").fetchone()[0]
        }

        # Live Station Matrix from v_station_live_status View
        stations = conn.execute("""
            SELECT s.station_id, op.company_name AS operator_name, s.latitude, s.longitude, 
                   COUNT(p.port_id) AS total_ports,
                   SUM(CASE WHEN p.status = 'Available' THEN 1 ELSE 0 END) AS available_ports,
                   SUM(CASE WHEN p.status = 'Occupied' THEN 1 ELSE 0 END) AS occupied_ports,
                   SUM(CASE WHEN p.status = 'Reserved' THEN 1 ELSE 0 END) AS reserved_ports,
                   SUM(CASE WHEN p.status IN ('Faulted', 'Under Maintenance') THEN 1 ELSE 0 END) AS offline_ports,
                   ROUND(COALESCE(AVG(r.rating), 4.7), 1) AS avg_rating,
                   GROUP_CONCAT(DISTINCT p.connector_type) AS connector_types
            FROM STATIONS s
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            LEFT JOIN PORTS p ON s.station_id = p.station_id
            LEFT JOIN REVIEWS r ON s.station_id = r.station_id
            GROUP BY s.station_id, op.company_name, s.latitude, s.longitude
            ORDER BY available_ports DESC, s.station_id ASC
            LIMIT 12
        """).fetchall()

        # Fetch Recent Bookings (Personalized for User, Global for Admin)
        current_uid = session.get("user_id")
        user_role = session.get("role")

        if user_role == "user" and current_uid:
            recent_bookings = conn.execute("""
                SELECT b.booking_id, u.name AS user_name, u.phone, b.port_id, p.connector_type, 
                       op.company_name, s.station_id, pr.rate_per_kwh, b.start_time, b.status,
                       cs.energy_kwh, pay.amount AS paid_amount
                FROM BOOKINGS b
                JOIN USERS u ON b.user_id = u.user_id
                JOIN PORTS p ON b.port_id = p.port_id
                JOIN STATIONS s ON p.station_id = s.station_id
                JOIN OPERATORS op ON s.operator_id = op.operator_id
                LEFT JOIN PRICES pr ON p.port_id = pr.port_id
                LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
                LEFT JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
                WHERE b.user_id = ?
                ORDER BY b.booking_id DESC
                LIMIT 10
            """, (current_uid,)).fetchall()
        else:
            recent_bookings = conn.execute("""
                SELECT b.booking_id, u.name AS user_name, u.phone, b.port_id, p.connector_type, 
                       op.company_name, s.station_id, pr.rate_per_kwh, b.start_time, b.status,
                       cs.energy_kwh, pay.amount AS paid_amount
                FROM BOOKINGS b
                JOIN USERS u ON b.user_id = u.user_id
                JOIN PORTS p ON b.port_id = p.port_id
                JOIN STATIONS s ON p.station_id = s.station_id
                JOIN OPERATORS op ON s.operator_id = op.operator_id
                LEFT JOIN PRICES pr ON p.port_id = pr.port_id
                LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
                LEFT JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
                ORDER BY b.booking_id DESC
                LIMIT 10
            """).fetchall()

        # Admin-specific metrics
        operator_financials = []
        open_complaints_list = []
        if user_role == "admin":
            operator_financials = conn.execute("""
                SELECT * FROM v_operator_financial_summary ORDER BY gross_revenue DESC LIMIT 8
            """).fetchall()

            open_complaints_list = conn.execute("""
                SELECT c.complaint_id, c.port_id, op.company_name, p.connector_type, c.issue, c.status
                FROM COMPLAINTS c
                JOIN PORTS p ON c.port_id = p.port_id
                JOIN STATIONS s ON p.station_id = s.station_id
                JOIN OPERATORS op ON s.operator_id = op.operator_id
                WHERE c.status IN ('Open', 'In Progress')
                ORDER BY c.complaint_id DESC
                LIMIT 6
            """).fetchall()

        # Default initial Ahmedabad stations seed for server-rendered fallback
        initial_ahmedabad_stations = REAL_AHMEDABAD_EV_HUBS[:6]

        return render_template(
            "index.html",
            stats=stats,
            stations=stations,
            bookings=recent_bookings,
            operator_financials=operator_financials,
            open_complaints=open_complaints_list,
            initial_ahmedabad_stations=initial_ahmedabad_stations
        )
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 3. MERGED SESSION LIFECYCLE & REFUND MANAGEMENT ROUTE
# -----------------------------------------------------------------------------
@app.route("/booking-payment", methods=["GET", "POST"])
@app.route("/session-manager", methods=["GET", "POST"])
def unified_booking_payment():
    conn = get_db_connection()
    try:
        active_tab = request.args.get("tab", "reserve")
        preselected_port = request.args.get("port_id")
        preselected_station = request.args.get("station_id")

        if request.method == "POST":
            form_action = request.form.get("action")

            # -----------------------------------------------------------------
            # PHASE 1: RESERVE CHARGING SLOT
            # -----------------------------------------------------------------
            if form_action == "reserve":
                driver_name = request.form.get("driver_name", "").strip()
                driver_phone = request.form.get("driver_phone", "").strip()
                port_id = int(request.form.get("port_id"))
                start_time = request.form.get("start_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                vehicle_model = request.form.get("vehicle_model", "")

                if not driver_name or not driver_phone:
                    flash("❌ Driver name and phone number are required.", "danger")
                    return redirect(url_for("unified_booking_payment", tab="reserve"))

                # Format phone cleanly
                if not driver_phone.startswith("+91") and not driver_phone.startswith("+"):
                    clean_p = "".join(filter(str.isdigit, driver_phone))
                    if len(clean_p) == 10:
                        driver_phone = f"+91-{clean_p[:5]}-{clean_p[5:]}"
                    else:
                        driver_phone = f"+91-{driver_phone}"

                # 1. Lookup or create User in USERS table
                user_row = conn.execute("SELECT user_id FROM USERS WHERE phone = ?", (driver_phone,)).fetchone()
                if user_row:
                    user_id = user_row["user_id"]
                    conn.execute("UPDATE USERS SET name = ? WHERE user_id = ?", (driver_name, user_id))
                else:
                    user_id = conn.execute("SELECT COALESCE(MAX(user_id), 0) + 1 FROM USERS").fetchone()[0]
                    conn.execute("INSERT INTO USERS (user_id, name, phone) VALUES (?, ?, ?)", (user_id, driver_name, driver_phone))

                # 2. Check Port availability
                port_row = conn.execute("SELECT status, connector_type FROM PORTS WHERE port_id = ?", (port_id,)).fetchone()
                if not port_row or port_row["status"] != "Available":
                    flash(f"⚠️ Port #{port_id} is currently {port_row['status'] if port_row else 'Unavailable'}. Please select another port.", "warning")
                    return redirect(url_for("unified_booking_payment", tab="reserve"))

                # 3. Create Booking (Trigger automatically updates Port to 'Reserved')
                next_bid = conn.execute("SELECT COALESCE(MAX(booking_id), 0) + 1 FROM BOOKINGS").fetchone()[0]
                conn.execute(
                    "INSERT INTO BOOKINGS (booking_id, user_id, port_id, start_time, status) VALUES (?, ?, ?, ?, 'Confirmed')",
                    (next_bid, user_id, port_id, start_time)
                )

                # Set session if not logged in
                if "user_id" not in session:
                    session["user_id"] = user_id
                    session["name"] = driver_name
                    session["phone"] = driver_phone
                    session["role"] = "user"

                conn.commit()
                flash(f"✅ Slot Reserved successfully! Booking #{next_bid} confirmed for {driver_name} on Port #{port_id} ({port_row['connector_type']}). Port is now Reserved.", "success")
                return redirect(url_for("unified_booking_payment", tab="settle", highlight=next_bid))

            # -----------------------------------------------------------------
            # PHASE 2: ACTIVE SESSION & ENERGY SETTLEMENT
            # -----------------------------------------------------------------
            elif form_action == "settle":
                booking_id = int(request.form.get("booking_id"))
                energy_kwh = float(request.form.get("energy_kwh", 25.0))
                end_time = request.form.get("end_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                booking_info = conn.execute("""
                    SELECT b.booking_id, b.user_id, b.port_id, b.status, pr.rate_per_kwh, u.name AS user_name
                    FROM BOOKINGS b
                    JOIN PORTS p ON b.port_id = p.port_id
                    JOIN PRICES pr ON p.port_id = pr.port_id
                    JOIN USERS u ON b.user_id = u.user_id
                    WHERE b.booking_id = ?
                """, (booking_id,)).fetchone()

                if not booking_info:
                    flash("❌ Booking record not found.", "danger")
                    return redirect(url_for("unified_booking_payment", tab="settle"))

                if booking_info["status"] == "Completed":
                    flash(f"ℹ️ Booking #{booking_id} has already been settled and completed.", "info")
                    return redirect(url_for("unified_booking_payment", tab="payments"))

                rate = booking_info["rate_per_kwh"]
                base_charge = 25.00 # ₹25 base connection charge in India
                subtotal = (energy_kwh * rate) + base_charge
                tax_amount = round(subtotal * 0.05, 2) # 5% GST
                total_amount = round(subtotal + tax_amount, 2)

                next_sid = conn.execute("SELECT COALESCE(MAX(session_id), 0) + 1 FROM CHARGING_SESSIONS").fetchone()[0]
                next_pid = conn.execute("SELECT COALESCE(MAX(payment_id), 0) + 1 FROM PAYMENTS").fetchone()[0]

                # Insert Session & Payment, Complete Booking (Trigger releases Port to Available)
                conn.execute(
                    "INSERT INTO CHARGING_SESSIONS (session_id, booking_id, energy_kwh, end_time) VALUES (?, ?, ?, ?)",
                    (next_sid, booking_id, energy_kwh, end_time)
                )
                conn.execute(
                    "INSERT INTO PAYMENTS (payment_id, booking_id, amount) VALUES (?, ?, ?)",
                    (next_pid, booking_id, total_amount)
                )
                conn.execute("UPDATE BOOKINGS SET status = 'Completed' WHERE booking_id = ?", (booking_id,))

                conn.commit()
                flash(f"⚡ Session #{next_sid} Logged ({energy_kwh} kWh @ ₹{rate}/kWh) & Payment #{next_pid} (₹{total_amount:.2f} incl. GST) Settled! Port #{booking_info['port_id']} released to Available.", "success")
                return redirect(url_for("unified_booking_payment", tab="payments", highlight_pay=next_pid))

            # -----------------------------------------------------------------
            # PHASE 3: PROCESS REFUND MODULE
            # -----------------------------------------------------------------
            elif form_action == "refund":
                payment_id = int(request.form.get("payment_id"))
                reason = request.form.get("reason", "Customer Billing Adjustment").strip()
                refund_amount_input = request.form.get("refund_amount")

                pay_row = conn.execute("""
                    SELECT p.payment_id, p.booking_id, p.amount, u.name AS user_name
                    FROM PAYMENTS p
                    JOIN BOOKINGS b ON p.booking_id = b.booking_id
                    JOIN USERS u ON b.user_id = u.user_id
                    WHERE p.payment_id = ?
                """, (payment_id,)).fetchone()

                if not pay_row:
                    flash("❌ Payment record not found.", "danger")
                    return redirect(url_for("unified_booking_payment", tab="payments"))

                orig_amount = pay_row["amount"]
                refund_amt = float(refund_amount_input) if refund_amount_input else orig_amount

                if refund_amt > orig_amount:
                    flash(f"❌ Refund amount (₹{refund_amt:.2f}) cannot exceed settled payment (₹{orig_amount:.2f}).", "danger")
                    return redirect(url_for("unified_booking_payment", tab="payments"))

                # Check if refund already processed
                existing_refund = conn.execute("SELECT refund_id FROM REFUNDS WHERE payment_id = ?", (payment_id,)).fetchone()
                if existing_refund:
                    flash(f"⚠️ A refund (Refund #{existing_refund['refund_id']}) has already been initiated for Payment #{payment_id}.", "warning")
                    return redirect(url_for("unified_booking_payment", tab="payments"))

                next_rid = conn.execute("SELECT COALESCE(MAX(refund_id), 0) + 1 FROM REFUNDS").fetchone()[0]
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(
                    "INSERT INTO REFUNDS (refund_id, payment_id, booking_id, amount, reason, refund_time, status) VALUES (?, ?, ?, ?, ?, ?, 'Processed')",
                    (next_rid, payment_id, pay_row["booking_id"], refund_amt, reason, now_str)
                )
                conn.execute("UPDATE BOOKINGS SET status = 'Cancelled' WHERE booking_id = ?", (pay_row["booking_id"],))

                conn.commit()
                flash(f"💸 Refund #{next_rid} of ₹{refund_amt:.2f} successfully processed for Payment #{payment_id} ({pay_row['user_name']})! Reason: {reason}.", "success")
                return redirect(url_for("unified_booking_payment", tab="payments"))

        # ---------------------------------------------------------------------
        # GET REQUEST: PREPARE DATA FOR ALL TABS
        # ---------------------------------------------------------------------
        # 1. Available Ports
        available_ports = conn.execute("""
            SELECT p.port_id, s.station_id, op.company_name, p.connector_type, pr.rate_per_kwh,
                   s.latitude, s.longitude
            FROM PORTS p
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE p.status = 'Available'
            ORDER BY s.station_id ASC, p.port_id ASC
        """).fetchall()

        # 2. Active Bookings
        current_uid = session.get("user_id")
        user_role = session.get("role")

        active_query = """
            SELECT b.booking_id, u.name AS user_name, u.phone, b.port_id, p.connector_type, 
                   op.company_name, pr.rate_per_kwh, b.start_time, b.status
            FROM BOOKINGS b
            JOIN USERS u ON b.user_id = u.user_id
            JOIN PORTS p ON b.port_id = p.port_id
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE b.status IN ('Confirmed', 'In Progress')
        """
        if user_role == "user" and current_uid:
            active_query += " AND b.user_id = ?"
            active_bookings = conn.execute(active_query + " ORDER BY b.booking_id DESC", (current_uid,)).fetchall()
        else:
            active_bookings = conn.execute(active_query + " ORDER BY b.booking_id DESC LIMIT 25").fetchall()

        # 3. Recent Payments & Refund Records
        pay_query = """
            SELECT p.payment_id, p.booking_id, p.amount, cs.energy_kwh, cs.end_time,
                   u.name AS user_name, u.phone, pt.connector_type, op.company_name,
                   r.refund_id, r.amount AS refunded_amount, r.status AS refund_status
            FROM PAYMENTS p
            JOIN BOOKINGS b ON p.booking_id = b.booking_id
            JOIN USERS u ON b.user_id = u.user_id
            JOIN PORTS pt ON b.port_id = pt.port_id
            JOIN STATIONS s ON pt.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
            LEFT JOIN REFUNDS r ON p.payment_id = r.payment_id
        """
        if user_role == "user" and current_uid:
            pay_query += " WHERE b.user_id = ?"
            recent_payments = conn.execute(pay_query + " ORDER BY p.payment_id DESC LIMIT 15", (current_uid,)).fetchall()
        else:
            recent_payments = conn.execute(pay_query + " ORDER BY p.payment_id DESC LIMIT 20").fetchall()

        # 4. Refunds Log Table
        refunds_log = conn.execute("""
            SELECT r.refund_id, r.payment_id, r.booking_id, r.amount, r.reason, r.refund_time, r.status,
                   u.name AS user_name, u.phone
            FROM REFUNDS r
            JOIN BOOKINGS b ON r.booking_id = b.booking_id
            JOIN USERS u ON b.user_id = u.user_id
            ORDER BY r.refund_id DESC
            LIMIT 15
        """).fetchall()

        now_formatted = datetime.now().strftime("%Y-%m-%dT%H:%M")
        highlight_id = request.args.get("highlight")
        highlight_pay = request.args.get("highlight_pay")

        return render_template(
            "booking_payment.html",
            active_tab=active_tab,
            available_ports=available_ports,
            active_bookings=active_bookings,
            recent_payments=recent_payments,
            refunds_log=refunds_log,
            now=now_formatted,
            preselected_port=preselected_port,
            preselected_station=preselected_station,
            highlight_id=highlight_id,
            highlight_pay=highlight_pay
        )
    finally:
        conn.close()

# Compatible redirect aliases for existing bookmarks
@app.route("/bookings/new", methods=["GET", "POST"])
def new_booking():
    if request.method == "POST":
        return unified_booking_payment()
    return redirect(url_for("unified_booking_payment", tab="reserve", port_id=request.args.get("port_id", "")))

@app.route("/payments/new", methods=["GET", "POST"])
def new_payment():
    if request.method == "POST":
        return unified_booking_payment()
    return redirect(url_for("unified_booking_payment", tab="settle"))

@app.route("/refunds/new", methods=["POST"])
def new_refund():
    return unified_booking_payment()

# -----------------------------------------------------------------------------
# 4. INCIDENT LOGGING & COMPLAINT RESOLUTION (ADMIN RESTRICTED ACTION)
# -----------------------------------------------------------------------------
@app.route("/complaints/new", methods=["GET", "POST"])
def new_complaint():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            port_id = int(request.form["port_id"])
            issue = request.form["issue"].strip()

            next_id = conn.execute("SELECT COALESCE(MAX(complaint_id), 0) + 1 FROM COMPLAINTS").fetchone()[0]
            conn.execute("INSERT INTO COMPLAINTS (complaint_id, port_id, issue, status) VALUES (?, ?, ?, 'Open')",
                         (next_id, port_id, issue))
            conn.commit()
            flash(f"⚠️ Incident Ticket #{next_id} logged for Port #{port_id}! Port automatically marked 'Faulted'.", "warning")
            return redirect(url_for("new_complaint"))

        ports = conn.execute("""
            SELECT p.port_id, s.station_id, op.company_name, p.connector_type, p.status
            FROM PORTS p
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY p.port_id
            LIMIT 50
        """).fetchall()

        recent_complaints = conn.execute("""
            SELECT c.complaint_id, c.port_id, op.company_name, c.issue, c.status, p.status AS port_status
            FROM COMPLAINTS c
            JOIN PORTS p ON c.port_id = p.port_id
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY c.complaint_id DESC
            LIMIT 12
        """).fetchall()

        return render_template("new_complaint.html", ports=ports, complaints=recent_complaints)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error filing complaint: {str(e)}", "danger")
        return redirect(url_for("new_complaint"))
    finally:
        conn.close()

@app.route("/complaints/resolve/<int:complaint_id>", methods=["POST"])
@admin_required
def resolve_complaint(complaint_id):
    """Admin-only action: Marks a complaint as Resolved, restoring port back to Available."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE COMPLAINTS SET status = 'Resolved' WHERE complaint_id = ?", (complaint_id,))
        conn.commit()
        flash(f"✅ Complaint #{complaint_id} resolved! Associated Port status restored to 'Available'.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error resolving complaint: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("new_complaint"))

# -----------------------------------------------------------------------------
# 5. STATION REVIEWS
# -----------------------------------------------------------------------------
@app.route("/reviews/new", methods=["GET", "POST"])
def new_review():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            user_id = session.get("user_id")
            if not user_id:
                user_id = int(request.form.get("user_id", 1))
            station_id = int(request.form["station_id"])
            rating = int(request.form["rating"])

            next_id = conn.execute("SELECT COALESCE(MAX(review_id), 0) + 1 FROM REVIEWS").fetchone()[0]
            conn.execute("INSERT INTO REVIEWS (review_id, user_id, station_id, rating) VALUES (?, ?, ?, ?)",
                         (next_id, user_id, station_id, rating))
            conn.commit()
            flash(f"⭐ Review #{next_id} ({rating} Stars) submitted for Station #{station_id}!", "success")
            return redirect(url_for("new_review"))

        users = conn.execute("SELECT user_id, name, phone FROM USERS ORDER BY name LIMIT 40").fetchall()
        stations = conn.execute("""
            SELECT s.station_id, op.company_name, s.latitude, s.longitude
            FROM STATIONS s
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY s.station_id
        """).fetchall()

        recent_reviews = conn.execute("""
            SELECT r.review_id, u.name AS user_name, op.company_name, r.station_id, r.rating
            FROM REVIEWS r
            JOIN USERS u ON r.user_id = u.user_id
            JOIN STATIONS s ON r.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY r.review_id DESC
            LIMIT 10
        """).fetchall()

        return render_template("new_review.html", users=users, stations=stations, reviews=recent_reviews)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error submitting review: {str(e)}", "danger")
        return redirect(url_for("new_review"))
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 6. SQL QUERY EXECUTION WORKBENCH (ADMIN ONLY ROUTE)
# -----------------------------------------------------------------------------
PRESET_QUERIES = {
    "1. Live Station Availability & Rating Matrix (Ahmedabad Hubs)": """SELECT 
    station_id, 
    operator_name, 
    latitude, 
    longitude, 
    total_ports, 
    available_ports, 
    occupied_ports, 
    offline_ports, 
    avg_rating, 
    total_reviews
FROM v_station_live_status
ORDER BY available_ports DESC, station_id ASC
LIMIT 15;""",

    "2. Revenue & Energy Dispensed by Connector Type (in ₹ INR)": """SELECT 
    p.connector_type,
    COUNT(cs.session_id) AS total_sessions,
    ROUND(SUM(cs.energy_kwh), 2) AS total_kwh_dispensed,
    ROUND(SUM(pay.amount), 2) AS total_revenue_inr
FROM PORTS p
JOIN BOOKINGS b ON p.port_id = b.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
GROUP BY p.connector_type
ORDER BY total_revenue_inr DESC;""",

    "3. High-Rated Indian Charging Stations (HAVING avg_rating >= 4.0)": """SELECT 
    s.station_id,
    op.company_name AS operator_name,
    COUNT(r.review_id) AS review_count,
    ROUND(AVG(r.rating), 2) AS average_rating
FROM STATIONS s
JOIN OPERATORS op ON s.operator_id = op.operator_id
JOIN REVIEWS r ON s.station_id = r.station_id
GROUP BY s.station_id, op.company_name
HAVING COUNT(r.review_id) >= 2 AND AVG(r.rating) >= 4.0
ORDER BY average_rating DESC;""",

    "4. Top 10 EV Drivers by Lifetime Spend in INR (Scalar Subquery)": """SELECT 
    u.user_id,
    u.name,
    u.phone,
    (SELECT COUNT(*) FROM BOOKINGS b WHERE b.user_id = u.user_id) AS total_bookings,
    (SELECT COALESCE(SUM(p.amount), 0.0) 
     FROM PAYMENTS p 
     JOIN BOOKINGS b ON p.booking_id = b.booking_id 
     WHERE b.user_id = u.user_id) AS total_spent_inr
FROM USERS u
ORDER BY total_spent_inr DESC
LIMIT 10;""",

    "5. Complete Session & Payment Receipts (Multi-Table Join)": """SELECT 
    b.booking_id,
    u.name AS driver_name,
    op.company_name AS operator,
    p.connector_type,
    pr.rate_per_kwh AS rate_inr,
    cs.energy_kwh,
    pay.amount AS total_inr_paid,
    b.status
FROM BOOKINGS b
JOIN USERS u ON b.user_id = u.user_id
JOIN PORTS p ON b.port_id = p.port_id
JOIN STATIONS s ON p.station_id = s.station_id
JOIN OPERATORS op ON s.operator_id = op.operator_id
JOIN PRICES pr ON p.port_id = pr.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
ORDER BY b.booking_id DESC
LIMIT 10;""",

    "6. Operator Market Performance & Gross Revenue (in ₹ INR)": """SELECT 
    operator_id,
    company_name,
    stations_managed,
    total_ports_deployed,
    total_completed_sessions,
    total_energy_sold_kwh,
    gross_revenue AS gross_revenue_inr
FROM v_operator_financial_summary
ORDER BY gross_revenue_inr DESC;""",

    "7. Incident & Complaint Triage with Port Health Status": """SELECT 
    c.complaint_id,
    c.port_id,
    p.connector_type,
    p.status AS current_port_status,
    op.company_name AS station_operator,
    c.issue,
    c.status AS ticket_status
FROM COMPLAINTS c
JOIN PORTS p ON c.port_id = p.port_id
JOIN STATIONS s ON p.station_id = s.station_id
JOIN OPERATORS op ON s.operator_id = op.operator_id
ORDER BY c.complaint_id DESC
LIMIT 10;""",

    "8. Refunded Transactions & Settlement Audit": """SELECT 
    r.refund_id,
    r.payment_id,
    r.booking_id,
    u.name AS customer_name,
    u.phone,
    r.amount AS refund_inr,
    r.reason,
    r.refund_time,
    r.status
FROM REFUNDS r
JOIN BOOKINGS b ON r.booking_id = b.booking_id
JOIN USERS u ON b.user_id = u.user_id
ORDER BY r.refund_id DESC
LIMIT 10;"""
}

@app.route("/queries", methods=["GET", "POST"])
@admin_required
def queries():
    selected_preset = request.args.get("preset", "1. Live Station Availability & Rating Matrix (Ahmedabad Hubs)")
    query_sql = PRESET_QUERIES.get(selected_preset, PRESET_QUERIES["1. Live Station Availability & Rating Matrix (Ahmedabad Hubs)"])

    results = []
    columns = []
    error_msg = None
    row_count = 0

    if request.method == "POST":
        query_sql = request.form.get("sql_query", "").strip()
        selected_preset = request.form.get("preset_choice", selected_preset)

    if query_sql:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query_sql)
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = cursor.fetchall()
                row_count = len(results)
            else:
                conn.commit()
                row_count = cursor.rowcount
                flash(f"SQL Command executed successfully. {row_count} rows affected.", "info")
        except Exception as e:
            error_msg = str(e)
        finally:
            conn.close()

    return render_template("queries.html", 
                           presets=PRESET_QUERIES, 
                           selected_preset=selected_preset, 
                           query_sql=query_sql, 
                           columns=columns, 
                           results=results, 
                           row_count=row_count, 
                           error=error_msg)

# -----------------------------------------------------------------------------
# 7. ADMIN QUICK PORT STATUS OVERRIDE
# -----------------------------------------------------------------------------
@app.route("/admin/port/toggle", methods=["POST"])
@admin_required
def admin_toggle_port():
    conn = get_db_connection()
    try:
        port_id = int(request.form.get("port_id"))
        new_status = request.form.get("status", "Available")
        if new_status in ["Available", "Occupied", "Reserved", "Under Maintenance", "Faulted"]:
            conn.execute("UPDATE PORTS SET status = ? WHERE port_id = ?", (new_status, port_id))
            conn.commit()
            flash(f"🔧 Port #{port_id} status changed to '{new_status}'.", "info")
        else:
            flash("❌ Invalid port status requested.", "danger")
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error updating port status: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(request.referrer or url_for("index"))

if __name__ == "__main__":
    print("⚡ Starting VoltGrid India Ahmedabad EV Charging DBMS on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
