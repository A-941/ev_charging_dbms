"""
EV Charging Station Management System - Interactive Streamlit Dashboard
Provides an interactive GUI for managing the database, simulating charging sessions,
submitting reviews/complaints, viewing geospatial stations, and executing live SQL queries.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_connection, execute_query, execute_non_query, get_db_stats

st.set_page_config(
    page_title="EV Charging Station Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #616161;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚡ EV Charging Station Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Relational Database Management System | Academic DBMS Project</div>', unsafe_allow_html=True)

# Sidebar System Health & Database Stats
st.sidebar.title("🗄️ Database Metrics")
stats = get_db_stats()
for tbl, cnt in stats.items():
    st.sidebar.metric(label=tbl, value=f"{cnt:,} rows")

# Navigation Tabs
tab_overview, tab_explorer, tab_simulator, tab_feedback, tab_sql = st.tabs([
    "📊 Executive Dashboard",
    "🗺️ Station Explorer & Map",
    "🔌 Booking & Charging Simulator",
    "⭐ Reviews & Complaints",
    "🔍 SQL Query Workbench"
])

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE DASHBOARD
# -----------------------------------------------------------------------------
with tab_overview:
    st.subheader("Network Operational Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Stations", f"{stats.get('STATIONS', 0)}")
    with col2:
        st.metric("Total Charging Ports", f"{stats.get('PORTS', 0)}")
    with col3:
        total_energy = execute_query("SELECT ROUND(COALESCE(SUM(energy_kwh), 0), 1) AS kwh FROM CHARGING_SESSIONS")
        st.metric("Energy Dispensed", f"{total_energy['kwh'].iloc[0]:,} kWh")
    with col4:
        total_rev = execute_query("SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS rev FROM PAYMENTS")
        st.metric("Total Revenue", f"${total_rev['rev'].iloc[0]:,}")

    st.divider()
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("#### 🏢 Operator Revenue & Infrastructure Summary")
        op_df = execute_query("""
            SELECT 
                op.company_name AS Operator,
                COUNT(DISTINCT s.station_id) AS Stations,
                COUNT(DISTINCT p.port_id) AS Ports,
                COUNT(DISTINCT cs.session_id) AS Sessions,
                ROUND(COALESCE(SUM(pay.amount), 0.0), 2) AS Revenue_USD
            FROM OPERATORS op
            LEFT JOIN STATIONS s ON op.operator_id = s.operator_id
            LEFT JOIN PORTS p ON s.station_id = p.station_id
            LEFT JOIN BOOKINGS b ON p.port_id = b.port_id
            LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
            LEFT JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
            GROUP BY op.operator_id, op.company_name
            ORDER BY Revenue_USD DESC
        """)
        st.dataframe(op_df, use_container_width=True)

    with col_right:
        st.markdown("#### 🔌 Connector Type Utilization & Share")
        conn_df = execute_query("""
            SELECT 
                p.connector_type AS Connector,
                COUNT(DISTINCT p.port_id) AS Total_Ports,
                COUNT(cs.session_id) AS Total_Sessions,
                ROUND(COALESCE(SUM(cs.energy_kwh), 0.0), 1) AS Energy_Sold_kWh
            FROM PORTS p
            LEFT JOIN BOOKINGS b ON p.port_id = b.port_id
            LEFT JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
            GROUP BY p.connector_type
            ORDER BY Energy_Sold_kWh DESC
        """)
        st.dataframe(conn_df, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: STATION EXPLORER & MAP
# -----------------------------------------------------------------------------
with tab_explorer:
    st.subheader("Geographic Station Network & Port Availability")
    
    # Filter Controls
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        operators = ["All Operators"] + execute_query("SELECT company_name FROM OPERATORS ORDER BY company_name")["company_name"].tolist()
        sel_operator = st.selectbox("Filter by Operator", operators)
    with fcol2:
        connectors = ["All Connectors", "CCS2", "Type 2", "CHAdeMO", "GB/T", "Tesla Supercharger"]
        sel_connector = st.selectbox("Filter by Connector", connectors)
    with fcol3:
        statuses = ["All Statuses", "Available", "Occupied", "Reserved", "Under Maintenance", "Faulted"]
        sel_status = st.selectbox("Filter by Port Status", statuses)

    # Station Map & Details Query
    query = """
        SELECT 
            s.station_id,
            op.company_name AS operator,
            s.latitude AS lat,
            s.longitude AS lon,
            COUNT(p.port_id) AS total_ports,
            SUM(CASE WHEN p.status = 'Available' THEN 1 ELSE 0 END) AS available_ports,
            ROUND(AVG(r.rating), 1) AS avg_rating
        FROM STATIONS s
        JOIN OPERATORS op ON s.operator_id = op.operator_id
        LEFT JOIN PORTS p ON s.station_id = p.station_id
        LEFT JOIN REVIEWS r ON s.station_id = r.station_id
        WHERE 1=1
    """
    params = []
    if sel_operator != "All Operators":
        query += " AND op.company_name = ?"
        params.append(sel_operator)
    if sel_connector != "All Connectors":
        query += " AND p.connector_type = ?"
        params.append(sel_connector)
    if sel_status != "All Statuses":
        query += " AND p.status = ?"
        params.append(sel_status)

    query += " GROUP BY s.station_id, op.company_name, s.latitude, s.longitude"
    stations_df = execute_query(query, tuple(params))

    if not stations_df.empty:
        st.map(stations_df[["lat", "lon"]], zoom=2)
        st.dataframe(stations_df, use_container_width=True)
    else:
        st.info("No charging stations match the selected filters.")

# -----------------------------------------------------------------------------
# TAB 3: BOOKING & CHARGING SIMULATOR
# -----------------------------------------------------------------------------
with tab_simulator:
    st.subheader("⚡ Live Charging Session & Booking Simulator")
    
    sim_col1, sim_col2 = st.columns([1, 1])
    
    with sim_col1:
        st.markdown("### 📅 Create New Booking")
        users_df = execute_query("SELECT user_id, name, phone FROM USERS ORDER BY user_id LIMIT 30")
        user_options = {f"{row['name']} (ID: {row['user_id']})": row['user_id'] for _, row in users_df.iterrows()}
        selected_user_label = st.selectbox("Select User", list(user_options.keys()))
        selected_user_id = user_options[selected_user_label]
        
        avail_ports_df = execute_query("""
            SELECT p.port_id, s.station_id, op.company_name, p.connector_type, pr.rate_per_kwh
            FROM PORTS p
            JOIN STATIONS s ON p.station_id = s.station_id
            JOIN OPERATORS op ON s.operator_id = op.operator_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE p.status = 'Available'
            LIMIT 25
        """)
        
        if not avail_ports_df.empty:
            port_options = {
                f"Port #{r['port_id']} ({r['connector_type']} @ ${r['rate_per_kwh']}/kWh - {r['company_name']})": (r['port_id'], r['rate_per_kwh'])
                for _, r in avail_ports_df.iterrows()
            }
            selected_port_label = st.selectbox("Select Available Port", list(port_options.keys()))
            selected_port_id, selected_rate = port_options[selected_port_label]
            
            if st.button("Confirm Booking", type="primary"):
                max_b_id = execute_query("SELECT COALESCE(MAX(booking_id), 0) + 1 AS next_id FROM BOOKINGS")["next_id"].iloc[0]
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert booking (Trigger automatically marks Port as Reserved!)
                execute_non_query(
                    "INSERT INTO BOOKINGS (booking_id, user_id, port_id, start_time, status) VALUES (?, ?, ?, ?, 'Confirmed')",
                    (int(max_b_id), selected_user_id, selected_port_id, now_str)
                )
                st.success(f"✅ Booking #{max_b_id} Confirmed! Port #{selected_port_id} status automatically reserved.")
                st.rerun()
        else:
            st.warning("No ports currently marked 'Available'.")

    with sim_col2:
        st.markdown("### 🔋 Complete Charging Session & Billing")
        active_bookings = execute_query("""
            SELECT b.booking_id, u.name, b.port_id, p.connector_type, pr.rate_per_kwh, b.start_time
            FROM BOOKINGS b
            JOIN USERS u ON b.user_id = u.user_id
            JOIN PORTS p ON b.port_id = p.port_id
            JOIN PRICES pr ON p.port_id = pr.port_id
            WHERE b.status = 'Confirmed'
            ORDER BY b.booking_id DESC
            LIMIT 15
        """)
        
        if not active_bookings.empty:
            booking_options = {
                f"Booking #{r['booking_id']} - {r['name']} (Port #{r['port_id']})": r
                for _, r in active_bookings.iterrows()
            }
            sel_b_label = st.selectbox("Select Active Booking", list(booking_options.keys()))
            sel_b_data = booking_options[sel_b_label]
            
            energy_input = st.number_input("Energy Consumed (kWh)", min_value=1.0, max_value=120.0, value=35.5, step=0.5)
            calculated_amount = round((energy_input * sel_b_data['rate_per_kwh']) + 2.50, 2)
            st.info(f"💵 Total Bill Amount: **${calculated_amount:.2f}** (Energy: {energy_input} kWh × ${sel_b_data['rate_per_kwh']} + $2.50 Service Fee)")
            
            if st.button("Complete Session & Settle Payment"):
                b_id = int(sel_b_data['booking_id'])
                end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                max_s_id = int(execute_query("SELECT COALESCE(MAX(session_id), 0) + 1 AS next_id FROM CHARGING_SESSIONS")["next_id"].iloc[0])
                max_p_id = int(execute_query("SELECT COALESCE(MAX(payment_id), 0) + 1 AS next_id FROM PAYMENTS")["next_id"].iloc[0])
                
                # Insert Session & Payment, Update Booking (Trigger automatically marks Port as Available!)
                execute_non_query("INSERT INTO CHARGING_SESSIONS VALUES (?, ?, ?, ?)", (max_s_id, b_id, energy_input, end_str))
                execute_non_query("INSERT INTO PAYMENTS VALUES (?, ?, ?)", (max_p_id, b_id, calculated_amount))
                execute_non_query("UPDATE BOOKINGS SET status = 'Completed' WHERE booking_id = ?", (b_id,))
                
                st.success(f"🎉 Session #{max_s_id} logged and Payment #{max_p_id} of ${calculated_amount:.2f} settled! Port released back to Available.")
                st.rerun()
        else:
            st.info("No active confirmed bookings ready for completion.")

# -----------------------------------------------------------------------------
# TAB 4: REVIEWS & COMPLAINTS
# -----------------------------------------------------------------------------
with tab_feedback:
    st.subheader("⭐ Feedback & Maintenance Incident Desk")
    
    col_rev, col_comp = st.columns(2)
    
    with col_rev:
        st.markdown("### ✍️ Submit Station Review")
        station_choices = execute_query("SELECT s.station_id, op.company_name FROM STATIONS s JOIN OPERATORS op ON s.operator_id = op.operator_id")
        st_opts = {f"Station #{r['station_id']} ({r['company_name']})": r['station_id'] for _, r in station_choices.iterrows()}
        rev_st = st.selectbox("Select Station", list(st_opts.keys()))
        rev_rating = st.slider("Rating (Stars)", min_value=1, max_value=5, value=5)
        
        if st.button("Submit Review"):
            next_r_id = int(execute_query("SELECT COALESCE(MAX(review_id), 0) + 1 AS next_id FROM REVIEWS")["next_id"].iloc[0])
            execute_non_query("INSERT INTO REVIEWS VALUES (?, 1, ?, ?)", (next_r_id, st_opts[rev_st], rev_rating))
            st.success("⭐ Review submitted successfully!")
            st.rerun()

    with col_comp:
        st.markdown("### ⚠️ Lodge Port Incident / Complaint")
        port_choices = execute_query("SELECT port_id, station_id, connector_type FROM PORTS LIMIT 30")
        p_opts = {f"Port #{r['port_id']} (Station #{r['station_id']} - {r['connector_type']})": r['port_id'] for _, r in port_choices.iterrows()}
        comp_port = st.selectbox("Select Defective Port", list(p_opts.keys()))
        comp_issue = st.text_area("Issue Description", "Connector locking mechanism unresponsive upon vehicle docking.")
        
        if st.button("File Complaint", type="primary"):
            next_c_id = int(execute_query("SELECT COALESCE(MAX(complaint_id), 0) + 1 AS next_id FROM COMPLAINTS")["next_id"].iloc[0])
            # Trigger trg_port_fault_on_complaint automatically sets port status to 'Faulted'
            execute_non_query("INSERT INTO COMPLAINTS VALUES (?, ?, ?, 'Open')", (next_c_id, p_opts[comp_port], comp_issue))
            st.error("⚠️ Incident ticket logged! Port status automatically switched to 'Faulted' via database trigger.")
            st.rerun()

    st.divider()
    st.markdown("### 📋 Recent Complaints Registry")
    recent_complaints = execute_query("""
        SELECT c.complaint_id, c.port_id, p.connector_type, s.station_id, op.company_name, c.issue, c.status
        FROM COMPLAINTS c
        JOIN PORTS p ON c.port_id = p.port_id
        JOIN STATIONS s ON p.station_id = s.station_id
        JOIN OPERATORS op ON s.operator_id = op.operator_id
        ORDER BY c.complaint_id DESC
        LIMIT 10
    """)
    st.dataframe(recent_complaints, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: SQL QUERY WORKBENCH
# -----------------------------------------------------------------------------
with tab_sql:
    st.subheader("🔍 Interactive SQL Query Workbench")
    
    PRESET_QUERIES = {
        "DQL: Station Availability View (v_station_live_status)": "SELECT * FROM v_station_live_status ORDER BY total_ports DESC LIMIT 15;",
        "DQL: Total Revenue & Energy Dispensed per Connector Type": """SELECT 
    p.connector_type,
    COUNT(cs.session_id) AS session_count,
    ROUND(SUM(cs.energy_kwh), 2) AS total_kwh,
    ROUND(SUM(pay.amount), 2) AS total_revenue
FROM PORTS p
JOIN BOOKINGS b ON p.port_id = b.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
GROUP BY p.connector_type
ORDER BY total_revenue DESC;""",
        "DQL: High-Performing Stations (HAVING avg_rating >= 4.0)": """SELECT 
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
        "Joins: Complete Session Billing & Driver Receipt": """SELECT 
    b.booking_id,
    u.name AS user_name,
    op.company_name,
    p.connector_type,
    pr.rate_per_kwh,
    cs.energy_kwh,
    pay.amount AS total_paid
FROM BOOKINGS b
JOIN USERS u ON b.user_id = u.user_id
JOIN PORTS p ON b.port_id = p.port_id
JOIN STATIONS s ON p.station_id = s.station_id
JOIN OPERATORS op ON s.operator_id = op.operator_id
JOIN PRICES pr ON p.port_id = pr.port_id
JOIN CHARGING_SESSIONS cs ON b.booking_id = cs.booking_id
JOIN PAYMENTS pay ON b.booking_id = pay.booking_id
LIMIT 10;""",
        "Subquery: Users with Highest Spending (Scalar Subquery)": """SELECT 
    u.user_id,
    u.name,
    (SELECT COUNT(*) FROM BOOKINGS b WHERE b.user_id = u.user_id) AS total_bookings,
    (SELECT COALESCE(SUM(p.amount), 0.0) 
     FROM PAYMENTS p 
     JOIN BOOKINGS b ON p.booking_id = b.booking_id 
     WHERE b.user_id = u.user_id) AS total_spent
FROM USERS u
ORDER BY total_spent DESC
LIMIT 10;""",
        "Set Operation: Users who Booked vs Users who Reviewed (EXCEPT)": """SELECT user_id, name, phone FROM USERS WHERE user_id IN (
    SELECT user_id FROM BOOKINGS
    EXCEPT
    SELECT user_id FROM REVIEWS
) LIMIT 10;"""
    }
    
    sel_preset = st.selectbox("Choose a Pre-loaded Syllabus Demonstration Query", list(PRESET_QUERIES.keys()))
    query_text = st.text_area("SQL Query Editor", value=PRESET_QUERIES[sel_preset], height=150)
    
    if st.button("🚀 Execute SQL Query", type="primary"):
        try:
            res_df = execute_query(query_text)
            st.success(f"Query returned {len(res_df)} rows.")
            st.dataframe(res_df, use_container_width=True)
            
            # Download CSV option
            csv = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results as CSV", csv, "query_results.csv", "text/csv")
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")
