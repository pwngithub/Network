import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Disable SSL warnings for self-signed certs
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


# --- Fetch Peak/Average Stats ---
def fetch_bandwidth_stats(sensor_id):
    try:
        url = (
            f"{PRTG_URL}/api/table.json?"
            f"content=channels&columns=name,maximum_raw,average_raw"
            f"&id={sensor_id}"
            f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
        )
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats = {}
            for ch in data.get("channels", []):
                name = ch.get("name", "")
                max_val = ch.get("maximum_raw")
                avg_val = ch.get("average_raw")
                if max_val not in (None, "", " "):
                    try:
                        stats[f"{name}_max"] = round(float(max_val) / 1_000_000, 2)
                    except ValueError:
                        pass
                if avg_val not in (None, "", " "):
                    try:
                        stats[f"{name}_avg"] = round(float(avg_val) / 1_000_000, 2)
                    except ValueError:
                        pass
            return stats
    except Exception as e:
        st.warning(f"Error fetching bandwidth data for sensor {sensor_id}: {e}")
    return {}


# --- Fetch Historical Data for Total Trend ---
def fetch_historic_totals(sensor_ids, days=7):
    """Fetch daily total peak In/Out from the last N days."""
    totals = []
    for offset in range(days, 0, -1):
        day = datetime.now() - timedelta(days=offset)
        date_str = day.strftime("%Y-%m-%d")
        total_in = 0
        total_out = 0

        for sid in sensor_ids:
            try:
                url = (
                    f"{PRTG_URL}/api/historicdata.json?"
                    f"id={sid}&avg=86400"  # daily average
                    f"&sdate={date_str}+00:00:00"
                    f"&edate={date_str}+23:59:59"
                    f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
                )
                response = requests.get(url, verify=False, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Find highest In/Out for the day
                    for record in data.get("histdata", []):
                        in_val = record.get("Traffic In (Speed)", "")
                        out_val = record.get("Traffic Out (Speed)", "")
                        if in_val not in ("", None, "-") and out_val not in ("", None, "-"):
                            try:
                                total_in = max(total_in, float(in_val) / 1_000_000)
                                total_out = max(total_out, float(out_val) / 1_000_000)
                            except ValueError:
                                pass
            except Exception:
                pass
        totals.append((date_str, total_in, total_out))
    return totals


# --- Fetch and Display Graph ---
def show_graph(sensor_name, sensor_id):
    stats = fetch_bandwidth_stats(sensor_id)
    in_peak = stats.get("Traffic In_max", 0)
    out_peak = stats.get("Traffic Out_max", 0)
    in_avg = stats.get("Traffic In_avg", 0)
    out_avg = stats.get("Traffic Out_avg", 0)

    # Display text stats
    st.markdown(
        f"**Peak In:** {in_peak} Mbps  **Peak Out:** {out_peak} Mbps  \n"
        f"**Avg In:** {in_avg} Mbps  **Avg Out:** {out_avg} Mbps"
    )

    # Build graph URL
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
    except requests.exceptions.RequestException as e:
        st.error(f"Network error for {sensor_name}")
        st.code(str(e))

    return in_peak, out_peak


# --- Display Sensors (2×2 Grid) + Collect Totals ---
total_in = 0
total_out = 0
sensor_items = list(SENSORS.items())

for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i:i+2]):
        with col:
            st.subheader(f"{sensor_name} — {graph_period}")
            in_peak, out_peak = show_graph(sensor_name, sensor_id)
            total_in += in_peak
            total_out += out_peak

# --- Summary Chart for Total Bandwidth ---
st.markdown("---")
st.header("📈 Total Bandwidth Summary (All Sensors Combined)")

st.markdown(
    f"**Total Peak In:** {total_in:.2f} Mbps  **Total Peak Out:** {total_out:.2f} Mbps"
)

# --- Bar Chart Visualization (Current Total) ---
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(["Total Peak In", "Total Peak Out"], [total_in, total_out], color=["tab:blue", "tab:orange"])
ax.set_ylabel("Mbps")
ax.set_title("Aggregate Peak Bandwidth (Current)")
ax.grid(axis="y", linestyle="--", alpha=0.6)
st.pyplot(fig)

# --- Historical Trend ---
st.markdown("---")
st.header("📊 Total Bandwidth Trend (Last 7 Days)")

with st.spinner("Fetching historical data..."):
    history = fetch_historic_totals(SENSORS.values(), days=7)

if history:
    dates = [d[0] for d in history]
    ins = [d[1] for d in history]
    outs = [d[2] for d in history]

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(dates, ins, marker="o", label="Total Peak In (Mbps)", color="tab:blue")
    ax2.plot(dates, outs, marker="o", label="Total Peak Out (Mbps)", color="tab:orange")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Mbps")
    ax2.set_title("Total Network Peak Bandwidth - Last 7 Days")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)
    st.pyplot(fig2)
else:
    st.warning("No historical data available.")
