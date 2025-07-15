"""Scene platform for Scene Router integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN, Scene as SceneEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, SERVICE_TURN_ON, STATE_ON
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
    scene_router: SceneRouter = data[DATA_SCENE_ROUTERS][config_entry.entry_id]
    coordinator: SceneRouterCoordinator = data[DATA_COORDINATORS][config_entry.entry_id]

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
        if not (target := await self.scene_router.selected_scene_entity_id):
            _LOGGER.warning("SceneRouter '%s' returned no scene", self.entity_id)
            return

        await self.hass.services.async_call(
            SCENE_DOMAIN,
            SERVICE_TURN_ON,
            {CONF_ENTITY_ID: target},
            blocking=True,
        )

    def _handle_coordinator_update(self) -> None:
        if self.scene_router.scene_router_config.enable_auto_change:
            if any(
                (state := self.hass.states.get(light_entity_id))
                and state.state == STATE_ON
                for light_entity_id in self.scene_router.scene_router_config.light_entities
            ):
                _LOGGER.debug(
                    "SceneRouter '%s' auto changing scene due to light state",
                    self.entity_id,
                )
                self.hass.async_create_task(self.async_activate())

        return super()._handle_coordinator_update()
