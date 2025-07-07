"""Scene platform for Scene Router integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN, Scene as SceneEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DATA_SCENE_ROUTERS, DOMAIN
from .coordinator import SceneRouterCoordinator
from .entity import SceneRouterEntity, SceneRouterEntityDescription
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up scene platform for Scene Router integration."""
    data: dict[str, Any] = hass.data[DOMAIN]
    scene_routers: dict[str, SceneRouter] = data[DATA_SCENE_ROUTERS]
    coordinators: dict[str, SceneRouterCoordinator] = data[DATA_COORDINATORS]

    scene_router = scene_routers[config_entry.entry_id]
    coordinator = coordinators[config_entry.entry_id]

    async_add_entities(
        [
            SceneRouterSceneEntity(
                config_entry,
                scene_router,
                coordinator,
                SceneRouterEntityDescription(
                    key="scene",
                    translation_key="scene",
                ),
            )
        ]
    )


class SceneRouterSceneEntity(SceneRouterEntity, SceneEntity):
    """Scene entity for Scene Router integration."""

    _attr_name = None

    async def async_activate(self) -> None:
        """Activate scene."""
        target, _ = await self.scene_router.selected_scene

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

    def _handle_coordinator_update(self) -> None:
        if self.scene_router.scene_router_config.enable_auto_change:
            if any(
                self.hass.states.get(light_entity_id).state == "on"
                for light_entity_id in self.scene_router.scene_router_config.light_entities
            ):
                _LOGGER.debug(
                    "SceneRouter '%s' auto changing scene due to light state",
                    self.entity_id,
                )
                self.hass.async_create_task(self.async_activate())

        return super()._handle_coordinator_update()
