"""MOX Lock Platform."""

import asyncio
from typing import Any

from aiomox.device.device import Device
from aiomox.device.switch import StateType, Switch as MoxSwitch
from aiomox.mox_client import MoxClient

from homeassistant.components.lock import LockEntity
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
            MoxLockEntity(
                name,
                info["id"],
                info["display_name"],
                hass.data[DOMAIN].get("MoxClient"),
            )
        )

    if len(entities) > 0:
        async_add_entities(entities)


class MoxLockEntity(LockEntity):
    """Mox Lock (Based on a switch)."""

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
        self._switch = MoxSwitch(device_id, mox_client, self._callback)
        self._attr_unique_id = hex(device_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.device_name

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        return not self._switch.is_on()

    async def _callback(self, device: Device, state_type: StateType) -> None:
        """Handle callback from mox platform."""
        if state_type == StateType.ON_OFF:
            self.async_write_ha_state()

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        await self._switch.turn_off()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        await self._switch.turn_on()
        await asyncio.sleep(1)
        await self._switch.turn_off()

    async def async_open(self, **kwargs: Any) -> None:
        """Open the door latch."""
        await self.async_unlock()
