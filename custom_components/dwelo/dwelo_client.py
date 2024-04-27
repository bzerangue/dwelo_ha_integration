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

    def _get_headers(self):
        if not self._bearer_token:
            raise MissingBearerToken
        return {"authorization": self._bearer_token}

    def _transform_endpoint(self, endpoint: str) -> str:
        return f"{self._host}{endpoint}"

    async def _handle_dwelo_response(self, response: ClientResponse):
        if not response.ok:
            _LOGGER.error(f"Dwelo API returned an error: {response}")  # noqa: G004
            return None

        _LOGGER.info(f"Dwelo successful response: {response.status}")  # noqa: G004

        return await response.json()

    async def _get(self, endpoint: str) -> any:
        response = await self._session.get(
            self._transform_endpoint(endpoint), headers=self._get_headers()
        )

        return await self._handle_dwelo_response(response)

    async def _post(self, endpoint: str, json_payload: object) -> any:
        _LOGGER.info(f"Dwelo API request: {json_payload}")  # noqa: G004
        response = await self._session.post(
            self._transform_endpoint(endpoint),
            headers=self._get_headers(),
            json=json_payload,
        )

        return await self._handle_dwelo_response(response)

    async def get_devices(self) -> dict[str, DweloDeviceMetadata]:
        device_details = await self._get(self.DEVICE_ENDPOINT)
        if not device_details:
            return {}

        grouped_devices = {}
        for dev in device_details["results"]:
            mapped_device = self._response_entry_to_device(dev)
            grouped_devices[dev["uid"]] = mapped_device
            if mapped_device.gateway_id not in self._registered_gateways:
                self._registered_gateways.add(mapped_device.gateway_id)

        return grouped_devices

    async def get_thermostat_device_data(
        self, device_metadata: DweloDeviceMetadata
    ) -> DweloThermostatData:
        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return None

        gateway_data = await self._get(
            f"{self.GATEWAY_ENDPOINT}{device_metadata.gateway_id}"
        )
        if not gateway_data:
            return None

        device_data = {}
        for sensor in gateway_data["results"]:
            if sensor["deviceId"] == device_metadata.uid:
                device_data[sensor["sensorType"]] = sensor

        return convert_to_thermostat(device_data)

    async def set_thermostat_temperature(
        self,
        device_metadata: DweloDeviceMetadata,
        temperature: float,
        mode: DweloThermostatMode,
    ) -> bool:
        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return False

        await self._post(
            f"{self.DEVICE_ENDPOINT}{device_metadata.uid}/command/",
            {"command": mode, "commandValue": temperature},
        )

    async def set_thermostat_mode(
        self, device_metadata: DweloDeviceMetadata, mode: DweloThermostatMode
    ) -> bool:
        if device_metadata.device_type != "thermostat":
            _LOGGER.error(f"Device is not a thermostat: {device_metadata}")  # noqa: G004
            return False

        await self._post(
            f"{self.DEVICE_ENDPOINT}{device_metadata.uid}/command/",
            {"command": mode},
        )


class MissingBearerToken(Exception):
    """Raised when the bearer token is missing."""
