import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

# Disable SSL warnings for self-signed certs (safe inside your network)
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

st.title("📊 PRTG Sensor Graph Viewer")

# --- Sensors to Display ---
SENSORS = {
    "Core Router - Houlton (ID 12435)": "12435",
    "Core Router - Presque Isle (ID 12506)": "12506",
    "Fiber Aggregation Switch (ID 12363)": "12363",
    "DWDM Node - Calais (ID 12340)": "12340",
}

# --- Graph Period Selector ---
graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)
period_to_graphid = {
    "Live (2 hours)": "0",
    "Last 48 hours": "1",
    "Last 30 days": "2",
    "Last 365 days": "3",
}
graphid = period_to_graphid[graph_period]

# --- Create 2x2 Grid Layout ---
sensor_items = list(SENSORS.items())

# Split into two rows of two columns each
for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i:i+2]):
        with col:
            st.subheader(f"{sensor_name} — {graph_period}")
            graph_url = (
                f"{PRTG_URL}/chart.png"
                f"?id={sensor_id}&graphid={graphid}"
                f"&width=1200&height=500"
                f"&avg=0&graphstyling=base"
                f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
            )

            try:
                response = requests.get(graph_url, verify=False, timeout=10)
                if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                    img = Image.open(BytesIO(response.content))
                    st.image(img, caption=f"{sensor_name}", use_container_width=True)
                else:
                    st.warning(f"⚠️ Could not load graph for {sensor_name}.")
                    st.code(response.text[:300])
            except requests.exceptions.RequestException as e:
                st.error(f"Network error for {sensor_name}")
                st.code(str(e))
