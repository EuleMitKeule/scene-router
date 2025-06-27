"""Scene platform for Scene Router integration."""

from __future__ import annotations

import logging

from config.custom_components.scene_router.entity import SceneRouterEntity
from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN, Scene as SceneEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_SCENE_ROUTERS, DOMAIN
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up scene platform for Scene Router integration."""
    scene_routers: list[SceneRouter] = hass.data.get(DOMAIN, {}).get(
        DATA_SCENE_ROUTERS, []
    )

    if not scene_routers:
        _LOGGER.debug(
            "No SceneRouter instances found in hass.data, skipping scene platform"
        )
        return

    async_add_entities(
        [
            SceneRouterSceneEntity(
                config_entry,
                router,
                EntityDescription(
                    key="scene",
                    translation_key="scene",
                ),
            )
            for router in scene_routers
        ]
    )


class SceneRouterSceneEntity(SceneRouterEntity, SceneEntity):
    """Scene entity for Scene Router integration."""

    _attr_name = None

    async def async_activate(self) -> None:
        """Activate scene."""
        target = self.router.selected_scene()

        if not target:
            _LOGGER.warning("SceneRouter '%s' returned no scene", self.entity_id)
            return

        _LOGGER.debug(
            "SceneRouter '%s' activating target scene '%s'",
            self.entity_id,
            target,
        )

        await self.hass.services.async_call(
            SCENE_DOMAIN,
            "turn_on",
            {CONF_ENTITY_ID: target},
            blocking=True,
        )
