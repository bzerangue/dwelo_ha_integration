import logging

from aiohttp import ClientResponse, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .device_converter import convert_to_thermostat
try:
    from .models import (
        DweloDeviceMetadata,
        DweloThermostatData,
        DweloThermostatMode,
        DweloLockState,
        DweloLockData,
        DweloDeviceType,
    )
except ImportError as e:
    _LOGGER.error(f"Failed to import models: {e}")
    raise

_LOGGER = logging.getLogger(__name__)

APPLICATION_ID = "concierge"


class DweloClient:
    """The Dwelo client for interfacing with the Dwelo API."""

    DEVICE_ENDPOINT = "device/"
    GATEWAY_ENDPOINT = "sensor/gateway/"
    LOGIN_ENDPOINT = "login/"

    def __init__(
        self,
        host: str,
        hass: HomeAssistant,
        email: str,
        password: str,
    ) -> None:
        """Create a Dwelo client."""
        self._host = host if host.endswith("/") else host + "/"
        self._email = email
        self._password = password
        self._session: ClientSession = async_create_clientsession(hass)

        # Dwelo seems to operate on gateways. Exactly what that is, I'm not sure,
        # but every device has a parent gateway. These are currently tracked but unused
        self._registered_gateways = set()
        self._bearer_token = None
        _LOGGER.debug(f"DweloDeviceType imported: {DweloDeviceType}")

    async def login(self) -> bool:
        """Login to the Dwelo API."""
        response = await self._session.post(
            self._transform_endpoint(self.LOGIN_ENDPOINT),
            json={
                "email": self._email,
                "password": self._password,
                "applicationId": APPLICATION_ID,
            },
        )

        if not response.ok:
            _LOGGER.error(f"Dwelo auth returned an error: {response}")
            return False

        _LOGGER.info(f"Dwelo auth success: {response.status}")
        response_json = await response.json()
        self._bearer_token = response_json["token"]
        return True

    def _response_entry_to_device(self, entry) -> DweloDeviceMetadata:
        """Convert a Dwelo API device entry to DweloDeviceMetadata."""
        try:
            device_type_str = entry["deviceType"]
            device_type = DweloDeviceType(device_type_str)
            metadata = DweloDeviceMetadata(
                uid=str(entry["uid"]),
                device_type=device_type,
                given_name=entry["givenName"],
                gateway_id=str(entry["gatewayId"]),
                is_active=entry["isActive"],
                is_online=entry["isOnline"],
                date_registered=entry["dateRegistered"],
            )
            _LOGGER.debug(f"Parsed device metadata: {metadata}")
            return metadata
        except KeyError as e:
            _LOGGER.error(f"Missing field in device entry {entry.get('uid', 'unknown')}: {e}")
            raise
        except ValueError as e:
            _LOGGER.error(f"Invalid device type for {entry.get('uid', 'unknown')}: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Failed to parse device {entry.get('uid', 'unknown')}: {e}")
            raise

    def _transform_endpoint(self, endpoint: str) -> str:
        """Transform an endpoint to the correct format."""
        return f"{self._host}{endpoint}"

    def _get_headers(self):
        """Get headers required for making an authorized call to Dwelo."""
        if not self._bearer_token:
            raise MissingBearerToken
        return {"authorization": self._bearer_token}

    async def _handle_dwelo_response(self, response: ClientResponse):
        """Handle a Dwelo API response and get the json body."""
        if not response.ok:
            response_text = await response.text()
            _LOGGER.error(f"Dwelo API returned an error: {response.status}, {response_text}")
            return None

        _LOGGER.debug(f"Dwelo successful response: {response.status}")
        return await response.json()

    async def get(self, endpoint: str) -> any:
        """Make a GET request to the Dwelo API."""
        _LOGGER.debug(f"Making request to Dwelo API endpoint {endpoint}")
        response = await self._session.get(
            self._transform_endpoint(endpoint), headers=self._get_headers()
        )
        return await self._handle_dwelo_response(response)

    async def post(self, endpoint: str, json_payload: object) -> any:
        """Make a POST request to the Dwelo API."""
        _LOGGER.debug(
            f"Making request to Dwelo API endpoint {self._transform_endpoint(endpoint)} with payload: {json_payload}"
        )
        response = await self._session.post(
            self._transform_endpoint(endpoint),
            headers=self._get_headers(),
            json=json_payload,
        )
        response_text = await response.text()
        _LOGGER.debug(f"POST response: {response.status}, {response_text}")
        return await self._handle_dwelo_response(response)

    async def get_devices(self) -> dict[str, DweloDeviceMetadata]:
        """Get all devices from the Dwelo API."""
        # Use gateway_id from registered gateways or a default if none registered
        gateway_id = next(iter(self._registered_gateways), "999999")
        device_details = await self.get(
            f"{self.DEVICE_ENDPOINT}?gatewayId={gateway_id}&limit=5000&offset=0"
        )
        if not device_details or "results" not in device_details:
            _LOGGER.error("Failed to fetch devices")
            return {}

        _LOGGER.debug(f"Raw device details: {device_details['results']}")
        grouped_devices = {}
        for dev in device_details["results"]:
            try:
                mapped_device = self._response_entry_to_device(dev)
                grouped_devices[mapped_device.uid] = mapped_device
                if mapped_device.gateway_id not in self._registered_gateways:
                    self._registered_gateways.add(mapped_device.gateway_id)
            except Exception as e:
                _LOGGER.error(f"Skipping device {dev.get('uid', 'unknown')}: {e}")

        _LOGGER.debug(f"Retrieved devices: {grouped_devices}")
        return grouped_devices


class MissingBearerToken(Exception):
    """Raised when the bearer token is missing."""