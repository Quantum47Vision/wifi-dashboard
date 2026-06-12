import streamlit as st
import subprocess
import platform
import re
import pandas as pd
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Wi-Fi Performance Dashboard",
    page_icon="📶",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
}

div[data-testid="metric-container"] {
    border: 1px solid #333;
    padding: 10px;
    border-radius: 10px;
    text-align: center;
}

h1 {
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
HOST = "8.8.8.8"
PING_COUNT = 5

# --------------------------------------------------
# PING FUNCTIONS
# --------------------------------------------------
def ping():
    param = "-n" if platform.system().lower() == "windows" else "-c"

    cmd = [
        "ping",
        param,
        str(PING_COUNT),
        HOST
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stdout


def parse_ping(output):

    times = re.findall(
        r"time[=<]([\d]+)ms",
        output
    )

    if not times:
        return None

    times = list(map(int, times))

    avg_latency = round(sum(times) / len(times), 1)

    jitter = max(times) - min(times)

    packet_loss = len(times) < PING_COUNT

    return avg_latency, jitter, packet_loss


def analyze(avg, jitter, loss):

    if loss:
        return "❌ Packet loss detected (unstable Wi-Fi or interference)"

    if jitter > 40:
        return "⚠️ High jitter (network congestion/interference)"

    if avg > 100:
        return "🐢 High latency (slow routing or ISP issue)"

    return "✅ Connection healthy"


# --------------------------------------------------
# SESSION STORAGE
# --------------------------------------------------
if "data" not in st.session_state:
    st.session_state.data = []

# --------------------------------------------------
# HEADER
# --------------------------------------------------
left, right = st.columns([4, 1])

with left:
    st.title("📶 Wi-Fi Performance Dashboard")
    st.caption(
        "Monitor latency, jitter and packet loss in real time."
    )

with right:
    st.write("")
    st.write("")

    run_test = st.button(
        "▶ Run Test",
        use_container_width=True
    )

# --------------------------------------------------
# RUN TEST
# --------------------------------------------------
if run_test:

    output = ping()

    result = parse_ping(output)

    if result:

        avg, jitter, loss = result

        reason = analyze(avg, jitter, loss)

        st.session_state.data.append(
            {
                "time": datetime.now(),
                "latency": avg,
                "jitter": jitter,
                "packet_loss": loss,
                "reason": reason
            }
        )

# --------------------------------------------------
# DATAFRAME
# --------------------------------------------------
df = pd.DataFrame(st.session_state.data)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if not df.empty:

    latest = df.iloc[-1]

    # KPI ROW
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Latency",
            f"{latest['latency']} ms"
        )

    with c2:
        st.metric(
            "Jitter",
            f"{latest['jitter']} ms"
        )

    with c3:
        st.metric(
            "Packet Loss",
            "Yes" if latest["packet_loss"] else "No"
        )

    with c4:
        status = (
            "Healthy"
            if "healthy" in latest["reason"].lower()
            else "Issue"
        )

        st.metric(
            "Status",
            status
        )

    st.divider()

    # CHARTS
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Latency Trend")

        st.line_chart(
            df.set_index("time")["latency"],
            height=250
        )

    with col2:
        st.subheader("Jitter Trend")

        st.line_chart(
            df.set_index("time")["jitter"],
            height=250
        )

    st.divider()

    # LOGS + ISSUE
    col1, col2 = st.columns([3, 1])

    with col1:

        st.subheader("Test History")

        st.dataframe(
            df,
            use_container_width=True,
            height=250
        )

    with col2:

        st.subheader("Latest Analysis")

        st.info(latest["reason"])

        st.write("")

        if latest["latency"] < 50:
            st.success("Excellent latency")
        elif latest["latency"] < 100:
            st.warning("Moderate latency")
        else:
            st.error("High latency")

else:

    st.info(
        "Run your first test using the button above."
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Latency", "--")
    c2.metric("Jitter", "--")
    c3.metric("Packet Loss", "--")

