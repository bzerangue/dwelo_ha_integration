"""Dwelo data models."""

from dataclasses import dataclass
from enum import Enum


class DweloDeviceType(Enum):
    """Dwelo device types."""

    THERMOSTAT = "thermostat"


class DweloThermostatMode(Enum):
    """Dwelo thermostat modes."""

    HEAT = "heat"
    COOL = "cool"
    OFF = "off"


class DweloThermostatState(Enum):
    """Dwelo thermostat states."""

    HEAT = "heat"
    COOL = "cool"
    IDLE = "idle"


@dataclass
class DweloDeviceMetadata:
    """A dwelo device."""

    uid: str
    device_type: DweloDeviceType
    given_name: str
    gateway_id: str
    is_active: bool
    is_online: bool
    date_registered: str


@dataclass
class DweloData:
    """Central data for dwelo."""

    entry_id: str
    client: any
    devices: dict[str, DweloDeviceMetadata]


@dataclass
class DweloThermostatData:
    """Dwelo thermostat data."""

    current_temperature: float
    mode: DweloThermostatMode
    target_temperature_cool: float
    target_temperature_heat: float
    state: str
