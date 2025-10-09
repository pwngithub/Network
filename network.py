import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# --- PRTG Configuration ---
PRTG_URL = "https://prtg.pioneerbroadband.net"
SENSOR_ID = "12363"

# --- Load Credentials ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("⚠️ Missing PRTG credentials in Streamlit secrets.")
    st.stop()

# --- UI ---
st.title("📊 PRTG Sensor Graph Viewer")
graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)
period_to_graphid = {"Live (2 hours)": "0", "Last 48 hours": "1", "Last 30 days": "2", "Last 365 days": "3"}
graphid = period_to_graphid[graph_period]

# --- Build Graph URL ---
graph_url = (
    f"{PRTG_URL}/chart.png?id={SENSOR_ID}&graphid={graphid}"
    f"&width=1200&height=500"
    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
)

st.write("Fetching graph...")

try:
    response = requests.get(graph_url, verify=False, timeout=10)
    if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
        img = Image.open(BytesIO(response.content))
        st.image(img, caption=f"PRTG Graph - {graph_period}", use_container_width=True)
    else:
        st.error(f"Failed to load graph. HTTP {response.status_code}")
        st.code(response.text[:500])
except requests.exceptions.RequestException as e:
    st.error("Network error while contacting PRTG.")
    st.code(str(e))
