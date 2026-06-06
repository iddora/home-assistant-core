"""Tests for the mox light platform."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiomox.device.dimmer import StateType as DST
from aiomox.device.switch import StateType as SST
import pytest

from homeassistant.components.light import ColorMode
from homeassistant.components.mox.light import MoxDimmerEntity, MoxLightEntity
from homeassistant.core import HomeAssistant

from tests.common import MockEntityPlatform


@pytest.fixture
def mock_mox_client() -> MagicMock:
    """Return a mock mox client."""
    return MagicMock()


async def test_light_reports_onoff_color_mode_when_on(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test switch light reports onoff color mode when on."""
    mock_switch = MagicMock()
    mock_switch.is_on.return_value = True
    mock_switch.turn_on = AsyncMock()
    mock_switch.turn_off = AsyncMock()

    with patch(
        "homeassistant.components.mox.light.MoxSwitch", return_value=mock_switch
    ):
        entity = MoxLightEntity("kitchen", 0x123, "Kitchen Light", mock_mox_client)

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity.async_turn_on()

    entity._async_calculate_state()
    assert entity.color_mode == ColorMode.ONOFF
    assert entity.supported_color_modes == {ColorMode.ONOFF}
    assert entity.is_on


async def test_light_clears_color_mode_when_off(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test switch light clears color mode when off."""
    mock_switch = MagicMock()
    mock_switch.is_on.return_value = False
    mock_switch.turn_off = AsyncMock()

    with patch(
        "homeassistant.components.mox.light.MoxSwitch", return_value=mock_switch
    ):
        entity = MoxLightEntity("kitchen", 0x123, "Kitchen Light", mock_mox_client)
        entity._attr_is_on = True
        entity._attr_color_mode = ColorMode.ONOFF

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity.async_turn_off()

    entity._async_calculate_state()
    assert entity.color_mode is None
    assert not entity.is_on


async def test_dimmer_reports_brightness_color_mode_when_on(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test dimmer reports brightness color mode when on."""
    mock_dimmer = MagicMock()
    mock_dimmer.get_luminous.return_value = 50
    mock_dimmer.set_luminous = AsyncMock()

    with patch(
        "homeassistant.components.mox.light.MoxDimmer", return_value=mock_dimmer
    ):
        entity = MoxDimmerEntity("kitchen", 0x456, "Kitchen Dimmer", mock_mox_client)

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity.async_turn_on(brightness=128)

    entity._async_calculate_state()
    assert entity.color_mode == ColorMode.BRIGHTNESS
    assert entity.supported_color_modes == {ColorMode.BRIGHTNESS}
    assert entity.is_on
    assert entity.brightness == 127
    mock_dimmer.set_luminous.assert_awaited_once_with(50, 100)


async def test_dimmer_clears_color_mode_when_off(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test dimmer clears color mode when off."""
    mock_dimmer = MagicMock()
    mock_dimmer.get_luminous.return_value = 0
    mock_dimmer.set_luminous = AsyncMock()

    with patch(
        "homeassistant.components.mox.light.MoxDimmer", return_value=mock_dimmer
    ):
        entity = MoxDimmerEntity("kitchen", 0x456, "Kitchen Dimmer", mock_mox_client)
        entity._update_brightness_state(50)

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity.async_turn_off()

    entity._async_calculate_state()
    assert entity.color_mode is None
    assert not entity.is_on
    mock_dimmer.set_luminous.assert_awaited_once_with(0, 100)


async def test_dimmer_callback_updates_color_mode(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test dimmer callback updates color mode from device state."""
    mock_dimmer = MagicMock()
    mock_dimmer.get_luminous.return_value = 75

    with patch(
        "homeassistant.components.mox.light.MoxDimmer", return_value=mock_dimmer
    ):
        entity = MoxDimmerEntity("kitchen", 0x456, "Kitchen Dimmer", mock_mox_client)

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity._callback(mock_dimmer, DST.LUMINOUS)
    await hass.async_block_till_done()

    assert entity.color_mode == ColorMode.BRIGHTNESS
    assert entity.brightness == 191


async def test_light_callback_updates_color_mode(
    hass: HomeAssistant, mock_mox_client: MagicMock
) -> None:
    """Test switch light callback updates color mode from device state."""
    mock_switch = MagicMock()
    mock_switch.is_on.return_value = True

    with patch(
        "homeassistant.components.mox.light.MoxSwitch", return_value=mock_switch
    ):
        entity = MoxLightEntity("kitchen", 0x123, "Kitchen Light", mock_mox_client)

    platform = MockEntityPlatform(hass, domain="light", platform_name="mox")
    await platform.async_add_entities([entity])

    await entity._callback(mock_switch, SST.ON_OFF)
    await hass.async_block_till_done()

    assert entity.color_mode == ColorMode.ONOFF
