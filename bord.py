import csv
import os
import time

import cv2
import numpy as np
import streamlit as st


VIDEO_PATH = "vedios/8.mp4"
NUM_LANES = 3
BASE_TIME = 5
FACTOR = 2
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720


st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #000;
        color: #eee;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #111;
        color: #eee;
    }
    section[data-testid="stSidebar"] * {
        color: #eee !important;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        border-radius: 5px;
        padding: 0.5em 1em;
    }
    .stButton>button:hover {
        background-color: #155a8a;
    }
    h1, h2, h3 {
        color: #eee;
        text-align: center;
    }
    body, .stText, * {
        color: #eee !important;
    }
    input, textarea, select {
        color: #eee !important;
    }
    .lane-box {
        border: 1px solid #444;
        border-radius: 6px;
        padding: 4px;
        background-color: #111;
    }
    div[data-testid="stFileUploader"] {
        background-color: #222 !important;
        color: #eee !important;
        border: 1px solid #444;
    }
    div[data-testid="stFileUploader"] div,
    div[data-testid="stFileUploader"] svg,
    div[data-testid="stFileUploader"] p {
        background-color: #222 !important;
        color: #eee !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: #1f77b4 !important;
        color: #fff !important;
    }
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        background-color: #222 !important;
        color: #eee !important;
    }
    [data-testid="stFileUploader"] > div {
        background-color: #111;
        color: #eee;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 0.5rem;
    }
    .stFileUploader,
    .stFileUploader label,
    .stFileUploader span,
    .stFileUploader p {
        color: #eee !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style='display:flex;justify-content:center;margin-bottom:1rem;'>
        <div style='
            background: linear-gradient(90deg, #0f2740, #0072C6);
            color: #fff;
            padding: 0.9rem 1.4rem;
            border-radius: 12px;
            border: 1px solid #2d8fd5;
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            box-shadow: 0 6px 18px rgba(0, 114, 198, 0.25);
        '>SMART TRAFFIC CONTROL</div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("<h2 style='text-align:center;color:#0072C6;'>Settings</h2>", unsafe_allow_html=True)
    base_time_input = st.number_input("Base signal time (seconds)", min_value=1, value=BASE_TIME, step=1)

    st.markdown("---")
    st.markdown("<h3 style='color:#0072C6;'>Lane Videos</h3>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#eee;margin-bottom:0.2rem;'>Upload lane videos (each file = one lane)</div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Upload lane videos",
        type=["mp4", "avi", "mov"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    custom_paths = st.text_input("Or enter comma-separated paths manually")

st.markdown(
    """
    # SMART TRAFFIC CONTROL 
    """,
    unsafe_allow_html=True,
)
st.markdown("**Real-time traffic analysis and emergency vehicle detection **")

with st.expander("How to use this dashboard"):
    st.write(
        "Upload one or more lane videos on the left.\n"
        "If you upload a single video it will be split into three vertical lanes.\n"
        "The system counts vehicles and adjusts green signals accordingly.\n"
        "Visit the Graph or Data dashboards to inspect historical counts."
    )

st.markdown("---")
col_nav1, col_nav2 = st.columns(2)
if col_nav1.button("Graph Dashboard"):
    st.switch_page("pages/traffic_graph.py")
if col_nav2.button("Data Dashboard"):
    st.switch_page("pages/save_data.py")
st.markdown("---")


video_sources = []
if uploaded:
    os.makedirs("temp_videos", exist_ok=True)
    for upload in uploaded:
        file_name = os.path.basename(upload.name)
        file_name = "".join(c for c in file_name if c.isalnum() or c in " ._-()").strip()
        if not file_name:
            file_name = f"upload_{int(time.time())}.mp4"

        path = os.path.join("temp_videos", file_name)
        try:
            file_bytes = upload.getbuffer()
            if len(file_bytes) == 0 and os.path.exists(path):
                video_sources.append(path)
                continue

            with open(path, "wb") as file_obj:
                file_obj.write(file_bytes)
            video_sources.append(path)
        except OSError as exc:
            st.error(f"Failed to save uploaded video `{file_name}`: {exc}")

if custom_paths:
    for path in custom_paths.split(","):
        path = path.strip()
        if path:
            video_sources.append(path)

if not video_sources:
    video_sources = [VIDEO_PATH]

single_video_mode = len(video_sources) == 1
NUM_LANES = 3 if single_video_mode else len(video_sources)

if "frame_idx" not in st.session_state:
    st.session_state.frame_idx = 0

process_every_n_frames = 1

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

auto_refresh = st.sidebar.checkbox("Auto refresh stream", value=st.session_state.auto_refresh)
refresh_rate = st.sidebar.slider("Refresh interval (ms)", min_value=100, max_value=2000, value=800, step=100)
st.session_state.auto_refresh = auto_refresh
refresh_interval = f"{refresh_rate / 1000:.3f}s" if auto_refresh else None

if (
    "video_sources" not in st.session_state
    or st.session_state.video_sources != video_sources
    or "caps" not in st.session_state
):
    old_caps = st.session_state.get("caps", [])
    for cap in old_caps:
        try:
            cap.release()
        except Exception:
            pass

    st.session_state.video_sources = video_sources
    st.session_state.single_video_mode = single_video_mode
    st.session_state.caps = [cv2.VideoCapture(src) for src in video_sources]
    st.session_state.last_frames = [None] * NUM_LANES
    st.session_state.last_lane_counts = [0] * NUM_LANES
    st.session_state.last_emergencies = [False] * NUM_LANES

if "green_lane" not in st.session_state:
    st.session_state.green_lane = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "last_switch_time" not in st.session_state:
    st.session_state.last_switch_time = time.time()
if "base_time" not in st.session_state:
    st.session_state.base_time = BASE_TIME
if "last_frames" not in st.session_state:
    st.session_state.last_frames = [None] * NUM_LANES
if "last_lane_counts" not in st.session_state:
    st.session_state.last_lane_counts = [0] * NUM_LANES
if "last_emergencies" not in st.session_state:
    st.session_state.last_emergencies = [False] * NUM_LANES
if "duration" not in st.session_state:
    st.session_state.duration = st.session_state.base_time
if "last_write" not in st.session_state:
    st.session_state.last_write = time.time() - 300

if base_time_input != st.session_state.base_time:
    st.session_state.base_time = base_time_input
    st.session_state.duration = base_time_input


def detect_emergency_frame(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 150, 150])
    upper_blue = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    return cv2.countNonZero(mask) > 300


@st.cache_resource
def load_yolo():
    net = cv2.dnn.readNet("models/yolov3-tiny.weights", "models/yolov3-tiny.cfg")
    with open("models/coco.names") as file_obj:
        classes = file_obj.read().strip().split("\n")
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    return net, classes, output_layers


def process_lane_frame(frame, net, classes, output_layers):
    if frame is None:
        return None, 0, False

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    blob = cv2.dnn.blobFromImage(frame, 1 / 255, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outputs = net.forward(output_layers)

    count = 0
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.3 and class_id < len(classes):
                label = classes[class_id]
                if label in ["car", "truck", "bus", "motorbike"]:
                    count += 1

    emergency = detect_emergency_frame(frame)
    return frame, count, emergency


net, classes, output_layers = load_yolo()


def render_live_dashboard():
    caps = st.session_state.caps
    run_detection = (st.session_state.frame_idx % process_every_n_frames == 0)

    frames = []
    lane_counts = [0] * NUM_LANES
    emergencies = [False] * NUM_LANES

    if st.session_state.single_video_mode:
        cap = caps[0]
        ret, full_frame = cap.read()
        if not ret:
            cap.release()
            caps[0] = cv2.VideoCapture(st.session_state.video_sources[0])
            ret, full_frame = caps[0].read()

        if ret:
            full_frame = cv2.resize(full_frame, (FRAME_WIDTH, FRAME_HEIGHT))
            lane_width = FRAME_WIDTH // 3

            for lane_idx in range(3):
                x_start = lane_idx * lane_width
                x_end = (lane_idx + 1) * lane_width if lane_idx < 2 else FRAME_WIDTH
                lane_frame = full_frame[:, x_start:x_end]

                if run_detection:
                    processed_frame, count, emergency = process_lane_frame(
                        lane_frame, net, classes, output_layers
                    )
                    lane_counts[lane_idx] = count
                    emergencies[lane_idx] = emergency
                else:
                    processed_frame = cv2.resize(lane_frame, (FRAME_WIDTH // 3, FRAME_HEIGHT))
                    lane_counts[lane_idx] = st.session_state.last_lane_counts[lane_idx]
                    emergencies[lane_idx] = st.session_state.last_emergencies[lane_idx]

                frames.append(processed_frame)
        else:
            frames = st.session_state.last_frames.copy()
            lane_counts = st.session_state.last_lane_counts.copy()
            emergencies = st.session_state.last_emergencies.copy()
    else:
        for idx, cap in enumerate(caps):
            ret, frame = cap.read()
            if not ret:
                cap.release()
                caps[idx] = cv2.VideoCapture(st.session_state.video_sources[idx])
                ret, frame = caps[idx].read()

            if not ret:
                frames.append(st.session_state.last_frames[idx])
                lane_counts[idx] = st.session_state.last_lane_counts[idx]
                emergencies[idx] = st.session_state.last_emergencies[idx]
                continue

            if run_detection:
                processed_frame, count, emergency = process_lane_frame(
                    frame, net, classes, output_layers
                )
                lane_counts[idx] = count
                emergencies[idx] = emergency
            else:
                processed_frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                lane_counts[idx] = st.session_state.last_lane_counts[idx]
                emergencies[idx] = st.session_state.last_emergencies[idx]

            frames.append(processed_frame)

    st.session_state.last_frames = frames.copy()
    st.session_state.last_lane_counts = lane_counts.copy()
    st.session_state.last_emergencies = emergencies.copy()
    st.session_state.frame_idx += 1

    current_time = time.time()
    elapsed = current_time - st.session_state.start_time

    if any(emergencies):
        new_lane = emergencies.index(True)
        if new_lane != st.session_state.green_lane or elapsed >= st.session_state.duration:
            st.session_state.green_lane = new_lane
            st.session_state.duration = 15
            st.session_state.start_time = current_time
            st.session_state.last_switch_time = current_time
    else:
        if elapsed >= st.session_state.duration:
            new_lane = int(np.argmax(lane_counts))
            st.session_state.green_lane = new_lane
            st.session_state.duration = max(
                1, st.session_state.base_time + lane_counts[new_lane] * FACTOR
            )
            st.session_state.start_time = current_time
            st.session_state.last_switch_time = current_time

    time_left = max(
        int(st.session_state.duration - (current_time - st.session_state.start_time)),
        0,
    )

    current_time_write = time.time()
    if current_time_write - st.session_state.last_write >= 300:
        total = sum(lane_counts)
        file_exists = os.path.isfile("traffic_data.csv")
        with open("traffic_data.csv", "a", newline="") as file_obj:
            writer = csv.writer(file_obj)
            if not file_exists:
                header = ["Time"] + [f"Lane{i + 1}" for i in range(NUM_LANES)] + ["Total"]
                writer.writerow(header)
            row = [time.strftime("%H:%M:%S", time.localtime(current_time_write))] + lane_counts + [total]
            writer.writerow(row)
        st.session_state.last_write = current_time_write
        for i, count in enumerate(lane_counts, start=1):
            st.session_state[f"lane{i}"] = count
        st.session_state.total = total

    total = sum(lane_counts)

    if frames:
        st.subheader("Live Lane Feeds")
        cols_vid = st.columns(NUM_LANES)
        for i, frame in enumerate(frames):
            with cols_vid[i]:
                st.markdown(f"<div class='lane-box'><strong>Lane {i + 1}</strong><br/>", unsafe_allow_html=True)
                if frame is not None:
                    st.image(frame, channels="BGR", width=300)
                else:
                    st.write("(no frame)")
                st.markdown("</div>", unsafe_allow_html=True)

    cols = st.columns(NUM_LANES)
    for i in range(NUM_LANES):
        if i == st.session_state.green_lane:
            if time_left > 3:
                signal = "GREEN"
            elif time_left > 0:
                signal = "YELLOW"
            else:
                signal = "RED"
        else:
            signal = "RED"

        if emergencies[i]:
            signal += " ALERT"

        cols[i].metric(
            f"Lane {i + 1}",
            f"{lane_counts[i]} vehicles",
            signal,
        )

    st.subheader("Intersection Status")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Signal Time", f"{time_left} sec", delta_color="off")
    col2.metric("Total Vehicles", total, delta_color="off")
    col3.metric("Active Lane", st.session_state.green_lane + 1, delta_color="off")
    col4.metric("Base Time", f"{st.session_state.base_time} sec", delta_color="off")

    if any(emergencies):
        st.warning(
            "Emergency vehicle detected in lane(s): "
            + ", ".join(str(i + 1) for i, emergency in enumerate(emergencies) if emergency)
        )


live_dashboard_fragment = st.fragment(run_every=refresh_interval)(render_live_dashboard)
live_dashboard_fragment()

st.markdown(
    "<hr><p style='text-align:center;font-size:0.8em;color:#666;'>© 2026 Smart Traffic Control. All rights reserved.</p>",
    unsafe_allow_html=True,
)
