"""MOX Switch Platform."""

from typing import Any

from aiomox.device.device import Device
from aiomox.device.switch import StateType, Switch as MoxSwitch
from aiomox.mox_client import MoxClient

from homeassistant.components.switch import SwitchEntity
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
    """Set up the switch platform."""
    if discovery_info is None:
        return

    entities = []
    for name, info in discovery_info.items():
        entities.append(
            MoxSwitchEntity(
                name,
                info["id"],
                info["display_name"],
                hass.data[DOMAIN].get("MoxClient"),
            )
        )

    if len(entities) > 0:
        async_add_entities(entities)


class MoxSwitchEntity(SwitchEntity):
    """Mox Switch."""

    def __init__(
        self,
        device_name: str,
        device_id: int,
        friendly_name: str | None,
        mox_client: MoxClient,
    ) -> None:
        """Create new MoxSwitchEntity."""
        super().__init__()
        self.device_name = friendly_name or device_name
        self._switch = MoxSwitch(device_id, mox_client, self.switch_callback)
        self._attr_unique_id = hex(device_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device_name

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._switch.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._switch.turn_off()

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._switch.is_on()

    async def switch_callback(self, device: Device, state_type: StateType) -> None:
        """Handle callback from mox platform."""
        if state_type == StateType.ON_OFF:
            self.async_write_ha_state()
