import os

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
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(90deg, #1d4ed8, #0ea5e9);
        color: #ffffff;
        border-radius: 10px;
        border: 1px solid #60a5fa;
        font-weight: 600;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
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
    div[data-testid="stDataFrame"] {
        border: 1px solid #334155;
        border-radius: 14px;
        overflow: hidden;
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

st.markdown("# Saved Traffic Data Dashboard", unsafe_allow_html=True)
st.markdown("**This page stores the measured traffic values that can be reviewed, explained, or exported later.**")

st.markdown(
    """
    <div class="info-card">
        <strong>How to explain this page:</strong><br/>
        This table stores each saved traffic reading with time, lane-wise counts, and total vehicles.
        The brighter cards and table borders make each feature easier to see during the demo.
    </div>
    """,
    unsafe_allow_html=True,
)

if os.path.exists("traffic_data.csv"):
    df = pd.read_csv("traffic_data.csv")
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()

    if not df.empty and "Time" in df.columns:
        lane_columns = [col for col in df.columns if col.startswith("Lane")]
        total_value = int(pd.to_numeric(df["Total"], errors="coerce").fillna(0).iloc[-1]) if "Total" in df.columns else 0

        metric_cols = st.columns(3)
        metric_cols[0].metric("Saved Records", len(df))
        metric_cols[1].metric("Lane Columns", len(lane_columns))
        metric_cols[2].metric("Latest Total", total_value)

        st.subheader("Saved Dataset")
        st.dataframe(df, width="stretch", hide_index=True)

        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="traffic_data.csv",
            mime="text/csv",
        )
    else:
        st.warning("No traffic data found.")
else:
    st.warning("No data file found.")

if st.button("Back to Main Dashboard"):
    st.switch_page("bord.py")

st.markdown(
    "<hr><p style='text-align:center;font-size:0.8em;color:#94a3b8;'>© 2026 Smart Traffic Control. All rights reserved.</p>",
    unsafe_allow_html=True,
)
