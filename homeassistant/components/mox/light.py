"""MOX light platform."""

from enum import Enum
from typing import Any

from aiomox.device.device import Device as MoxDevice
from aiomox.device.dimmer import Dimmer as MoxDimmer, StateType as DST
from aiomox.device.switch import StateType as SST, Switch as MoxSwitch
from aiomox.mox_client import MoxClient

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
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
    """Set up the light platform."""
    if discovery_info is None:
        return

    entities: list[MoxLightEntity] = []
    for name, info in discovery_info.items():
        if info.get("type") == "dimmer":
            entities.append(
                MoxDimmerEntity(
                    name,
                    info.get("id"),
                    info.get("display_name"),
                    hass.data[DOMAIN].get("MoxClient"),
                )
            )
        else:
            entities.append(
                MoxLightEntity(
                    name,
                    info.get("id"),
                    info.get("display_name"),
                    hass.data[DOMAIN].get("MoxClient"),
                )
            )

    if len(entities) > 0:
        async_add_entities(entities)


class MoxLightEntity(LightEntity):
    """Mox Light."""

    _attr_supported_color_modes: set[ColorMode] = {ColorMode.ONOFF}
    _mox_device: MoxSwitch

    def __init__(
        self,
        device_name: str,
        device_id: int,
        friendly_name: str | None,
        mox_client: MoxClient,
    ) -> None:
        """Create new MoxLightEntity."""
        self._attr_name = friendly_name or device_name
        self._mox_device = self._create_mox_device(device_id, mox_client)
        self._attr_unique_id = hex(device_id)

    def _create_mox_device(self, device_id: int, mox_client: MoxClient) -> MoxSwitch:
        """Return an instance of the mox device."""
        return MoxSwitch(device_id, mox_client, self._callback)

    async def _callback(self, device: MoxDevice, state_type: Enum) -> None:
        """Handle callback from mox platform."""
        if state_type == SST.ON_OFF:
            self._attr_is_on = self._mox_device.is_on()
            self._attr_color_mode = ColorMode.ONOFF if self._attr_is_on else None
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._mox_device.turn_on()
        self._attr_is_on = True
        self._attr_color_mode = ColorMode.ONOFF

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._mox_device.turn_off()
        self._attr_is_on = False
        self._attr_color_mode = None


class MoxDimmerEntity(MoxLightEntity):
    """Mox Dimmer."""

    _attr_supported_color_modes: set[ColorMode] = {ColorMode.BRIGHTNESS}
    _mox_device: MoxDimmer

    def _create_mox_device(self, device_id: int, mox_client: MoxClient) -> MoxDimmer:
        """Return an instance of the mox device."""
        return MoxDimmer(device_id, mox_client, self._callback)

    def _update_brightness_state(self, luminous: int) -> None:
        """Update entity state from mox luminous value."""
        self._attr_brightness = MoxDimmerEntity._mox_to_ha(luminous)
        self._attr_is_on = bool(luminous)
        self._attr_color_mode = ColorMode.BRIGHTNESS if luminous else None

    async def _callback(self, device: MoxDevice, state_type: Enum) -> None:
        """Handle callback from mox platform."""
        if state_type == DST.LUMINOUS:
            self._update_brightness_state(self._mox_device.get_luminous())
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        luminous = MoxDimmerEntity._ha_to_mox(kwargs.get(ATTR_BRIGHTNESS, 255))
        await self._mox_device.set_luminous(luminous, 100)
        self._update_brightness_state(luminous)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._mox_device.set_luminous(0, 100)
        self._update_brightness_state(0)

    @staticmethod
    def _mox_to_ha(brightness: int) -> int:
        """Convert brightess scaling."""
        return int(brightness * 255 / 100)

    @staticmethod
    def _ha_to_mox(brightness: int) -> int:
        """Convert brightess scaling."""
        return int(brightness / 255 * 100)
