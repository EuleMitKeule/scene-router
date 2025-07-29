"""Scene Router integration for Home Assistant."""

import copy
from functools import partial
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store

from .const import (
    CONF_CONDITION,
    CONF_FORCING_CUSTOM_CONDITIONS,
    CONF_REQUIRED_CUSTOM_CONDITIONS,
    CONF_SCENE_CONFIGS,
    DATA_COORDINATORS,
    DATA_SCENE_ROUTERS,
    DATA_STORE,
    DOMAIN,
    SIGNAL_ENTRY_UPDATED,
)
from .coordinator import SceneRouterCoordinator
from .entity import _on_entry_updated
from .scene_router import SceneRouter

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [
    Platform.NUMBER,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.TIME,
]
_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""

    _LOGGER.debug(
        "Setting up Scene Router integration from config entry: %s", config_entry
    )
    _LOGGER.debug("Config entry data: %s", config_entry.data)
    _LOGGER.debug("Config entry options: %s", config_entry.options)

    hass.data.setdefault(DOMAIN, {})
    store = Store(hass, key=DOMAIN, version=STORAGE_VERSION)
    data: dict[str, Any] = await store.async_load()
    if data is None:
        _LOGGER.debug("No stored data found, initializing empty data")
        data = {}
        await store.async_save(data)
    hass.data[DOMAIN][DATA_STORE] = store

    data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    scene_routers: dict[str, SceneRouter] = data.setdefault(DATA_SCENE_ROUTERS, {})
    coordinators: dict[str, SceneRouterCoordinator] = data.setdefault(
        DATA_COORDINATORS, {}
    )

    scene_router = SceneRouter(hass, config_entry)
    scene_routers[config_entry.entry_id] = scene_router

    coordinator = SceneRouterCoordinator(
        hass,
        config_entry,
        scene_router,
    )
    coordinators[config_entry.entry_id] = coordinator

    async_dispatcher_connect(
        hass,
        f"{DOMAIN}_{config_entry.entry_id}_{SIGNAL_ENTRY_UPDATED}",
        partial(
            _on_entry_updated,
            hass,
            config_entry,
            scene_router,
        ),
    )

    await hass.config_entries.async_forward_entry_setups(
        config_entry,
        [
            platform
            for platform in PLATFORMS
            if platform not in [Platform.SENSOR, Platform.SCENE]
        ],
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry,
        [
            platform
            for platform in PLATFORMS
            if platform in [Platform.SENSOR, Platform.SCENE]
        ],
    )

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await coordinator.async_config_entry_first_refresh()

    return True


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Updating Scene Router config entry %s", config_entry.entry_id)

    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle config entry unload."""
    _LOGGER.debug("Unloading Scene Router config entry %s", config_entry.entry_id)

    data: dict[str, Any] = hass.data[DOMAIN]
    scene_routers: dict[str, SceneRouter] = data[DATA_SCENE_ROUTERS]
    coordinators: dict[str, SceneRouterCoordinator] = data[DATA_COORDINATORS]

    if config_entry.entry_id not in scene_routers:
        _LOGGER.warning(
            "Config entry %s not found in scene routers, cannot unload",
            config_entry.entry_id,
        )
        return False

    scene_routers.pop(config_entry.entry_id)
    coordinators.pop(config_entry.entry_id)
    if not scene_routers:
        _LOGGER.debug("No more SceneRouter instances, clearing hass.data[%s]", DOMAIN)
        hass.data.pop(DOMAIN, None)

    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    return True


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle config entry removal."""


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to new format."""
    _LOGGER.debug("Migrating Scene Router config entry %s", config_entry.entry_id)

    if config_entry.version == 1:
        _LOGGER.debug(
            "Migrating Scene Router config entry %s from v1 to v2",
            config_entry.entry_id,
        )

        options = copy.deepcopy(dict(config_entry.options))
        scene_configs: list[dict[str, Any]] = options[CONF_SCENE_CONFIGS]
        for scene_config in scene_configs:
            conditions = scene_config.pop("conditions", [])
            if not conditions:
                raise ValueError(
                    f"Scene config {scene_config} in entry {config_entry.entry_id} has no conditions"
                )

            if len(conditions) > 1:
                _LOGGER.warning(
                    "Scene config %s in entry %s has multiple conditions, only the first one will be used",
                    scene_config,
                    config_entry.entry_id,
                )

            scene_config[CONF_CONDITION] = conditions[0]
            scene_config[CONF_FORCING_CUSTOM_CONDITIONS] = scene_config.pop(
                "forcing_custom_condition", None
            )
            scene_config[CONF_REQUIRED_CUSTOM_CONDITIONS] = scene_config.pop(
                "required_custom_condition", None
            )

        hass.config_entries.async_update_entry(
            config_entry, data=config_entry.data, options=options, version=2
        )

    return True
