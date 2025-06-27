"""Scene Router Implementation."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .models import SceneRouterConfig

_LOGGER = logging.getLogger(__name__)


class SceneRouter:
    """Scene Router for managing scenes in Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        config: SceneRouterConfig,
    ) -> None:
        """Initialize the SceneRouter."""
        self.hass = hass
        self.config = config

        if config.enable_device:
            dr.async_get(hass).async_get_or_create(
                config_entry_id=config_entry.entry_id,
                **self.device_info,
            )

        _LOGGER.debug("SceneRouter initialized for router '%s'", config.name)

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return the device information for this scene router."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.config.name)},
            name=self.config.name,
        )

    @property
    def selected_scene_entity_id(self) -> str | None:
        """Return the currently selected scene entity ID."""
        entity_id, _ = self.selected_scene()
        if not entity_id:
            _LOGGER.warning("SceneRouter '%s' has no selected scene", self.config.name)
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'", self.config.name, entity_id
        )
        return entity_id

    @property
    def selected_scene_friendly_name(self) -> str | None:
        """Return the currently selected scene friendly name."""
        _, friendly_name = self.selected_scene()
        if not friendly_name:
            _LOGGER.warning("SceneRouter '%s' has no selected scene", self.config.name)
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'", self.config.name, friendly_name
        )
        return friendly_name

    @property
    def selected_scene(self) -> tuple[str, str] | None:
        """Return the currently selected scene."""
        if not self.config.scenes:
            _LOGGER.warning(
                "No scenes configured for scene router '%s'", self.config.name
            )
            return None

        # TODO: Implement logic to select the scene

        first_scene = self.config.scenes[0].scene
        _LOGGER.debug(
            "SceneRouter '%s' select_scene -> '%s'",
            self.config.name,
            first_scene,
        )

        scene = self.hass.states.get(first_scene)

        if not scene:
            _LOGGER.warning(
                "Scene '%s' not found in Home Assistant",
                first_scene,
            )
            return None

        entity_id = scene.entity_id
        friendly_name = scene.attributes.get("friendly_name", first_scene) or entity_id

        _LOGGER.debug(
            "SceneRouter '%s' found scene '%s' with entity_id '%s'",
            self.config.name,
            friendly_name,
            entity_id,
        )

        return entity_id, friendly_name
