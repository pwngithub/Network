import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

# Disable SSL warnings for self-signed certs (safe internally)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Page Setup ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

PRTG_URL = "https://prtg.pioneerbroadband.net"

# --- Load Credentials ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

st.title("📊 PRTG Bandwidth Overview")

# --- Graph Period ---
graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)
period_to_graphid = {
    "Live (2 hours)": "0",
    "Last 48 hours)": "1",
    "Last 30 days": "2",
    "Last 365 days": "3",
}
graphid = period_to_graphid[graph_period]

# --- Sensors ---
SENSORS = {
    "Firstlight (ID 12435)": "12435",
    "NNINIX (ID 12506)": "12506",
    "HE (ID 12363)": "12363",
    "Cogent (ID 12340)": "12340",
}

# --- Fetch Formatted Stats ---
def fetch_bandwidth_stats(sensor_id):
    """Fetches the pre-formatted channel data directly from PRTG, including units."""
    try:
        # Request the 'maximum' and 'average' fields which include the units as a string
        url = (
            f"{PRTG_URL}/api/table.json?"
            f"content=channels&columns=name,maximum,average"
            f"&id={sensor_id}"
            f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
        )
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats = {}
            for ch in data.get("channels", []):
                name = ch.get("name", "Unknown Channel")
                # Get the formatted string (e.g., "9.73 Gbit/s")
                stats[f"{name}_max"] = ch.get("maximum", "N/A")
                stats[f"{name}_avg"] = ch.get("average", "N/A")
            return stats
    except Exception as e:
        st.warning(f"Error fetching bandwidth data for sensor {sensor_id}: {e}")
    return {}

# --- Fetch and Display Graph ---
def show_graph(sensor_name, sensor_id):
    """Displays the formatted bandwidth stats and the graph for a sensor."""
    stats = fetch_bandwidth_stats(sensor_id)
    in_peak = stats.get("Traffic In_max", "N/A")
    out_peak = stats.get("Traffic Out_max", "N/A")
    in_avg = stats.get("Traffic In_avg", "N/A")
    out_avg = stats.get("Traffic Out_avg", "N/A")

    # Display the pre-formatted values directly
    st.markdown(
        f"**Peak In:** {in_peak}  **Peak Out:** {out_peak}  \n"
        f"**Avg In:** {in_avg}  **Avg Out:** {out_avg}"
    )

    graph_url = (
        f"{PRTG_URL}/chart.png"
        f"?id={sensor_id}&graphid={graphid}"
        f"&width=1600&height=700"
        f"&avg=0&graphstyling=base"
        f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
    )

    try:
        response = requests.get(graph_url, verify=False, timeout=10)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=f"{sensor_name}", use_container_width=True)
            st.markdown("<hr style='border:1px solid #ccc; margin:20px 0;'>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Could not load graph for {sensor_name}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error for {sensor_name}")
        st.code(str(e))

# --- Display Sensors (2×2 Grid) ---
sensor_items = list(SENSORS.items())

for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i:i+2]):
        if sensor_name: # Check if there is a sensor to display
            with col:
                st.subheader(f"{sensor_name} — {graph_period}")
                show_graph(sensor_name, sensor_id)
