import logging

from aiohttp import ClientResponse, ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .device_converter import convert_to_thermostat
from .models import DweloDeviceMetadata, DweloThermostatData, DweloThermostatMode

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
            _LOGGER.error(f"Dwelo auth returned an error: {response}")  # noqa: G004
            return False

        _LOGGER.info(f"Dwelo auth success: {response.status}")  # noqa: G004
        response_json = await response.json()
        self._bearer_token = response_json["token"]
        return True

    def _response_entry_to_device(self, entry) -> DweloDeviceMetadata:
        return DweloDeviceMetadata(
            uid=entry["uid"],
            device_type=entry["deviceType"],
            given_name=entry["givenName"],
            gateway_id=entry["gatewayId"],
            is_active=entry["isActive"],
            is_online=entry["isOnline"],
            date_registered=entry["dateRegistered"],
        )

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
            _LOGGER.error(f"Dwelo API returned an error: {response}")  # noqa: G004
            return None

        _LOGGER.debug(f"Dwelo successful response: {response.status}")  # noqa: G004

        return await response.json()

    async def get(self, endpoint: str) -> any:
        """Make a GET request to the Dwelo API."""
        _LOGGER.debug(f"Making request to Dwelo API endpoint {endpoint}")  # noqa: G004
        response = await self._session.get(
            self._transform_endpoint(endpoint), headers=self._get_headers()
        )

        return await self._handle_dwelo_response(response)

    async def post(self, endpoint: str, json_payload: object) -> any:
        """Make a POST request to the Dwelo API."""
        _LOGGER.debug(
            f"Making request to Dwelo API endpoint {endpoint} with payload: {json_payload}"  # noqa: G004
        )
        response = await self._session.post(
            self._transform_endpoint(endpoint),
            headers=self._get_headers(),
            json=json_payload,
        )

        return await self._handle_dwelo_response(response)

    async def get_devices(self) -> dict[str, DweloDeviceMetadata]:
        """Get all devices from the Dwelo API."""
        device_details = await self.get(self.DEVICE_ENDPOINT)
        if not device_details:
            return {}

        grouped_devices = {}
        for dev in device_details["results"]:
            mapped_device = self._response_entry_to_device(dev)
            grouped_devices[dev["uid"]] = mapped_device
            if mapped_device.gateway_id not in self._registered_gateways:
                self._registered_gateways.add(mapped_device.gateway_id)

        return grouped_devices


class MissingBearerToken(Exception):
    """Raised when the bearer token is missing."""
