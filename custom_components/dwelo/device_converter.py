"""Contains functions to convert Dwelo device data to the expected format."""

from .models import DweloThermostatData


def convert_to_thermostat(dwelo_device_data: any):
    """Convert a Dwelo device data to a DweloThermostatData object."""
    return DweloThermostatData(
        current_temperature=float(dwelo_device_data["temperature"]["value"]),
        mode=dwelo_device_data["mode"]["value"],
        target_temperature_cool=float(dwelo_device_data["setToCool"]["value"]),
        target_temperature_heat=float(dwelo_device_data["setToHeat"]["value"]),
        state=dwelo_device_data["state"]["value"],
    )
