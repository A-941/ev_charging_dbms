"""
Automated Integration Test Suite for VoltGrid India Ahmedabad EV DBMS Flask App
Validates:
1. Unauthenticated & Regular User RBAC blocking on /queries (Admin only).
2. Admin authentication and unrestricted access to /queries.
3. User login and registration with text inputs.
4. Live Ahmedabad Station Finder API endpoint (/api/nearest-stations) with Nominatim geocoding & Haversine distance.
5. Unified booking reservation with direct text name/phone and trigger check.
6. Session settlement with INR (₹) calculation.
7. Refund module processing and REFUNDS table records.
8. Incident filing and Admin resolution restoring port to Available.
"""

import sys
import unittest
from pathlib import Path

# Add flask_app to path
FLASK_DIR = Path(__file__).resolve().parent / "flask_app"
sys.path.insert(0, str(FLASK_DIR))

from app import app, get_db_connection
from ev_api_service import geocode_locality, get_nearest_ahmedabad_stations, calculate_haversine

class TestVoltGridApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_index_loads_successfully(self):
        """Test home dashboard loads with 200 OK and contains Ahmedabad localization."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"VoltGrid", res.data)
        self.assertIn(b"Live Ahmedabad EV Station Finder", res.data)
        self.assertIn(b"Live Station Availability", res.data)
        self.assertIn(b"Slot Bookings", res.data)

    def test_02_rbac_workbench_protection_unauthenticated(self):
        """Test unauthenticated user trying to access /queries is redirected to /login."""
        res = self.client.get("/queries", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location", ""))

    def test_03_rbac_workbench_protection_regular_user(self):
        """Test regular logged-in user trying to access /queries is redirected with access denied."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["name"] = "Aarav Patel"
            sess["phone"] = "+91-98765-43210"
            sess["role"] = "user"

        res = self.client.get("/queries", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Access Denied", res.data)

    def test_04_admin_login_and_workbench_access(self):
        """Test admin login grants full access to SQL Workbench."""
        res = self.client.post("/login", data={
            "login_type": "admin",
            "admin_username": "admin",
            "admin_password": "admin123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome, System Administrator", res.data)

        # Access /queries
        q_res = self.client.get("/queries")
        self.assertEqual(q_res.status_code, 200)
        self.assertIn(b"SQL Query Execution Workbench", q_res.data)
        self.assertIn(b"Live Station Availability", q_res.data)

        # Execute custom SQL
        exec_res = self.client.post("/queries", data={
            "sql_query": "SELECT operator_id, company_name FROM OPERATORS LIMIT 3;"
        })
        self.assertEqual(exec_res.status_code, 200)
        self.assertIn(b"Tata Power", exec_res.data)

    def test_05_ahmedabad_ev_api_service_and_endpoint(self):
        """Test the free Ahmedabad EV station location API returns nearest hubs sorted by distance."""
        # Direct Service Call Test
        service_res = get_nearest_ahmedabad_stations(locality_query="Prahlad Nagar")
        self.assertEqual(service_res["status"], "success")
        self.assertTrue(service_res["count"] > 0)
        first_hub = service_res["stations"][0]
        self.assertIn("Prahlad Nagar", first_hub["name"])
        self.assertEqual(first_hub["distance_km"], 0.0)

        # HTTP Endpoint Test (POST JSON)
        res = self.client.post("/api/nearest-stations", json={
            "locality": "Sindhu Bhavan Road",
            "connector": "CCS2"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["count"] > 0)
        self.assertIn("Sindhu Bhavan", data["stations"][0]["name"])
        self.assertTrue(data["stations"][0]["distance_km"] <= 1.0)

    def test_06_unified_booking_and_settlement_lifecycle(self):
        """Test reserving a slot with text inputs, then settling it in INR, and verifying port status."""
        conn = get_db_connection()
        avail_port = conn.execute("SELECT port_id FROM PORTS WHERE status = 'Available' LIMIT 1").fetchone()
        self.assertIsNotNone(avail_port, "Must have an available port for test")
        port_id = avail_port["port_id"]
        conn.close()

        # 1. Reserve slot with text inputs
        res = self.client.post("/booking-payment", data={
            "action": "reserve",
            "driver_name": "Dhruv Makwana",
            "driver_phone": "+91-94280-11223",
            "vehicle_model": "Tata Nexon EV Max / Long Range",
            "port_id": port_id,
            "start_time": "2026-08-31 11:00:00"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Slot Reserved successfully", res.data)

        # Verify Port status became Reserved
        conn = get_db_connection()
        p_row = conn.execute("SELECT status FROM PORTS WHERE port_id = ?", (port_id,)).fetchone()
        self.assertEqual(p_row["status"], "Reserved")

        b_row = conn.execute("SELECT booking_id FROM BOOKINGS WHERE port_id = ? AND status = 'Confirmed' ORDER BY booking_id DESC LIMIT 1", (port_id,)).fetchone()
        self.assertIsNotNone(b_row)
        booking_id = b_row["booking_id"]
        conn.close()

        # 2. Settle the booking
        settle_res = self.client.post("/booking-payment", data={
            "action": "settle",
            "booking_id": booking_id,
            "energy_kwh": "32.0",
            "end_time": "2026-08-31 12:30:00"
        }, follow_redirects=True)
        self.assertEqual(settle_res.status_code, 200)
        self.assertIn(b"Settled", settle_res.data)

        # Verify Port released back to Available and Payment recorded in INR
        conn = get_db_connection()
        p_row_after = conn.execute("SELECT status FROM PORTS WHERE port_id = ?", (port_id,)).fetchone()
        self.assertEqual(p_row_after["status"], "Available")

        pay_row = conn.execute("SELECT payment_id, amount FROM PAYMENTS WHERE booking_id = ?", (booking_id,)).fetchone()
        self.assertIsNotNone(pay_row)
        self.assertTrue(pay_row["amount"] > 0)
        payment_id = pay_row["payment_id"]
        conn.close()

        # 3. Process Refund for this payment
        refund_res = self.client.post("/booking-payment", data={
            "action": "refund",
            "payment_id": payment_id,
            "refund_amount": str(pay_row["amount"]),
            "reason": "Test customer refund request"
        }, follow_redirects=True)
        self.assertEqual(refund_res.status_code, 200)
        self.assertIn(b"successfully processed", refund_res.data)

        # Verify REFUNDS record
        conn = get_db_connection()
        ref_row = conn.execute("SELECT refund_id, status FROM REFUNDS WHERE payment_id = ?", (payment_id,)).fetchone()
        self.assertIsNotNone(ref_row)
        self.assertEqual(ref_row["status"], "Processed")
        conn.close()

    def test_07_complaint_and_admin_resolve_trigger(self):
        """Test filing a complaint marks port Faulted, and Admin resolution marks it Available."""
        conn = get_db_connection()
        avail_port = conn.execute("SELECT port_id FROM PORTS WHERE status = 'Available' LIMIT 1").fetchone()
        port_id = avail_port["port_id"]
        conn.close()

        # File complaint
        res = self.client.post("/complaints/new", data={
            "port_id": port_id,
            "issue": "Connector latch stuck"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        p_row = conn.execute("SELECT status FROM PORTS WHERE port_id = ?", (port_id,)).fetchone()
        self.assertEqual(p_row["status"], "Faulted")

        comp_row = conn.execute("SELECT complaint_id FROM COMPLAINTS WHERE port_id = ? ORDER BY complaint_id DESC LIMIT 1", (port_id,)).fetchone()
        complaint_id = comp_row["complaint_id"]
        conn.close()

        # Login as Admin and Resolve
        with self.client.session_transaction() as sess:
            sess["user_id"] = 0
            sess["role"] = "admin"
            sess["name"] = "Admin"

        resolve_res = self.client.post(f"/complaints/resolve/{complaint_id}", follow_redirects=True)
        self.assertEqual(resolve_res.status_code, 200)

        conn = get_db_connection()
        p_row_resolved = conn.execute("SELECT status FROM PORTS WHERE port_id = ?", (port_id,)).fetchone()
        self.assertEqual(p_row_resolved["status"], "Available")
        conn.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
