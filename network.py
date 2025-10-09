import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# --- PRTG Configuration ---
# Securely load credentials from secrets.toml
PRTG_URL = "https://prtg.pioneerbroadband.net"
SENSOR_ID = "12363"
PRTG_USERNAME = st.secrets["prtg_username"]
PRTG_PASSHASH = st.secrets["prtg_passhash"]

# ... (the rest of your app code remains the same) ...

# --- Streamlit App ---
st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

st.title("PRTG Sensor Graph")

# (The rest of your code is here)
