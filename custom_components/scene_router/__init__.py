"""Scene Router integration for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .models import SceneRouterConfig
from .scene_router import SceneRouter
from .validation import CONFIG_SCHEMA as _CONFIG_SCHEMA

PLATFORMS = [
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SENSOR,
]
CONFIG_SCHEMA = _CONFIG_SCHEMA
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""

    domain_config = config.get(DOMAIN)
    if not domain_config:
        _LOGGER.debug("No configuration found for %s, skipping setup", DOMAIN)
        return True

    hass.data.setdefault(DOMAIN, {})["config"] = domain_config

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    domain_config = hass.data[DOMAIN].get("config")

    if not domain_config:
        _LOGGER.error("No configuration found for %s, cannot set up entry", DOMAIN)
        return False

    scene_router_configs: list[SceneRouterConfig] = SceneRouterConfig.load_many(
        {DOMAIN: domain_config}
    )

    hass.data.setdefault(DOMAIN, {})["scene_routers"] = []

    for scene_router_config in scene_router_configs:
        _LOGGER.debug("Initializing SceneRouter for %s", scene_router_config.name)

        router = SceneRouter(hass, config_entry, scene_router_config)

        hass.data[DOMAIN]["scene_routers"].append(router)

        await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

        _LOGGER.info("SceneRouter '%s' initialized", scene_router_config.name)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle config entry unload."""
    return True


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle config entry removal."""
