import os

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #07111f 0%, #0d1b2a 45%, #132238 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #f4f7fb;
    }
    .stButton > button {
        background: linear-gradient(90deg, #1d4ed8, #0ea5e9);
        color: #ffffff;
        border-radius: 10px;
        border: 1px solid #60a5fa;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1e40af, #0284c7);
        color: #ffffff;
    }
    h1, h2, h3 {
        color: #f8fafc;
        text-align: center;
    }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.92);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 0.8rem;
        box-shadow: 0 8px 24px rgba(2, 6, 23, 0.35);
    }
    div[data-testid="stMetricLabel"] {
        color: #93c5fd;
        font-weight: 700;
    }
    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #334155;
        border-radius: 14px;
        background: rgba(15, 23, 42, 0.85);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 14px;
        overflow: hidden;
    }
    [data-testid="stCaptionContainer"] {
        color: #cbd5e1;
    }
    .info-card {
        background: linear-gradient(135deg, rgba(14, 116, 144, 0.25), rgba(30, 64, 175, 0.22));
        border: 1px solid #38bdf8;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        color: #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=60)
def load_traffic_data():
    if not os.path.exists("traffic_data.csv"):
        return None

    df = pd.read_csv("traffic_data.csv")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()
    if "Time" not in df.columns:
        return None

    numeric_columns = [col for col in df.columns if col.startswith("Lane") or col == "Total"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return df


def build_line_chart(dataframe, value_columns, legend_title, color_range):
    chart_data = dataframe[["Time"] + value_columns].melt(
        "Time",
        var_name="Series",
        value_name="Vehicles",
    )
    return (
        alt.Chart(chart_data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Time:N", title="Recorded Time", axis=alt.Axis(labelAngle=-25, labelColor="#cbd5e1")),
            y=alt.Y("Vehicles:Q", title="Vehicle Count", axis=alt.Axis(labelColor="#cbd5e1", gridColor="#334155")),
            color=alt.Color(
                "Series:N",
                scale=alt.Scale(range=color_range),
                legend=alt.Legend(title=legend_title, labelColor="#e2e8f0", titleColor="#f8fafc"),
            ),
            tooltip=["Time:N", "Series:N", "Vehicles:Q"],
        )
        .properties(height=340)
        .configure(background="transparent")
        .configure_view(strokeOpacity=0)
    )


df = load_traffic_data()

st.markdown("# Traffic Graph Dashboard", unsafe_allow_html=True)
st.markdown("**This page shows how vehicle counts change over time across each lane and overall traffic flow.**")

st.markdown(
    """
    <div class="info-card">
        <strong>How to explain this page:</strong><br/>
        The graphs below show traffic trends over time. Bright colored lines make it easy to compare
        total junction load and lane-wise congestion during your demo.
    </div>
    """,
    unsafe_allow_html=True,
)

if df is None or df.empty:
    st.warning("No traffic data found.")
else:
    lane_columns = [col for col in df.columns if col.startswith("Lane")]
    latest = df.iloc[-1]
    total_records = len(df)
    peak_total = int(df["Total"].max()) if "Total" in df.columns else 0
    avg_total = round(df["Total"].mean(), 1) if "Total" in df.columns else 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Records Collected", total_records)
    metric_cols[1].metric("Latest Total Vehicles", int(latest["Total"]) if "Total" in df.columns else 0)
    metric_cols[2].metric("Peak Total Traffic", peak_total)
    metric_cols[3].metric("Average Total Traffic", avg_total)

    if "Total" in df.columns:
        st.subheader("Overall Traffic Trend")
        st.altair_chart(
            build_line_chart(df, ["Total"], "Traffic Type", ["#f59e0b"]),
            use_container_width=True,
        )
        st.caption("Orange line shows the total detected vehicles at each recorded time.")

    if lane_columns:
        st.subheader("Lane-by-Lane Traffic Trend")
        st.altair_chart(
            build_line_chart(
                df,
                lane_columns,
                "Lane",
                ["#38bdf8", "#22c55e", "#f97316", "#e879f9"],
            ),
            use_container_width=True,
        )
        st.caption("Each lane has a separate color so congestion differences are easier to explain.")

    if "Emergency" in df.columns:
        emergency_count = int((df["Emergency"].astype(str).str.upper() == "YES").sum())
        st.subheader("Emergency Vehicle Summary")
        st.write(f"Emergency detections recorded: **{emergency_count}**")

    with st.expander("Recent recorded values"):
        st.dataframe(df.tail(10), width="stretch", hide_index=True)

if st.button("Back to Dashboard"):
    st.switch_page("bord.py")

st.markdown(
    "<hr><p style='text-align:center;font-size:0.8em;color:#94a3b8;'>© 2026 Smart Traffic Control. All rights reserved.</p>",
    unsafe_allow_html=True,
)
