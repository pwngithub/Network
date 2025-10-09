import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

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

# --- Sensors ---
SENSORS = {
    "Core Router - Houlton (ID 12435)": "12435",
    "Core Router - Presque Isle (ID 12506)": "12506",
    "Fiber Aggregation Switch (ID 12363)": "12363",
    "DWDM Node - Calais (ID 12340)": "12340",
}

# --- Graph Period ---
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

# --- Function to fetch peak bandwidth from PRTG API ---
def fetch_peak_bandwidth(sensor_id):
    try:
        url = (
            f"{PRTG_URL}/api/table.json?"
            f"content=channels&columns=name,lastvalue_,lastvalue_raw,maximum,maximum_raw"
            f"&id={sensor_id}"
            f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
        )
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            peaks = {}
            for ch in data.get("channels", []):
                name = ch.get("name", "")
                max_val = ch.get("maximum_raw")
                if max_val is not None:
                    # Convert from bits per second to Mbps
                    peaks[name] = round(float(max_val) / 1_000_000, 2)
            return peaks
    except Exception as e:
        st.warning(f"Error fetching peak bandwidth: {e}")
    return {}

# --- Function to fetch and display graph ---
def show_graph(sensor_name, sensor_id):
    peaks = fetch_peak_bandwidth(sensor_id)
    if peaks:
        in_bw = peaks.get("Traffic In", 0)
        out_bw = peaks.get("Traffic Out", 0)
        st.markdown(f"**Peak In:** {in_bw} Mbps  **Peak Out:** {out_bw} Mbps")

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
            st.image(img, caption=f"{sensor_name}", use_container_width=False)
        else:
            st.warning(f"⚠️ Could not load graph for {sensor_name}.")
            st.code(response.text[:200])
    except requests.exceptions.RequestException as e:
        st.error(f"Network error for {sensor_name}")
        st.code(str(e))

# --- Layout (2x2 grid) ---
sensor_items = list(SENSORS.items())
for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i:i+2]):
        with col:
            st.subheader(f"{sensor_name} — {graph_period}")
            show_graph(sensor_name, sensor_id)
