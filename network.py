import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import urllib3
import datetime

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

# ---------- secrets ----------
PRTG_URL = "https://prtg.pioneerbroadband.net"
try:
    PRTG_USERNAME = st.secrets["prtg_username"]
    PRTG_PASSHASH = st.secrets["prtg_passhash"]
except KeyError:
    st.error("Missing PRTG credentials in Streamlit secrets.")
    st.stop()

# ---------- title ----------
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

# ---------- period selector ----------
period_col, _ = st.columns([1, 3])
with period_col:
    graph_period = st.radio(
        "📊  Period",
        ["Live (2 h)", "48 h", "30 d", "365 d"],
        horizontal=True,
        label_visibility="collapsed",
    )
graphid = {"Live (2 h)": "0", "48 h": "1", "30 d": "2", "365 d": "3"}[graph_period]

# ---------- sensors ----------
SENSORS = {
    "Firstlight (ID 12435)": "12435",
    "NNINIX (ID 12506)": "12506",
    "HE (ID 12363)": "12363",
    "Cogent (ID 12340)": "12340",
}

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

def show_graph(sensor_name, sensor_id):
    stats = fetch_bandwidth_stats(sensor_id)
    in_peak = stats.get("Traffic In_max", 0)
    out_peak = stats.get("Traffic Out_max", 0)
    in_avg = stats.get("Traffic In_avg", 0)
    out_avg = stats.get("Traffic Out_avg", 0)

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

    # ---------- WORKING IMAGE BLOCK ----------
    response = requests.get(graph_url, verify=False, timeout=10)
    if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image"):
        img = Image.open(BytesIO(response.content))
        st.image(img, use_container_width=True)   # ← new API
    else:
        st.warning(f"Graph not returned as PNG for {sensor_name}")
    # -----------------------------------------

    return in_peak, out_peak

# ---------- display ----------
total_in, total_out = 0, 0
sensor_items = list(SENSORS.items())

for i in range(0, len(sensor_items), 2):
    cols = st.columns(2)
    for col, (sensor_name, sensor_id) in zip(cols, sensor_items[i : i + 2]):
        with col:
            with st.container():
                st.subheader(sensor_name)
                st.caption(graph_period)
                in_peak, out_peak = show_graph(sensor_name, sensor_id)
                total_in += in_peak
                total_out += out_peak

st.markdown("---")
st.header("📈  Aggregate Peak")
agg_col1, agg_col2, agg_col3 = st.columns([1, 2, 1])
with agg_col2:
    st.metric("Total Peak In", f"{total_in:.1f} Mbps")
    st.metric("Total Peak Out", f"{total_out:.1f} Mbps")

st.markdown('<div id="top"></div>', unsafe_allow_html=True)
if st.button("⬆  Back to top"):
    st.markdown(
        '<script>window.scrollTo({top:0,behavior:"smooth"});</script>',
        unsafe_allow_html=True,
    )

