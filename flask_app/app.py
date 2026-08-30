"""
EV Charging Station Management System - Flask Web Application
Provides forms for inserting bookings/payments, managing complaints/reviews,
and an interactive query execution workbench connected to ev_charging.db.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "ev_charging_secret_key_dbms_project"

DB_PATH = Path(__file__).resolve().parent.parent / "ev_charging.db"

def get_db_connection():
    """Returns a SQLite connection with Foreign Keys and Row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -----------------------------------------------------------------------------
# 1. HOME / DASHBOARD ROUTE
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    try:
        # Fetch high-level statistics
        stats = {
            "operators": conn.execute("SELECT COUNT(*) FROM OPERATORS").fetchone()[0],
            "stations": conn.execute("SELECT COUNT(*) FROM STATIONS").fetchone()[0],
            "ports": conn.execute("SELECT COUNT(*) FROM PORTS").fetchone()[0],
            "available_ports": conn.execute("SELECT COUNT(*) FROM PORTS WHERE status = 'Available'").fetchone()[0],
            "bookings": conn.execute("SELECT COUNT(*) FROM BOOKINGS").fetchone()[0],
            "sessions": conn.execute("SELECT COUNT(*) FROM CHARGING_SESSIONS").fetchone()[0],
            "energy_kwh": conn.execute("SELECT ROUND(COALESCE(SUM(energy_kwh), 0), 1) FROM CHARGING_SESSIONS").fetchone()[0],
            "revenue": conn.execute("SELECT ROUND(COALESCE(SUM(amount), 0), 2) FROM PAYMENTS").fetchone()[0],
        }

        # Fetch Live Station Status using the created View
        stations = conn.execute("""
            SELECT station_id, operator_name, latitude, longitude, 
                   total_ports, available_ports, occupied_ports, offline_ports, avg_rating
            FROM v_station_live_status
            ORDER BY available_ports DESC, station_id ASC
            LIMIT 10
        """).fetchall()

        # Fetch Recent Bookings
        recent_bookings = conn.execute("""
            SELECT b.booking_id, u.name AS user_name, b.port_id, p.connector_type, 
                   b.start_time, b.status
            FROM BOOKINGS b
            JOIN USERS u ON b.user_id = u.user_id
            JOIN PORTS p ON b.port_id = p.port_id
            ORDER BY b.booking_id DESC
            LIMIT 8
        """).fetchall()

        return render_template("index.html", stats=stats, stations=stations, bookings=recent_bookings)
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 2. INSERT BOOKING FORM ROUTE
# -----------------------------------------------------------------------------
@app.route("/bookings/new", methods=["GET", "POST"])
def new_booking():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            user_id = int(request.form["user_id"])
            port_id = int(request.form["port_id"])
            start_time = request.form.get("start_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Compute next booking_id
            next_id = conn.execute("SELECT COALESCE(MAX(booking_id), 0) + 1 FROM BOOKINGS").fetchone()[0]

            # Insert new booking (Trigger automatically marks Port as Reserved!)
            conn.execute(
                "INSERT INTO BOOKINGS (booking_id, user_id, port_id, start_time, status) VALUES (?, ?, ?, ?, 'Confirmed')",
                (next_id, user_id, port_id, start_time)
            )
            conn.commit()
            flash(f"✅ Booking #{next_id} confirmed for User #{user_id} on Port #{port_id}! Port status updated to 'Reserved'.", "success")
            return redirect(url_for("index"))

        # Fetch available users and available ports for dropdowns
        users = conn.execute("SELECT user_id, name, phone FROM USERS ORDER BY name").fetchall()
        ports = conn.execute("""
            SELECT p.port_id, s.station_id, op.company_name, p.connector_type, pr.rate_per_kwh
            FROM PORTS p
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE p.status = 'Available'
            ORDER BY s.station_id, p.port_id
        """).fetchall()

        now_formatted = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template("new_booking.html", users=users, ports=ports, now=now_formatted)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error creating booking: {str(e)}", "danger")
        return redirect(url_for("new_booking"))
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 3. INSERT CHARGING SESSION & PAYMENT FORM ROUTE
# -----------------------------------------------------------------------------
@app.route("/payments/new", methods=["GET", "POST"])
def new_payment():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            booking_id = int(request.form["booking_id"])
            energy_kwh = float(request.form["energy_kwh"])
            end_time = request.form.get("end_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Fetch rate for calculating payment
            port_row = conn.execute("""
                SELECT pr.rate_per_kwh, b.port_id
                FROM BOOKINGS b
                JOIN PRICES pr ON b.port_id = pr.port_id
                WHERE b.booking_id = ?
            """, (booking_id,)).fetchone()

            rate = port_row["rate_per_kwh"] if port_row else 0.35
            amount = round((energy_kwh * rate) + 2.50, 2) # Rate * energy + $2.50 base service charge

            # IDs
            next_session_id = conn.execute("SELECT COALESCE(MAX(session_id), 0) + 1 FROM CHARGING_SESSIONS").fetchone()[0]
            next_payment_id = conn.execute("SELECT COALESCE(MAX(payment_id), 0) + 1 FROM PAYMENTS").fetchone()[0]

            # Atomic transaction: Insert session, insert payment, complete booking
            conn.execute("INSERT INTO CHARGING_SESSIONS (session_id, booking_id, energy_kwh, end_time) VALUES (?, ?, ?, ?)",
                         (next_session_id, booking_id, energy_kwh, end_time))
            conn.execute("INSERT INTO PAYMENTS (payment_id, booking_id, amount) VALUES (?, ?, ?)",
                         (next_payment_id, booking_id, amount))
            conn.execute("UPDATE BOOKINGS SET status = 'Completed' WHERE booking_id = ?", (booking_id,))
            
            conn.commit()
            flash(f"⚡ Session #{next_session_id} recorded ({energy_kwh} kWh) & Payment #{next_payment_id} (${amount:.2f}) settled successfully! Port released to 'Available'.", "success")
            return redirect(url_for("index"))

        # Fetch active/confirmed bookings ready for completion
        active_bookings = conn.execute("""
            SELECT b.booking_id, u.name AS user_name, b.port_id, p.connector_type, pr.rate_per_kwh, b.start_time
            FROM BOOKINGS b
            JOIN USERS u ON b.user_id = u.user_id
            JOIN PORTS p ON b.port_id = p.port_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE b.status IN ('Confirmed', 'In Progress')
            ORDER BY b.booking_id DESC
        """).fetchall()

        now_formatted = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template("new_payment.html", bookings=active_bookings, now=now_formatted)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error settling payment: {str(e)}", "danger")
        return redirect(url_for("new_payment"))
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 4. INSERT COMPLAINT FORM ROUTE
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
            flash(f"⚠️ Complaint #{next_id} filed on Port #{port_id}! Port status automatically marked 'Faulted' via database trigger.", "warning")
            return redirect(url_for("index"))

        ports = conn.execute("""
            SELECT p.port_id, s.station_id, op.company_name, p.connector_type, p.status
            FROM PORTS p
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY p.port_id
            LIMIT 50
        """).fetchall()

        recent_complaints = conn.execute("""
            SELECT c.complaint_id, c.port_id, op.company_name, c.issue, c.status
            FROM COMPLAINTS c
            JOIN PORTS p ON c.port_id = p.port_id
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            ORDER BY c.complaint_id DESC
            LIMIT 8
        """).fetchall()

        return render_template("new_complaint.html", ports=ports, complaints=recent_complaints)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error filing complaint: {str(e)}", "danger")
        return redirect(url_for("new_complaint"))
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 5. INSERT REVIEW FORM ROUTE
# -----------------------------------------------------------------------------
@app.route("/reviews/new", methods=["GET", "POST"])
def new_review():
    conn = get_db_connection()
    try:
        if request.method == "POST":
            user_id = int(request.form["user_id"])
            station_id = int(request.form["station_id"])
            rating = int(request.form["rating"])

            next_id = conn.execute("SELECT COALESCE(MAX(review_id), 0) + 1 FROM REVIEWS").fetchone()[0]
            conn.execute("INSERT INTO REVIEWS (review_id, user_id, station_id, rating) VALUES (?, ?, ?, ?)",
                         (next_id, user_id, station_id, rating))
            conn.commit()
            flash(f"⭐ Review #{next_id} ({rating} Stars) submitted for Station #{station_id}!", "success")
            return redirect(url_for("index"))

        users = conn.execute("SELECT user_id, name FROM USERS ORDER BY name LIMIT 40").fetchall()
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
            LIMIT 8
        """).fetchall()

        return render_template("new_review.html", users=users, stations=stations, reviews=recent_reviews)
    except Exception as e:
        conn.rollback()
        flash(f"❌ Error submitting review: {str(e)}", "danger")
        return redirect(url_for("new_review"))
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 6. SQL QUERY EXECUTION WORKBENCH ROUTE
# -----------------------------------------------------------------------------
PRESET_QUERIES = {
    "1. Station Availability Live View": "SELECT * FROM v_station_live_status ORDER BY total_ports DESC LIMIT 15;",
    "2. Revenue & Energy Dispensed by Connector Type": """SELECT 
    p.connector_type,
    COUNT(cs.session_id) AS total_sessions,
    ROUND(SUM(cs.energy_kwh), 2) AS total_kwh_dispensed,
    ROUND(SUM(pay.amount), 2) AS total_revenue_usd
FROM PORTS p
JOIN BOOKINGS b ON p.port_id = b.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
GROUP BY p.connector_type
ORDER BY total_revenue_usd DESC;""",
    "3. High-Rated Stations (HAVING avg_rating >= 4.0)": """SELECT 
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
    "4. Top 10 Drivers by Lifetime Spend (Scalar Subquery)": """SELECT 
    u.user_id,
    u.name,
    u.phone,
    (SELECT COUNT(*) FROM BOOKINGS b WHERE b.user_id = u.user_id) AS total_bookings,
    (SELECT COALESCE(SUM(p.amount), 0.0) 
     FROM PAYMENTS p 
     JOIN BOOKINGS b ON p.booking_id = b.booking_id 
     WHERE b.user_id = u.user_id) AS total_spent_usd
FROM USERS u
ORDER BY total_spent_usd DESC
LIMIT 10;""",
    "5. Complete Session & Payment Receipts (Multi-Table Inner Join)": """SELECT 
    b.booking_id,
    u.name AS driver_name,
    op.company_name AS operator,
    p.connector_type,
    pr.rate_per_kwh,
    cs.energy_kwh,
    pay.amount AS total_amount_paid
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
    "6. Users who Booked but Never Reviewed (EXCEPT Set Op)": """SELECT user_id, name, phone 
FROM USERS 
WHERE user_id IN (
    SELECT user_id FROM BOOKINGS
    EXCEPT
    SELECT user_id FROM REVIEWS
)
LIMIT 15;"""
}

@app.route("/queries", methods=["GET", "POST"])
def queries():
    selected_preset = request.args.get("preset", "1. Station Availability Live View")
    query_sql = PRESET_QUERIES.get(selected_preset, PRESET_QUERIES["1. Station Availability Live View"])

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
                flash(f"Command executed successfully. {row_count} rows affected.", "info")
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

if __name__ == "__main__":
    print("⚡ Starting EV Charging Station Flask Application on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
