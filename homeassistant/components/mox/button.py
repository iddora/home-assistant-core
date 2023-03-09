"""MOX Button Platform."""

import asyncio

from aiomox.device.switch import Switch as MoxSwitch
from aiomox.mox_client import MoxClient

from homeassistant.components.button import ButtonEntity
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
    """Set up the button platform."""
    if discovery_info is None:
        return
    entities = []
    for name, info in discovery_info.items():
        entities.append(
            MoxButtonEntity(
                name,
                info["id"],
                info["display_name"],
                hass.data[DOMAIN].get("MoxClient"),
            )
        )

    if len(entities) > 0:
        async_add_entities(entities)


class MoxButtonEntity(ButtonEntity):
    """Mox Switch."""

    def __init__(
        self,
        device_name: str,
        device_id: int,
        friendly_name: str | None,
        mox_client: MoxClient,
    ) -> None:
        """Create new MoxButtonEntity."""
        super().__init__()
        self.device_name = friendly_name or device_name
        self._switch = MoxSwitch(device_id, mox_client)
        self._attr_unique_id = hex(device_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device_name

    async def async_press(self) -> None:
        """Press the button."""
        await self._switch.turn_on()
        await asyncio.sleep(1)
        await self._switch.turn_off()
