from __future__ import annotations

import random
from typing import Any

DEFAULT_ZONE_NAMES = ["Server Room", "Main Office", "Storage Vault"]
DEFAULT_INITIAL_TEMPERATURES = [72.0, 74.0, 68.0]
DEFAULT_FAN_THRESHOLD = 80.0
DEFAULT_ALARM_THRESHOLD = 95.0
DEFAULT_FAN_COOLING = 0.4
DEFAULT_TICKS = 30
DEFAULT_RANDOM_SEED = 42
AMBIENT_MIN = 0.1
AMBIENT_MAX = 0.5


def validate_configuration(
    zone_names: list[str],
    initial_temperatures: list[float],
    ticks: int,
    fan_cooling: float,
    fan_threshold: float,
    alarm_threshold: float,
    ambient_min: float = AMBIENT_MIN,
    ambient_max: float = AMBIENT_MAX,
) -> None:
    if not zone_names:
        raise ValueError("At least one zone is required.")
    if len(zone_names) != len(initial_temperatures):
        raise ValueError("Zone names and initial temperatures must have the same length.")
    if ticks <= 0:
        raise ValueError("Ticks must be greater than 0.")
    if fan_cooling < 0:
        raise ValueError("Fan cooling cannot be negative.")
    if fan_threshold >= alarm_threshold:
        raise ValueError("Alarm threshold must be greater than fan threshold.")
    if ambient_min < 0 or ambient_max < 0:
        raise ValueError("Ambient increases cannot be negative.")
    if ambient_min > ambient_max:
        raise ValueError("Ambient minimum cannot be greater than ambient maximum.")
    for zone_name, temperature in zip(zone_names, initial_temperatures):
        if not isinstance(temperature, (int, float)):
            raise ValueError(f"Initial temperature for {zone_name} must be numeric.")


def compute_zone_state(
    temp: float,
    fan_threshold: float,
    alarm_threshold: float,
) -> tuple[str, str, str]:
    if temp > alarm_threshold:
        return "EMERGENCY CRITICAL", "ON", "ON"
    if temp > fan_threshold:
        return "COOLING ACTIVE", "ON", "OFF"
    return "SAFE", "OFF", "OFF"


def run_simulation(
    zone_names: list[str],
    initial_temperatures: list[float],
    ticks: int,
    fan_cooling: float,
    random_seed: int,
    fan_threshold: float,
    alarm_threshold: float,
    ambient_min: float = AMBIENT_MIN,
    ambient_max: float = AMBIENT_MAX,
) -> tuple[list[dict[str, Any]], list[float]]:
    validate_configuration(
        zone_names,
        initial_temperatures,
        ticks,
        fan_cooling,
        fan_threshold,
        alarm_threshold,
        ambient_min,
        ambient_max,
    )

    rng = random.Random(int(random_seed))
    zone_temps = [float(value) for value in initial_temperatures]
    telemetry: list[dict[str, Any]] = []

    for tick in range(int(ticks)):
        for index, zone_name in enumerate(zone_names):
            ambient_increase = rng.uniform(ambient_min, ambient_max)
            measured_temp = zone_temps[index] + ambient_increase

            status, fan_status, alarm_status = compute_zone_state(
                measured_temp,
                fan_threshold,
                alarm_threshold,
            )

            post_control_temp = measured_temp
            if fan_status == "ON":
                post_control_temp -= fan_cooling

            zone_temps[index] = post_control_temp

            telemetry.append(
                {
                    "tick": tick,
                    "zone": zone_name,
                    "ambient_increase": ambient_increase,
                    "measured_temp": measured_temp,
                    "fan_status": fan_status,
                    "alarm_status": alarm_status,
                    "post_control_temp": post_control_temp,
                    "status": status,
                }
            )

    return telemetry, zone_temps


def summarize_simulation(
    telemetry: list[dict[str, Any]],
    final_temperatures: list[float],
    zone_names: list[str],
) -> dict[str, Any]:
    if not telemetry:
        raise ValueError("Telemetry is empty. Run the simulation first.")

    measured = [float(record["measured_temp"]) for record in telemetry]

    return {
        "total_ticks": len({int(record["tick"]) for record in telemetry}),
        "total_measurements": len(telemetry),
        "fan_activations": sum(record["fan_status"] == "ON" for record in telemetry),
        "alarm_activations": sum(record["alarm_status"] == "ON" for record in telemetry),
        "safe_records": sum(record["status"] == "SAFE" for record in telemetry),
        "cooling_records": sum(record["status"] == "COOLING ACTIVE" for record in telemetry),
        "critical_records": sum(record["status"] == "EMERGENCY CRITICAL" for record in telemetry),
        "max_measured_temp": max(measured),
        "min_measured_temp": min(measured),
        "final_temperatures": {
            name: float(temp)
            for name, temp in zip(zone_names, final_temperatures)
        },
    }


def run_stress_test() -> dict[str, Any]:
    telemetry, final_temperatures = run_simulation(
        DEFAULT_ZONE_NAMES,
        [94.0, 92.0, 90.0],
        20,
        0.05,
        42,
        DEFAULT_FAN_THRESHOLD,
        DEFAULT_ALARM_THRESHOLD,
    )

    passed = any(record["alarm_status"] == "ON" for record in telemetry)
    summary = summarize_simulation(
        telemetry,
        final_temperatures,
        DEFAULT_ZONE_NAMES,
    )

    return {
        "passed": passed,
        "telemetry": telemetry,
        "final_temperatures": final_temperatures,
        "summary": summary,
    }