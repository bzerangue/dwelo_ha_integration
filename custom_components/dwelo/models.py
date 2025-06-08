"""Dwelo data models."""

from dataclasses import dataclass
from enum import Enum


class DweloDeviceType(Enum):
    """Dwelo device types."""

    THERMOSTAT = "thermostat"
    LOCK = "lock"


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

class DweloLockState(Enum):
    """Dwelo lock states."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"


@dataclass
class DweloDeviceMetadata:
    """A dwelo device."""

    uid: str
    device_type: DweloDeviceType
    given_name: str
    gateway_id: int
    is_active: bool
    is_online: bool
    date_registered: str


@dataclass
class DweloData:
    """Central data for dwelo."""

    entry_id: str
    client: any
    device_metadata: dict[str, DweloDeviceMetadata]


@dataclass
class DweloThermostatData:
    """Dwelo thermostat data."""

    current_temperature: float
    mode: DweloThermostatMode
    target_temperature_cool: float
    target_temperature_heat: float
    state: str


@dataclass
class DweloLockData:
    """Dwelo lock data."""

    state: DweloLockState
    battery_level: int
    is_online: bool