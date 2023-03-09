"""The Mox integration."""
from __future__ import annotations

import asyncio
import logging

from aiomox.mox_client import MoxClient

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.LIGHT,
    # Platform.COVER,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Init the connection to MOX Gateway."""
    client = MoxClient()
    await client.connect(asyncio.get_running_loop().create_future())
    hass.data[DOMAIN] = {"MoxClient": client}

    for platform in PLATFORMS:
        if (discovery_info := config[DOMAIN].get(platform)) is not None:
            hass.async_create_task(
                discovery.async_load_platform(
                    hass, platform, DOMAIN, discovery_info, config
                )
            )

    # Return boolean to indicate that initialization was successful.
    return True
