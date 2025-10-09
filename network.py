import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from requests.auth import HTTPBasicAuth

# --- Page Configuration ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# --- PRTG Configuration ---
PRTG_URL = "https://prtg.pioneerbroadband.net"
SENSOR_ID = "12363"

# --- Securely load credentials from Streamlit's secrets management ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("PRTG credentials not found in Streamlit secrets. Please configure them.")
    st.stop() # Stop the app if secrets are missing.

# --- Streamlit App UI ---
st.title("📊 PRTG Sensor Graph Viewer")
st.write(f"Displaying graph for Sensor ID: **{SENSOR_ID}**")

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

# --- Fetch and Display Graph (Using Header Authentication) ---
st.write("Attempting to fetch graph...")

# Define the authentication credentials to be sent in the request header.
auth = HTTPBasicAuth(PRTG_USERNAME, PRTG_PASSHASH)

# Construct the URL WITHOUT the username and passhash.
graph_url_base = (
    f"{PRTG_URL}/chart.png?id={SENSOR_ID}&graphid={graphid}"
    f"&width=1200&height=500"
)

try:
    # Make the request using the 'auth' parameter.
    response = requests.get(graph_url_base, auth=auth, verify=True, timeout=10)

    st.write(f"Response Status Code: {response.status_code}")

    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
        prtg_graph = Image.open(BytesIO(response.content))
        st.image(prtg_graph, caption=f"PRTG Graph - {graph_period}")
    else:
        st.error("Failed to get a valid image from PRTG. The server did not return an image.")
        st.write("Server Response (first 500 characters):")
        st.code(response.text[:500])

except requests.exceptions.RequestException as e:
    st.error("A network error occurred while trying to connect to PRTG.")
    st.info("This could mean Streamlit Cloud cannot access your server or the server is down.")
    st.code(str(e))
