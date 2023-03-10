"""MOX Cover Platform."""

from typing import Any

from aiomox.device.curtain import Curtain as MoxCurtain, StateType
from aiomox.device.device import Device as MoxDevice
from aiomox.mox_client import MoxClient

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the cover platform."""
    if discovery_info is None:
        return
    entities = []
    for name, info in discovery_info.items():
        entities.append(
            MoxCoverEntity(
                name,
                info["id"],
                info["display_name"],
                hass.data[DOMAIN].get("MoxClient"),
            )
        )

    if len(entities) > 0:
        async_add_entities(entities)


class MoxCoverEntity(CoverEntity):
    """Mox Cover."""

    _is_closing: bool = False
    _is_opening: bool = False
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        device_name: str,
        device_id: int,
        friendly_name: str | None,
        mox_client: MoxClient,
    ) -> None:
        """Create new MoxCoverEntity."""
        super().__init__()
        self.device_name = friendly_name or device_name
        self._curtain = MoxCurtain(device_id, mox_client, self._callback)
        self._attr_unique_id = hex(device_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device_name

    async def _callback(self, device: MoxDevice, state_type: StateType) -> None:
        """Handle callback from mox platform."""
        if state_type == StateType.POSITION:
            self._is_opening = False
            self._is_closing = False
            self.async_write_ha_state()

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover."""
        return self._curtain.get_position()

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed, same as position 0."""
        return self._curtain.get_position() == 0

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._is_closing

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._is_opening

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self._curtain.get_position() < 100:
            self._is_opening = True
            await self._curtain.set_position(100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if self._curtain.get_position() > 0:
            self._is_closing = True
            await self._curtain.set_position(0)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Close the cover."""
        new_position = kwargs[ATTR_POSITION]
        cur_position = self._curtain.get_position()
        if cur_position < new_position:
            self._is_opening = True
        elif cur_position > new_position:
            self._is_closing = True

        await self._curtain.set_position(new_position)
