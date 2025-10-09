import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# --- Page Configuration ---
# Set the page title, icon, and layout. This should be the first Streamlit command.
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# --- PRTG Configuration ---
# These values are constant for your setup.
PRTG_URL = "https://prtg.pioneerbroadband.net"
SENSOR_ID = "12363"

# --- Securely load credentials from Streamlit's secrets management ---
# This pulls from your local .streamlit/secrets.toml file or from the secrets
# configured in your Streamlit Cloud app settings.
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("PRTG credentials not found in Streamlit secrets. Please configure them.")
    st.stop() # Stop the app from running further if secrets are missing.

# --- Streamlit App UI ---
st.title("📊 PRTG Sensor Graph Viewer")
st.write(f"Displaying graph for Sensor ID: **{SENSOR_ID}**")

# Dropdown menu to let the user select the time period for the graph.
graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)

# A dictionary to map the user-friendly names to the 'graphid' PRTG requires.
period_to_graphid = {
    "Live (2 hours)": "0",
    "Last 48 hours": "1",
    "Last 30 days": "2",
    "Last 365 days": "3",
}
graphid = period_to_graphid[graph_period]

# Construct the final URL for the PRTG API call with all parameters.
graph_url = (
    f"{PRTG_URL}/chart.png?id={SENSOR_ID}&graphid={graphid}"
    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
    f"&width=1200&height=500"  # Adjust width and height as needed
)

# --- Fetch and Display Graph with Detailed Error Handling ---
st.write("Attempting to fetch graph...")

try:
    # Make the request with SSL verification and a 10-second timeout.
    response = requests.get(graph_url, verify=True, timeout=10)

    # Provide feedback on the HTTP status code for debugging.
    st.write(f"Response Status Code: {response.status_code}")

    # Check if the response was successful (200) and if the content is an image.
    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
        # If successful, open the image from the response and display it.
        prtg_graph = Image.open(BytesIO(response.content))
        st.image(prtg_graph, caption=f"PRTG Graph - {graph_period}")
    else:
        # If the response was not a valid image, show an error and the server's response text.
        st.error("Failed to get a valid image from PRTG. The server did not return an image.")
        st.write("Server Response (first 500 characters):")
        st.code(response.text[:500])

except requests.exceptions.RequestException as e:
    # Handle network-level errors (e.g., timeout, connection error).
    st.error("A network error occurred while trying to connect to PRTG.")
    st.info("This usually means Streamlit Cloud cannot access your PRTG server's URL, or the server is down.")
    st.code(str(e))
