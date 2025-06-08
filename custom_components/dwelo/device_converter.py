"""Contains functions to convert Dwelo device data to the expected format."""

from .models import DweloThermostatData, DweloLockData, DweloLockState


def convert_to_thermostat(dwelo_device_data: any):
    """Convert a Dwelo device data to a DweloThermostatData object."""
    return DweloThermostatData(
        current_temperature=float(dwelo_device_data["temperature"]["value"]),
        mode=dwelo_device_data["mode"]["value"],
        target_temperature_cool=float(dwelo_device_data["setToCool"]["value"]),
        target_temperature_heat=float(dwelo_device_data["setToHeat"]["value"]),
        state=dwelo_device_data["state"]["value"],
    )


def convert_to_lock(dwelo_device_data: any, metadata: any) -> DweloLockData:
    """Convert a Dwelo device data to a DweloLockData object."""
    lock_state = dwelo_device_data.get("lock", {}).get("value", "unknown")
    # Map API state to DweloLockState enum, defaulting to UNLOCKED if unknown
    state_map = {
        "locked": DweloLockState.LOCKED,
        "unlocked": DweloLockState.UNLOCKED,
    }
    state = state_map.get(lock_state.lower(), DweloLockState.UNLOCKED)

    battery_level = int(dwelo_device_data.get("battery", {}).get("value", 0))
    is_online = metadata.is_online if metadata else False

    return DweloLockData(
        state=state,
        battery_level=battery_level,
        is_online=is_online,
    )