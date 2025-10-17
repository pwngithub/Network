import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3
import datetime
import matplotlib.pyplot as plt

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="PRTG Graph Viewer", layout="wide")

# ---------- dark-mode toggle ----------
dark = st.checkbox("🌙 Dark mode")
if dark:
    st.markdown(
        """
        <style>
        .stApp {background-color:#0e1117;color:#fafafa}
        .stMetric {background:#1f1f1f;border-radius:6px;padding:6px 0}
        </style>
        """,
        unsafe_allow_html=True,
    )

PRTG_URL = "https://prtg.pioneerbroadband.net"
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

# ---------- title / last-update chip ----------
st.markdown(
    f"""
    <style>
    .title {{font-size:2rem;font-weight:600;margin-bottom:0}}
    .chip  {{display:inline-block;background:#f1f3f4;color:#444;
             padding:4px 10px;border-radius:12px;font-size:0.8rem}}
    </style>
    <div class="title">📡  PRTG Bandwidth Overview</div>
    <span class="chip">Last refresh: {datetime.datetime.now().strftime("%H:%M")}</span>
    """,
    unsafe_allow_html=True,
)

# ---------- horizontal period selector ----------
period_col, _ = st.columns([1, 3])
with period_col:
    graph_period = st.radio(
        "📊  Period",
        ["Live (2 hours)", "Last 48 hours", "Last 30 days", "Last 365 days"],
        horizontal=True,
        label_visibility="collapsed",
    )
period_to_graphid = {
    "Live (2 hours)": "0",
    "Last 48 hours": "1",
    "Last 30 days": "2",
    "Last 365 days": "3",
}
graphid = period_to_graphid[graph_period]

SENSORS = {
    "Firstlight (ID 12435)": "12435",
    "NNINIX (ID 12506)": "12506",
    "HE (ID 12363)": "12363",
    "Cogent (ID 12340)": "12340",
}

# ---------- unchanged helpers ----------
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

# ---------- show_graph with ORIGINAL image code ----------
def show_graph(sensor_name, sensor_id):
    stats = fetch_bandwidth_stats(sensor_id)
    in_peak = stats.get("Traffic In_max", 0)
    out_peak = stats.get("Traffic Out_max", 0)
    in_avg = stats.get("Traffic In_avg", 0)
    out_avg = stats.get("Traffic Out_avg", 0)

    # NEW: metric pills instead of markdown
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Peak In", f"{in_peak} Mbps")
    kpi2.metric("Peak Out", f"{out_peak} Mbps")
    kpi3.metric("Avg In", f"{in_avg} Mbps")
    kpi4.metric("Avg Out", f"{out_avg} Mbps")

    graph_url = (
        f"{PRTG_URL}/chart.png"
        f"?id={sensor_id}&graphid={graphid}"
        f"&width=1600&height=700"
        f"&avg=0&graphstyling=base"
        f"&username={PRTG_USERNAME}&passhash={PRTG_PASSHASH}"
    )

    # ---------- ORIGINAL IMAGE BLOCK  (only param fixed) ----------
    try:
        response = requests.get(graph_url, verify=False, timeout=10)
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            img = Image.open(BytesIO(response.content))
            st.image(img, use_container_width=True)   # ← fixed param
            st.markdown("<hr style='border:1px solid #ccc; margin:20px 0;'>", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Could not load graph for {sensor_name}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error for {sensor_name}")
        st.code(str(e))
    # -------------------------------------------------------

    return in_peak, out_peak

# ---------- 2×2 sensor grid ----------
total_in, total_out = 0, 0
sensor_items = list(SENSORS.items())

for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i : i + 2]):
        with col:
            with st.container():
                st.subheader(f"{sensor_name} — {graph_period}")
                in_peak, out_peak = show_graph(sensor_name, sensor_id)
                total_in += in_peak
                total_out += out_peak

# ---------- aggregate summary ----------
st.markdown("---")
st.header("📈 Total Bandwidth Summary (All Sensors Combined)")
st.markdown(
    f"**Total Peak In:** {total_in:.2f} Mbps  **Total Peak Out:** {total_out:.2f} Mbps"
)
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(["Total Peak In", "Total Peak Out"], [total_in, total_out],
       color=["tab:blue", "tab:orange"])
ax.set_ylabel("Mbps")
ax.set_title("Aggregate Peak Bandwidth (Current)")
ax.grid(axis="y", linestyle="--", alpha=0.6)
st.pyplot(fig)

# ---------- back-to-top ----------
st.markdown('<div id="top"></div>', unsafe_allow_html=True)
if st.button("⬆  Back to top"):
    st.markdown(
        '<script>window.scrollTo({top:0,behavior:"smooth"});</script>',
        unsafe_allow_html=True,
    )

