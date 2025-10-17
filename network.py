import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

# Disable SSL warnings, which can occur with some corporate network certificates.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Page Setup ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# Your PRTG server's base URL.
PRTG_URL = "https://prtg.pioneerbroadband.net"

# --- Load Credentials from Streamlit Secrets ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets. Please add them to continue.")
    st.stop()

# --- App UI ---
st.title("📊 PRTG Network Graph Viewer")

# A dictionary to hold the user-friendly names and their corresponding sensor IDs.
SENSOR_OPTIONS = {
    "Core Router - Houlton (ID 12435)": "12435",
    "Core Router - Presque Isle (ID 12506)": "12506",
    "Fiber Aggregation Switch (ID 12363)": "12363",
    "DWDM Node - Calais (ID 12340)": "12340",
}

# Create a dropdown menu for the user to select which sensor to view.
selected_sensor_label = st.selectbox("Select Sensor", list(SENSOR_OPTIONS.keys()))
SENSOR_ID = SENSOR_OPTIONS[selected_sensor_label]

# Create a dropdown for selecting the graph's time period.
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

# --- Build the final URL for the PRTG API call ---
graph_url = (
    f"{PRTG_URL}/chart.png"
    f"?id={SENSOR_ID}&graphid={graphid}"
    f"&width=1200&height=500"
    f"&avg=0&graphstyling=base"
    f"&useunit=gbit"  # <-- THIS IS THE NEW PARAMETER to force the Y-axis to Gbps
    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
)

st.write(f"Fetching graph for **{selected_sensor_label}**...")

# --- Make the API Request and Display the Graph ---
try:
    response = requests.get(graph_url, verify=False, timeout=15)

    if response.status_code == 200:
        if "image" in response.headers.get("Content-Type", ""):
            img = Image.open(BytesIO(response.content))
            st.image(img, caption=f"{selected_sensor_label} - {graph_period}", use_container_width=True)
        else:
            st.error("Authentication failed. PRTG returned a login page instead of an image.")
            st.code(response.text[:500])
    else:
        st.error(f"Failed to load graph. The server responded with HTTP status code: {response.status_code}")

except requests.exceptions.RequestException as e:
    st.error("A network error occurred while trying to contact the PRTG server.")
    st.code(str(e))


