import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

PRTG_URL = "https://prtg.pioneerbroadband.net"

# --- Load Credentials ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

st.title("📊 PRTG Graph Viewer")

# --- Simple Sensor Selection ---
SENSOR_ID = st.text_input("Enter Sensor ID", "12363")

graph_period = st.selectbox(
    "Select Graph Period",
    ("Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"),
)
period_to_graphid = {"Live (2 hours)": "0", "Last 48 hours": "1", "Last 30 days": "2", "Last 365 days": "3"}
graphid = period_to_graphid[graph_period]

graph_url = (
    f"{PRTG_URL}/chart.png"
    f"?id={SENSOR_ID}&graphid={graphid}"
    f"&width=1200&height=500"
    f"&avg=0&graphstyling=base"
    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
)

if st.button("Load Graph"):
    st.write(f"Fetching graph for Sensor ID: **{SENSOR_ID}** ...")
    try:
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
    except requests.exceptions.RequestException as e:
        st.error("Network error while contacting PRTG.")
        st.code(str(e))
