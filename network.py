import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Page Setup ---
st.set_page_config(page_title="PRTG Live Bandwidth Dashboard", layout="wide")

PRTG_URL = "https://prtg.pioneerbroadband.net"

# --- Load Credentials ---
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

st.title("📊 PRTG Bandwidth Overview (Live Data)")

# --- Sensors ---
SENSORS = {
    "Firstlight (ID 12435)": "12435",
    "NNINIX (ID 12506)": "12506",
    "HE (ID 12363)": "12363",
    "Cogent (ID 12340)": "12340",
}

# --- Graph Period Selection ---
graph_period = st.selectbox(
    "Select Graph Period",
    ("Last 2 hours", "Last 48 hours", "Last 30 days"),
)

# Determine time range for PRTG API (seconds)
period_to_seconds = {
    "Last 2 hours": 2 * 60 * 60,
    "Last 48 hours": 48 * 60 * 60,
    "Last 30 days": 30 * 24 * 60 * 60,
}
range_seconds = period_to_seconds[graph_period]

# --- Helper: Fetch Historic Data ---
def fetch_historic_data(sensor_id, range_seconds):
    url = (
        f"{PRTG_URL}/api/historicdata.json"
        f"?id={sensor_id}"
        f"&avg=0&sdate=now-{range_seconds}s&edate=now"
        f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
    )
    try:
        resp = requests.get(url, verify=False, timeout=15)
        if resp.status_code != 200:
            st.warning(f"⚠️ Failed to fetch data for sensor {sensor_id}. HTTP {resp.status_code}")
            return None
        data = resp.json()
        records = data.get("histdata", [])
        if not records:
            return None
        df = pd.DataFrame(records)
        # Ensure numeric columns
        for col in ["Traffic In (speed)", "Traffic Out (speed)"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        st.error(f"Error fetching data for sensor {sensor_id}: {e}")
        return None

# --- Plot Function ---
def plot_bandwidth(df, sensor_name):
    fig, ax = plt.subplots(figsize=(10, 4))
    if "Traffic In (speed)" in df.columns:
        ax.plot(df["datetime"], df["Traffic In (speed)"]/1_000_000, label="In", color="tab:blue", linewidth=2)
    if "Traffic Out (speed)" in df.columns:
        ax.plot(df["datetime"], df["Traffic Out (speed)"]/1_000_000, label="Out", color="tab:orange", linewidth=2)
    ax.set_title(sensor_name, fontsize=13, fontweight="bold")
    ax.set_ylabel("Mbps")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    fig.autofmt_xdate()
    st.pyplot(fig)

# --- Display All Graphs ---
for name, sid in SENSORS.items():
    st.subheader(name)
    df = fetch_historic_data(sid, range_seconds)
    if df is not None and not df.empty:
        # Display peak info
        peak_in = df["Traffic In (speed)"].max() / 1_000_000
        peak_out = df["Traffic Out (speed)"].max() / 1_000_000
        st.markdown(
            f"**Peak In:** {peak_in:.2f} Mbps  **Peak Out:** {peak_out:.2f} Mbps"
        )
        plot_bandwidth(df, name)
    else:
        st.warning(f"No data available for {name} in this range.")

st.markdown("---")
st.caption("Data source: PRTG historicdata.json API • Values converted to Mbps")
