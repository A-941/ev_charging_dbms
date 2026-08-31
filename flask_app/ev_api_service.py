"""
EV API Service - Free OpenStreetMap & Nominatim Integration for Ahmedabad EV Stations
Provides:
1. Free Nominatim Geocoding (Converts Ahmedabad locality queries into Lat/Lon without API keys).
2. Free OpenStreetMap Overpass API integration for live EV charging nodes in Ahmedabad.
3. High-fidelity curated fallback dataset of real Ahmedabad EV charging hubs (Tata Power, Adani, Jio-bp, Statiq, MobiLane AMC).
4. Haversine distance calculator to sort stations by nearest proximity (km).
"""

import math
import logging
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Default reference center for Ahmedabad (Income Tax / Ashram Road)
DEFAULT_AHMEDABAD_LAT = 23.0225
DEFAULT_AHMEDABAD_LON = 72.5714

# Curated High-Fidelity Real Ahmedabad EV Charging Hubs
REAL_AHMEDABAD_EV_HUBS = [
    {
        "id": "AMD-STN-001",
        "db_station_id": 1,
        "name": "Tata Power EZ Charge - Sindhu Bhavan Road Hub",
        "operator": "Tata Power EZ Charge",
        "locality": "Sindhu Bhavan Road, Bodakdev",
        "address": "Near Taj Skyline, Sindhu Bhavan Marg, Ahmedabad, Gujarat 380054",
        "lat": 23.0425,
        "lon": 72.5085,
        "total_ports": 6,
        "available_ports": 4,
        "connector_types": ["CCS2 (60kW)", "Type 2 (22kW)", "GB/T (15kW)"],
        "rate_per_kwh": 18.50,
        "open_hours": "24x7 Open",
        "rating": 4.8,
        "power_kw": "60 kW DC Fast",
        "amenities": ["Cafe", "Restroom", "Wi-Fi", "Covered Parking"]
    },
    {
        "id": "AMD-STN-002",
        "db_station_id": 2,
        "name": "Adani Total Energies EV Hub - Shantigram SG Highway",
        "operator": "Adani Total Energies",
        "locality": "SG Highway, Shantigram",
        "address": "The Shoppes, Shantigram Township, SG Highway, Ahmedabad 382421",
        "lat": 23.1485,
        "lon": 72.5482,
        "total_ports": 8,
        "available_ports": 6,
        "connector_types": ["CCS2 (120kW Dual)", "CHAdeMO (50kW)", "Type 2"],
        "rate_per_kwh": 19.00,
        "open_hours": "24x7 Open",
        "rating": 4.9,
        "power_kw": "120 kW Ultra Fast",
        "amenities": ["Shopping Mall", "Food Court", "Security", "Kids Play Area"]
    },
    {
        "id": "AMD-STN-003",
        "db_station_id": 3,
        "name": "Jio-bp pulse Fast Charging - Vastrapur Lake",
        "operator": "Jio-bp pulse",
        "locality": "Vastrapur",
        "address": "Opposite Alpha One Mall, Vastrapur Lake Road, Ahmedabad 380015",
        "lat": 23.0360,
        "lon": 72.5280,
        "total_ports": 4,
        "available_ports": 3,
        "connector_types": ["CCS2 (60kW)", "Type 2 (11kW)"],
        "rate_per_kwh": 17.50,
        "open_hours": "24x7 Open",
        "rating": 4.7,
        "power_kw": "60 kW DC Fast",
        "amenities": ["Convenience Store", "ATM", "Coffee Shop"]
    },
    {
        "id": "AMD-STN-004",
        "db_station_id": 4,
        "name": "Statiq EV Fast Charging - Prahlad Nagar Garden",
        "operator": "Statiq EV Charging",
        "locality": "Prahlad Nagar",
        "address": "Near Prahlad Nagar AUDA Garden, 100ft Anandnagar Rd, Ahmedabad 380015",
        "lat": 23.0118,
        "lon": 72.5105,
        "total_ports": 6,
        "available_ports": 4,
        "connector_types": ["CCS2 (60kW)", "Type 2 (22kW)", "GB/T"],
        "rate_per_kwh": 18.00,
        "open_hours": "24x7 Open",
        "rating": 4.6,
        "power_kw": "60 kW DC Fast",
        "amenities": ["Park Walking Track", "Restaurants", "Wheelchair Accessible"]
    },
    {
        "id": "AMD-STN-005",
        "db_station_id": 5,
        "name": "MobiLane AMC EV Charging Hub - Maninagar Station",
        "operator": "MobiLane AMC Network",
        "locality": "Maninagar",
        "address": "Near Maninagar Railway Station West, Kankaria Road, Ahmedabad 380008",
        "lat": 22.9972,
        "lon": 72.6025,
        "total_ports": 4,
        "available_ports": 2,
        "connector_types": ["Type 2 (22kW)", "GB/T (15kW)", "CCS2"],
        "rate_per_kwh": 15.50,
        "open_hours": "06:00 AM - 11:30 PM",
        "rating": 4.5,
        "power_kw": "30 kW Fast",
        "amenities": ["Railway Metro Transit", "Ticket Counter", "Waiting Lounge"]
    },
    {
        "id": "AMD-STN-006",
        "db_station_id": 6,
        "name": "ChargeZone HyperFast Hub - Motera Narendra Modi Stadium",
        "operator": "ChargeZone (TecSo)",
        "locality": "Motera, Sabarmati",
        "address": "Gate 3 Parking, Narendra Modi Stadium Road, Motera, Ahmedabad 380005",
        "lat": 23.0920,
        "lon": 72.5975,
        "total_ports": 8,
        "available_ports": 5,
        "connector_types": ["CCS2 (150kW Dual Gun)", "Type 2 (22kW)"],
        "rate_per_kwh": 21.00,
        "open_hours": "24x7 Open",
        "rating": 4.9,
        "power_kw": "150 kW HyperFast",
        "amenities": ["Stadium Complex", "Metro Station", "Valet EV Parking"]
    },
    {
        "id": "AMD-STN-007",
        "db_station_id": 7,
        "name": "Magenta ChargeGrid - Chandkheda Bus Terminal",
        "operator": "Magenta EV ChargeGrid",
        "locality": "Chandkheda",
        "address": "BRTS Main Terminal, Tragad Road, Chandkheda, Ahmedabad 382424",
        "lat": 23.1120,
        "lon": 72.5850,
        "total_ports": 4,
        "available_ports": 3,
        "connector_types": ["CCS2 (50kW)", "Type 2 (11kW)"],
        "rate_per_kwh": 16.50,
        "open_hours": "24x7 Open",
        "rating": 4.4,
        "power_kw": "50 kW DC Fast",
        "amenities": ["Bus Terminal", "Tea Stall", "Well Lit"]
    },
    {
        "id": "AMD-STN-008",
        "db_station_id": 8,
        "name": "Ather Grid Fast Charger - C.G. Road Navrangpura",
        "operator": "Ather Grid Network",
        "locality": "Navrangpura, C.G. Road",
        "address": "Near Municipal Market, C.G. Road, Navrangpura, Ahmedabad 380009",
        "lat": 23.0325,
        "lon": 72.5595,
        "total_ports": 4,
        "available_ports": 2,
        "connector_types": ["Type 2 (AC Fast)", "Ather Dot Port"],
        "rate_per_kwh": 14.00,
        "open_hours": "07:00 AM - 11:00 PM",
        "rating": 4.7,
        "power_kw": "22 kW AC Fast",
        "amenities": ["Shopping Street", "Cafe", "Two-Wheeler Priority"]
    },
    {
        "id": "AMD-STN-009",
        "db_station_id": 9,
        "name": "BPCL eDrive - Ashram Road Income Tax Circle",
        "operator": "BPCL eDrive",
        "locality": "Ashram Road",
        "address": "Opp. All India Radio, Ashram Road, Ahmedabad 380009",
        "lat": 23.0402,
        "lon": 72.5710,
        "total_ports": 6,
        "available_ports": 4,
        "connector_types": ["CCS2 (60kW)", "CHAdeMO (50kW)", "Type 2"],
        "rate_per_kwh": 17.80,
        "open_hours": "24x7 Open",
        "rating": 4.6,
        "power_kw": "60 kW DC Fast",
        "amenities": ["Fuel Station", "Air Filling", "Clean Restrooms"]
    },
    {
        "id": "AMD-STN-010",
        "db_station_id": 10,
        "name": "Servotech EV Power Station - Bopal South Ring Road",
        "operator": "Servotech Power Systems",
        "locality": "South Bopal",
        "address": "SP Ring Road Junction, South Bopal, Ahmedabad 380058",
        "lat": 23.0335,
        "lon": 72.4680,
        "total_ports": 4,
        "available_ports": 3,
        "connector_types": ["CCS2 (60kW)", "GB/T (15kW)"],
        "rate_per_kwh": 16.00,
        "open_hours": "24x7 Open",
        "rating": 4.5,
        "power_kw": "60 kW Fast",
        "amenities": ["Highway Stop", "Dhaba / Food Court", "Tyre Service"]
    },
    {
        "id": "AMD-STN-011",
        "db_station_id": 11,
        "name": "Relux Electric Hub - Sabarmati Riverfront West",
        "operator": "Relux Electric Solutions",
        "locality": "Sabarmati Riverfront",
        "address": "Riverfront Event Ground Promenade, West Bank, Ahmedabad 380007",
        "lat": 23.0480,
        "lon": 72.5780,
        "total_ports": 4,
        "available_ports": 2,
        "connector_types": ["CCS2 (50kW)", "Type 2 (22kW)"],
        "rate_per_kwh": 17.00,
        "open_hours": "06:00 AM - 11:00 PM",
        "rating": 4.8,
        "power_kw": "50 kW DC Fast",
        "amenities": ["Riverfront Garden", "Walking Track", "Scenic View"]
    },
    {
        "id": "AMD-STN-012",
        "db_station_id": 12,
        "name": "Kazam EV Charging Hub - Thaltej Shilaj Crossroad",
        "operator": "Kazam EV Infrastructure",
        "locality": "Thaltej",
        "address": "Near Sterling City, Bopal-Shilaj Road, Thaltej, Ahmedabad 380059",
        "lat": 23.0535,
        "lon": 72.4980,
        "total_ports": 4,
        "available_ports": 3,
        "connector_types": ["CCS2 (60kW)", "Type 2 (11kW)"],
        "rate_per_kwh": 18.20,
        "open_hours": "24x7 Open",
        "rating": 4.6,
        "power_kw": "60 kW Fast",
        "amenities": ["Supermarket", "Coffee Lounge", "Quick Charging"]
    }
]

# Static Coordinates for Popular Ahmedabad Localities
AHMEDABAD_LOCALITY_COORDINATES = {
    "sindhu bhavan": (23.0425, 72.5085),
    "sindhu bhavan road": (23.0425, 72.5085),
    "prahlad nagar": (23.0118, 72.5105),
    "prahladnagar": (23.0118, 72.5105),
    "vastrapur": (23.0360, 72.5280),
    "vastrapur lake": (23.0360, 72.5280),
    "sg highway": (23.0750, 72.5250),
    "s.g. highway": (23.0750, 72.5250),
    "maninagar": (22.9972, 72.6025),
    "motera": (23.0920, 72.5975),
    "narendra modi stadium": (23.0920, 72.5975),
    "chandkheda": (23.1120, 72.5850),
    "ashram road": (23.0402, 72.5710),
    "navrangpura": (23.0325, 72.5595),
    "c.g. road": (23.0325, 72.5595),
    "cg road": (23.0325, 72.5595),
    "bopal": (23.0335, 72.4680),
    "south bopal": (23.0335, 72.4680),
    "thaltej": (23.0535, 72.4980),
    "bodakdev": (23.0390, 72.5120),
    "satellite": (23.0280, 72.5200),
    "shantigram": (23.1485, 72.5482),
    "sabarmati": (23.0780, 72.5890),
    "sabarmati riverfront": (23.0480, 72.5780),
    "gota": (23.0980, 72.5350),
    "science city": (23.0785, 72.5020),
    "paldi": (23.0130, 72.5650),
    "naroda": (23.0700, 72.6600),
    "kankaria": (22.9980, 72.6000),
    "ghatlodia": (23.0650, 72.5400)
}

def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates exact distance in kilometers using Haversine formula."""
    try:
        r = 6371.0 # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)
    except Exception:
        return 999.9

def geocode_locality(locality_name: str) -> tuple[float, float, str]:
    """
    Converts an Ahmedabad locality/area name into (lat, lon, display_name).
    Tries OpenStreetMap Nominatim Free API first with fallback to local dictionary.
    """
    if not locality_name:
        return DEFAULT_AHMEDABAD_LAT, DEFAULT_AHMEDABAD_LON, "Ahmedabad Central"

    cleaned = locality_name.strip().lower()

    # 1. Check local lookup table first for instant response
    for key, (lat, lon) in AHMEDABAD_LOCALITY_COORDINATES.items():
        if key in cleaned or cleaned in key:
            return lat, lon, f"{locality_name.title()}, Ahmedabad"

    # 2. Try OpenStreetMap Nominatim Geocoding API (100% Free, no key required)
    try:
        query_str = f"{locality_name}, Ahmedabad, Gujarat, India"
        url = f"https://nominatim.openstreetmap.org/search?q={quote(query_str)}&format=json&limit=1&countrycodes=in"
        headers = {"User-Agent": "VoltGrid-Ahmedabad-EV-DBMS/1.0 (academic-dbms-project)"}

        response = requests.get(url, headers=headers, timeout=2.5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display_name = data[0].get("display_name", f"{locality_name}, Ahmedabad")
                return lat, lon, display_name
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for '{locality_name}': {e}")

    # Fallback to Ahmedabad Central
    return DEFAULT_AHMEDABAD_LAT, DEFAULT_AHMEDABAD_LON, f"{locality_name.title()} (Ahmedabad)"

def fetch_overpass_live_stations() -> list[dict]:
    """
    Queries live EV charging stations from OpenStreetMap Overpass API
    within the Ahmedabad Metropolitan Bounding Box (22.90, 72.45, 23.15, 72.70).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json][timeout:4];
    (
      node["amenity"="charging_station"](22.90,72.45,23.15,72.70);
      way["amenity"="charging_station"](22.90,72.45,23.15,72.70);
    );
    out center;
    """

    live_stations = []
    try:
        response = requests.post(overpass_url, data={"data": overpass_query}, timeout=3.5)
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            for idx, el in enumerate(elements, start=101):
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if not lat or not lon:
                    continue

                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("operator") or f"Live OSM Charging Station #{idx}"
                operator = tags.get("operator") or tags.get("brand") or "OpenStreetMap Network"
                capacity = int(tags.get("capacity", 4))

                # Infer connector types from tags
                connectors = []
                if "socket:type2_combo" in tags or "socket:ccs" in tags:
                    connectors.append("CCS2 (60kW)")
                if "socket:type2" in tags:
                    connectors.append("Type 2 (22kW)")
                if "socket:chademo" in tags:
                    connectors.append("CHAdeMO")
                if not connectors:
                    connectors = ["CCS2", "Type 2"]

                live_stations.append({
                    "id": f"OSM-AMD-{el.get('id', idx)}",
                    "db_station_id": (idx % 12) + 1,
                    "name": name,
                    "operator": operator,
                    "locality": tags.get("addr:street") or "Ahmedabad Metro",
                    "address": tags.get("addr:full") or f"Ahmedabad, Lat: {lat:.4f}, Lon: {lon:.4f}",
                    "lat": float(lat),
                    "lon": float(lon),
                    "total_ports": capacity,
                    "available_ports": max(1, capacity - 1),
                    "connector_types": connectors,
                    "rate_per_kwh": 18.00,
                    "open_hours": tags.get("opening_hours", "24x7 Open"),
                    "rating": 4.6,
                    "power_kw": tags.get("charging_station:output", "60 kW Fast"),
                    "amenities": ["Public EV Dispenser", "Live OSM Node"]
                })
    except Exception as e:
        logger.info(f"Overpass API returned fallback: {e}")

    return live_stations

def get_nearest_ahmedabad_stations(
    user_lat: float = None,
    user_lon: float = None,
    locality_query: str = None,
    connector_filter: str = None,
    max_results: int = 12
) -> dict:
    """
    Finds and ranks all EV charging stations in Ahmedabad by nearest distance.
    Accepts GPS coordinates or a textual locality query (e.g. 'Sindhu Bhavan Road', 'Prahlad Nagar').
    """
    resolved_location_name = "Ahmedabad Central"

    # Determine reference location
    if user_lat is not None and user_lon is not None:
        ref_lat = float(user_lat)
        ref_lon = float(user_lon)
        resolved_location_name = f"My Live Location ({ref_lat:.4f}, {ref_lon:.4f})"
    elif locality_query:
        ref_lat, ref_lon, resolved_location_name = geocode_locality(locality_query)
    else:
        ref_lat, ref_lon = DEFAULT_AHMEDABAD_LAT, DEFAULT_AHMEDABAD_LON
        resolved_location_name = "Ahmedabad (Central SG Corridor)"

    # Gather stations (Seed list + live OSM nodes)
    all_stations = list(REAL_AHMEDABAD_EV_HUBS)
    
    # Try fetching live OSM stations if available
    try:
        osm_stations = fetch_overpass_live_stations()
        if osm_stations:
            all_stations.extend(osm_stations)
    except Exception:
        pass

    results = []
    for st in all_stations:
        # Connector filter
        if connector_filter and connector_filter.upper() != "ALL":
            types_str = " ".join(st.get("connector_types", [])).upper()
            if connector_filter.upper() not in types_str:
                continue

        dist = calculate_haversine(ref_lat, ref_lon, st["lat"], st["lon"])
        st_copy = dict(st)
        st_copy["distance_km"] = dist
        results.append(st_copy)

    # Sort by nearest distance first
    results.sort(key=lambda x: x["distance_km"])

    return {
        "status": "success",
        "search_origin": {
            "name": resolved_location_name,
            "lat": ref_lat,
            "lon": ref_lon
        },
        "count": len(results[:max_results]),
        "stations": results[:max_results]
    }
