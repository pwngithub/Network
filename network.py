import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Page Configuration ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# --- PRTG Configuration ---
PRTG_URL = "https://prtg.pioneerbroadband.net"

# --- Load Credentials ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

st.title("📊 PRTG Sensor Graph Viewer")

# --- Fetch all sensors ---
st.write("Loading sensors from PRTG...")

try:
    sensors_api_url = (
        f"{PRTG_URL}/api/table.json?"
        f"content=sensors&output=json&columns=objid,device,sensor"
        f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
    )

    response = requests.get(sensors_api_url, verify=False, timeout=10)
    if response.status_code == 200:
        sensors_data = response.json()
        sensors_list = sensors_data.get("sensors", [])

        if not sensors_list:
            st.error("No sensors found. Check your PRTG credentials or permissions.")
            st.stop()

        # Build dropdown options
        sensor_options = {
            f"{s['device']} - {s['sensor']} (ID: {s['objid']})": s["objid"]
            for s in sensors_list
        }

        selected_sensor_label = st.selectbox("Select Sensor", list(sensor_options.keys()))
        SENSOR_ID = sensor_options[selected_sensor_label]
    else:
        st.error(f"Failed to load sensors (HTTP {response.status_code})")
        st.code(response.text[:500])
        st.stop()

except requests.exceptions.RequestException as e:
    st.error("Network error while connecting to PRTG API.")
    st.code(str(e))
    st.stop()

# --- Graph Period Selection ---
graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)
period_to_graphid = {"Live (2 hours)": "0", "Last 48 hours": "1", "Last 30 days": "2", "Last 365 days": "3"}
graphid = period_to_graphid[graph_period]

# --- Build Graph URL ---
graph_url = (
    f"{PRTG_URL}/chart.png"
    f"?id={SENSOR_ID}&graphid={graphid}"
    f"&width=1200&height=500"
    f"&avg=0&graphstyling=base"
    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
)

st.write(f"Fetching graph for Sensor ID: **{SENSOR_ID}** ...")
response = requests.get(graph_url, verify=False, timeout=10)

st.write("Status:", response.status_code)
st.write("Content-Type:", response.headers.get("Content-Type", "N/A"))

if response.status_code == 200:
    if "image" in response.headers.get("Content-Type", ""):
        img = Image.open(BytesIO(response.content))
        st.image(img, caption=f"PRTG Graph - {graph_period}", use_container_width=True)
    else:
        st.error("PRTG returned HTML instead of an image (login or error page).")
        st.code(response.text[:500])
else:
    st.error(f"Failed to load graph. HTTP {response.status_code}")
