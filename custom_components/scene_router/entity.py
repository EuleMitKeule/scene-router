"""Base entity for Scene Router integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity, EntityDescription

from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


class SceneRouterEntity(Entity):
    """Base entity for Scene Router integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        router: SceneRouter,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize the SceneRouterEntity."""
        self.router = router
        self.config_entry = config_entry
        self.entity_description = entity_description

        self._attr_unique_id = f"{config_entry.entry_id}{f'_{entity_description.key}' if entity_description.key else ''}"

        if router.config.enable_device:
            self._attr_device_info = router.device_info

        _LOGGER.debug("Registered SceneRouterEntity '%s'", self.entity_id)
