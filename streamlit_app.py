import pandas as pd
import plotly.express as px
import streamlit as st

from baseline_simulator import (
    AMBIENT_MAX,
    AMBIENT_MIN,
    DEFAULT_ALARM_THRESHOLD,
    DEFAULT_FAN_COOLING,
    DEFAULT_FAN_THRESHOLD,
    DEFAULT_INITIAL_TEMPERATURES,
    DEFAULT_RANDOM_SEED,
    DEFAULT_TICKS,
    DEFAULT_ZONE_NAMES,
    run_simulation,
    run_stress_test,
    summarize_simulation,
)

st.set_page_config(
    page_title="Baseline Multi-Zone Temperature Simulator",
    page_icon="🖥️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {background:#e8e6df;color:#242424;}
    [data-testid="stSidebar"] {background:#d6d4cc;border-right:1px solid #77776f;}
    [data-testid="stMetric"] {background:#dedcd4;border:1px solid #8b8a82;border-radius:4px;padding:.75rem;}
    .sim-strip {font-family:"Courier New",monospace;border:1px solid #77776f;background:#282b2a;color:#ece9df;padding:.55rem .8rem;margin:.25rem 0 1rem;border-radius:3px;font-size:.9rem;}
    .zone-panel {border:1px solid #77776f;background:#d6d4cc;padding:.9rem;border-radius:4px;min-height:210px;}
    .zone-title {font-family:"Courier New",monospace;font-weight:700;font-size:1rem;border-bottom:1px solid #8b8a82;padding-bottom:.45rem;margin-bottom:.65rem;}
    .reading {font-family:"Courier New",monospace;font-size:1rem;line-height:1.7;}
    .safe {color:#56705c;font-weight:700;}
    .cooling {color:#9b672d;font-weight:700;}
    .critical {color:#9a4444;font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_INPUTS = {
    "server_temp": float(DEFAULT_INITIAL_TEMPERATURES[0]),
    "office_temp": float(DEFAULT_INITIAL_TEMPERATURES[1]),
    "vault_temp": float(DEFAULT_INITIAL_TEMPERATURES[2]),
    "fan_threshold": float(DEFAULT_FAN_THRESHOLD),
    "alarm_threshold": float(DEFAULT_ALARM_THRESHOLD),
    "fan_cooling": float(DEFAULT_FAN_COOLING),
    "ticks": int(DEFAULT_TICKS),
    "random_seed": int(DEFAULT_RANDOM_SEED),
    "simulation_mode": "Complete Run",
}


def initialize_state():
    for key, value in DEFAULT_INPUTS.items():
        st.session_state.setdefault(key, value)

    st.session_state.setdefault("telemetry", None)
    st.session_state.setdefault("final_temperatures", None)
    st.session_state.setdefault("run_status", "READY")
    st.session_state.setdefault("run_type", "BASELINE")
    st.session_state.setdefault("visible_tick", None)
    st.session_state.setdefault("active_fan_threshold", float(DEFAULT_FAN_THRESHOLD))
    st.session_state.setdefault("active_alarm_threshold", float(DEFAULT_ALARM_THRESHOLD))
    st.session_state.setdefault("stress_passed", None)


def clear_results():
    st.session_state.telemetry = None
    st.session_state.final_temperatures = None
    st.session_state.run_status = "READY"
    st.session_state.run_type = "BASELINE"
    st.session_state.visible_tick = None
    st.session_state.active_fan_threshold = float(DEFAULT_FAN_THRESHOLD)
    st.session_state.active_alarm_threshold = float(DEFAULT_ALARM_THRESHOLD)
    st.session_state.stress_passed = None


def reset_all():
    for key, value in DEFAULT_INPUTS.items():
        st.session_state[key] = value
    clear_results()


def execute_user_run(step_mode=False):
    telemetry, final_temperatures = run_simulation(
        zone_names=DEFAULT_ZONE_NAMES,
        initial_temperatures=[
            float(st.session_state.server_temp),
            float(st.session_state.office_temp),
            float(st.session_state.vault_temp),
        ],
        ticks=int(st.session_state.ticks),
        fan_cooling=float(st.session_state.fan_cooling),
        random_seed=int(st.session_state.random_seed),
        fan_threshold=float(st.session_state.fan_threshold),
        alarm_threshold=float(st.session_state.alarm_threshold),
    )

    st.session_state.telemetry = telemetry
    st.session_state.final_temperatures = final_temperatures
    st.session_state.active_fan_threshold = float(st.session_state.fan_threshold)
    st.session_state.active_alarm_threshold = float(st.session_state.alarm_threshold)
    st.session_state.run_type = "BASELINE"
    st.session_state.stress_passed = None

    if step_mode:
        st.session_state.visible_tick = 0
        st.session_state.run_status = "STEP MODE"
    else:
        st.session_state.visible_tick = int(st.session_state.ticks) - 1
        st.session_state.run_status = "COMPLETE"


def execute_stress_test():
    result = run_stress_test()
    st.session_state.telemetry = result["telemetry"]
    st.session_state.final_temperatures = result["final_temperatures"]
    st.session_state.active_fan_threshold = float(DEFAULT_FAN_THRESHOLD)
    st.session_state.active_alarm_threshold = float(DEFAULT_ALARM_THRESHOLD)
    st.session_state.run_type = "STRESS TEST"
    st.session_state.visible_tick = 19
    st.session_state.run_status = "COMPLETE"
    st.session_state.stress_passed = bool(result["passed"])


initialize_state()

st.title("BASELINE MULTI-ZONE TEMPERATURE SIMULATOR")
st.caption("Interactive synthetic thermal-control simulation environment")

with st.sidebar:
    st.header("SIMULATION CONTROLS")

    st.subheader("Initial Conditions")
    st.slider("Server Room Start (°F)", 50.0, 110.0, step=0.5, key="server_temp")
    st.slider("Main Office Start (°F)", 50.0, 110.0, step=0.5, key="office_temp")
    st.slider("Storage Vault Start (°F)", 50.0, 110.0, step=0.5, key="vault_temp")

    st.subheader("Controller Parameters")
    st.slider("Fan Threshold (°F)", 60.0, 100.0, step=0.5, key="fan_threshold")
    st.slider("Alarm Threshold (°F)", 65.0, 120.0, step=0.5, key="alarm_threshold")
    st.slider("Fan Cooling (°F/tick)", 0.0, 5.0, step=0.05, key="fan_cooling")

    st.subheader("Simulation Parameters")
    st.number_input("Ticks", min_value=1, max_value=200, step=1, key="ticks")
    st.number_input(
        "Random Seed",
        min_value=0,
        step=1,
        key="random_seed",
        help="The same seed and settings reproduce the same environmental sequence.",
    )

    st.caption(
        f"Ambient rise: +{AMBIENT_MIN:.2f}°F to +{AMBIENT_MAX:.2f}°F per tick"
    )

    st.radio(
        "Simulation Mode",
        ["Complete Run", "Step-by-Step"],
        key="simulation_mode",
    )

    config_valid = (
        float(st.session_state.alarm_threshold)
        > float(st.session_state.fan_threshold)
    )

    if not config_valid:
        st.error("Alarm Threshold must be higher than Fan Threshold.")

    run_clicked = False
    step_start_clicked = False
    next_tick_clicked = False

    if st.session_state.simulation_mode == "Complete Run":
        run_clicked = st.button(
            "RUN SIMULATION",
            type="primary",
            use_container_width=True,
        )
    else:
        step_start_clicked = st.button(
            "START / RESTART STEP MODE",
            type="primary",
            use_container_width=True,
        )
        next_tick_clicked = st.button(
            "NEXT TICK",
            use_container_width=True,
            disabled=st.session_state.telemetry is None,
        )

    stress_clicked = st.button("RUN STRESS TEST", use_container_width=True)

    st.button(
        "RESET",
        use_container_width=True,
        on_click=reset_all,
    )

if run_clicked and config_valid:
    try:
        execute_user_run(step_mode=False)
    except ValueError as error:
        st.session_state.run_status = "CONFIG ERROR"
        st.error(str(error))

if step_start_clicked and config_valid:
    try:
        execute_user_run(step_mode=True)
    except ValueError as error:
        st.session_state.run_status = "CONFIG ERROR"
        st.error(str(error))

if next_tick_clicked and st.session_state.telemetry is not None:
    max_tick = max(int(record["tick"]) for record in st.session_state.telemetry)
    current_tick = int(st.session_state.visible_tick or 0)
    st.session_state.visible_tick = min(current_tick + 1, max_tick)

    if st.session_state.visible_tick >= max_tick:
        st.session_state.run_status = "COMPLETE"
    else:
        st.session_state.run_status = "STEP MODE"

if stress_clicked:
    execute_stress_test()

status_seed = 42 if st.session_state.run_type == "STRESS TEST" else int(st.session_state.random_seed)
status_ticks = 20 if st.session_state.run_type == "STRESS TEST" else int(st.session_state.ticks)

st.markdown(
    f"""
    <div class="sim-strip">
    SIMULATION: {st.session_state.run_status}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    MODE: {st.session_state.run_type}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    SEED: {status_seed}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    TICKS: {status_ticks}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    MODEL: SYNTHETIC THERMAL
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.stress_passed is True:
    st.success("STRESS TEST PASSED — Alarm branch successfully activated.")
elif st.session_state.stress_passed is False:
    st.error("STRESS TEST FAILED — No zone entered the alarm state.")

if st.session_state.telemetry is None:
    st.info("Configure parameters in the sidebar, then run the simulation.")
    columns = st.columns(3)
    initial_temperatures = [
        st.session_state.server_temp,
        st.session_state.office_temp,
        st.session_state.vault_temp,
    ]

    for column, zone_name, temperature in zip(
        columns,
        DEFAULT_ZONE_NAMES,
        initial_temperatures,
    ):
        with column:
            st.markdown(
                f"""
                <div class="zone-panel">
                    <div class="zone-title">{zone_name.upper()}</div>
                    <div class="reading">
                    INITIAL TEMP&nbsp;&nbsp;{float(temperature):.2f} °F<br>
                    FAN&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;OFF<br>
                    ALARM&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;OFF<br>
                    STATE&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;READY
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    full_df = pd.DataFrame(st.session_state.telemetry)
    visible_tick = int(st.session_state.visible_tick)

    visible_df = full_df[full_df["tick"] <= visible_tick].copy()
    current_df = visible_df[visible_df["tick"] == visible_tick].copy()

    st.subheader(f"ZONE STATUS — TICK {visible_tick}")
    zone_columns = st.columns(3)

    for column, zone_name in zip(zone_columns, DEFAULT_ZONE_NAMES):
        zone_rows = current_df[current_df["zone"] == zone_name]
        if zone_rows.empty:
            continue

        zone_row = zone_rows.iloc[-1]
        status = str(zone_row["status"])

        if status == "SAFE":
            status_class = "safe"
        elif status == "COOLING ACTIVE":
            status_class = "cooling"
        else:
            status_class = "critical"

        with column:
            st.markdown(
                f"""
                <div class="zone-panel">
                    <div class="zone-title">{zone_name.upper()}</div>
                    <div class="reading">
                    MEASURED&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{zone_row["measured_temp"]:.2f} °F<br>
                    POST-CONTROL&nbsp;{zone_row["post_control_temp"]:.2f} °F<br>
                    AMBIENT RISE&nbsp;+{zone_row["ambient_increase"]:.2f} °F<br><br>
                    FAN&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{zone_row["fan_status"]}<br>
                    ALARM&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{zone_row["alarm_status"]}<br>
                    STATE&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                    <span class="{status_class}">{status}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    current_temperatures = [
        float(
            current_df[current_df["zone"] == zone_name]["post_control_temp"].iloc[-1]
        )
        for zone_name in DEFAULT_ZONE_NAMES
    ]

    summary = summarize_simulation(
        visible_df.to_dict("records"),
        current_temperatures,
        DEFAULT_ZONE_NAMES,
    )

    st.subheader("SIMULATION SUMMARY")
    metric_columns = st.columns(4)
    metric_columns[0].metric("Ticks Processed", summary["total_ticks"])
    metric_columns[1].metric("Measurements", summary["total_measurements"])
    metric_columns[2].metric("Fan Activations", summary["fan_activations"])
    metric_columns[3].metric("Alarm Activations", summary["alarm_activations"])

    second_metric_row = st.columns(4)
    second_metric_row[0].metric("Maximum Measured", f'{summary["max_measured_temp"]:.2f} °F')
    second_metric_row[1].metric("Minimum Measured", f'{summary["min_measured_temp"]:.2f} °F')
    second_metric_row[2].metric("Safe Records", summary["safe_records"])
    second_metric_row[3].metric("Critical Records", summary["critical_records"])

    st.subheader("ZONE TEMPERATURE HISTORY")

    temperature_figure = px.line(
        visible_df,
        x="tick",
        y="post_control_temp",
        color="zone",
        markers=True,
        labels={
            "tick": "Simulation Tick",
            "post_control_temp": "Post-Control Temperature (°F)",
            "zone": "Zone",
        },
        hover_data={
            "measured_temp": ":.2f",
            "post_control_temp": ":.2f",
            "ambient_increase": ":.2f",
            "fan_status": True,
            "alarm_status": True,
            "status": True,
        },
    )

    temperature_figure.add_hline(
        y=st.session_state.active_fan_threshold,
        line_dash="dash",
        annotation_text="Fan Threshold",
    )

    temperature_figure.add_hline(
        y=st.session_state.active_alarm_threshold,
        line_dash="dash",
        annotation_text="Alarm Threshold",
    )

    temperature_figure.update_layout(
        template="plotly_white",
        legend_title_text="Zone",
        margin=dict(l=20, r=20, t=30, b=20),
    )

    st.plotly_chart(temperature_figure, use_container_width=True)

    st.subheader("CONTROLLER ACTIVITY")

    activity_figure = px.scatter(
        visible_df,
        x="tick",
        y="zone",
        color="status",
        labels={
            "tick": "Simulation Tick",
            "zone": "Zone",
            "status": "Controller State",
        },
        hover_data={
            "fan_status": True,
            "alarm_status": True,
            "measured_temp": ":.2f",
            "post_control_temp": ":.2f",
        },
    )

    activity_figure.update_traces(marker=dict(size=10))
    activity_figure.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=20, b=20),
    )

    st.plotly_chart(activity_figure, use_container_width=True)

    with st.expander("RAW SIMULATION TELEMETRY"):
        filter_columns = st.columns(2)

        selected_zones = filter_columns[0].multiselect(
            "Filter by zone",
            options=DEFAULT_ZONE_NAMES,
            default=DEFAULT_ZONE_NAMES,
        )

        status_options = [
            "SAFE",
            "COOLING ACTIVE",
            "EMERGENCY CRITICAL",
        ]

        selected_statuses = filter_columns[1].multiselect(
            "Filter by status",
            options=status_options,
            default=status_options,
        )

        filtered_df = visible_df[
            visible_df["zone"].isin(selected_zones)
            & visible_df["status"].isin(selected_statuses)
        ].copy()

        display_df = filtered_df.rename(
            columns={
                "tick": "Tick",
                "zone": "Zone",
                "ambient_increase": "Ambient Increase",
                "measured_temp": "Measured Temperature",
                "fan_status": "Fan",
                "alarm_status": "Alarm",
                "post_control_temp": "Post-Control Temperature",
                "status": "Status",
            }
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.download_button(
            "DOWNLOAD TELEMETRY CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="baseline_simulation_telemetry.csv",
            mime="text/csv",
        )

with st.expander("HOW THE BASELINE SIMULATOR WORKS"):
    st.markdown(
        f"""
1. Each zone begins at its selected starting temperature.
2. Every tick adds a pseudorandom ambient increase between
   **{AMBIENT_MIN:.2f}°F and {AMBIENT_MAX:.2f}°F**.
3. The controller evaluates the resulting **measured temperature**.
4. If measured temperature is strictly greater than the fan threshold,
   the fan turns on.
5. If measured temperature is strictly greater than the alarm threshold,
   the alarm also turns on.
6. Fan cooling is applied **after** the controller makes its decision.
7. The resulting **post-control temperature** becomes the starting
   temperature for the next tick.
8. Each zone and tick produces one telemetry record.
9. A fixed random seed allows identical runs to be reproduced.

**Baseline model only:** Ambient warming and fan-cooling values are synthetic
teaching parameters. They are not a validated physical thermal model.
        """
    )