"""Time platform for Scene Router integration."""

from dataclasses import dataclass
from datetime import time
import logging
from typing import Any

from homeassistant.components.time import (
    DOMAIN as TIME_DOMAIN,
    TimeEntity,
    TimeEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store

from .const import (
    DATA_COORDINATORS,
    DATA_SCENE_ROUTERS,
    DATA_STORE,
    DOMAIN,
    ConditionType,
)
from .coordinator import SceneRouterCoordinator
from .entity import (
    SceneRouterConditionEntity,
    SceneRouterConditionEntityDescription,
    _get_entity_key,
    _get_translation_key,
)
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SceneRouterTimeEntityDescription(
    SceneRouterConditionEntityDescription, TimeEntityDescription
):
    """Time entity description for Scene Router integration."""

    domain: str = TIME_DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up time platform for Scene Router integration."""
    _LOGGER.debug("Setting up time platform for Scene Router integration")

    data: dict[str, Any] = hass.data[DOMAIN]
    scene_router: SceneRouter = data[DATA_SCENE_ROUTERS][config_entry.entry_id]
    coordinator: SceneRouterCoordinator = data[DATA_COORDINATORS][config_entry.entry_id]
    store: Store = data.get(DATA_STORE)
    entity_descriptions: list[TimeEntityDescription] = []

    for scene_config in scene_router.scene_router_config.scene_configs:
        if not (scene := er.async_get(hass).async_get(scene_config.scene)):
            _LOGGER.warning(
                "Scene '%s' not found in entity registry, skipping conditions",
                scene_config.scene,
            )
            continue

        for condition in scene_config.conditions:
            if condition not in [
                ConditionType.TIME_AFTER,
                ConditionType.TIME_BEFORE,
            ]:
                continue

            entity_description = SceneRouterTimeEntityDescription(
                key=_get_entity_key(
                    scene_router.scene_router_config.name,
                    scene_config.scene,
                    condition,
                ),
                translation_key=_get_translation_key(condition),
                translation_placeholders={
                    "scene": scene.name or scene.original_name or scene_config.scene,
                },
                entity_category=EntityCategory.CONFIG,
                condition_type=condition,
                scene_entity_id=scene_config.scene,
            )
            entity_descriptions.append(entity_description)

    async_add_entities(
        SceneRouterTimeEntity(
            store,
            config_entry,
            scene_router,
            coordinator,
            entity_description,
        )
        for entity_description in entity_descriptions
    )


class SceneRouterTimeEntity(SceneRouterConditionEntity, TimeEntity, RestoreEntity):
    """Time entity for Scene Router integration."""

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added to hass."""
        await super().async_added_to_hass()

        data: dict[str, Any] = await self.store.async_load()
        self._attr_native_value = time.fromisoformat(
            data.get(self.entity_description.key, time().isoformat())
        )

    async def async_set_value(self, value: time) -> None:
        """Change the time."""
        _LOGGER.debug(
            "Setting time for SceneRouter '%s' to '%s'",
            self.scene_router.scene_router_config.name,
            value,
        )

        data: dict[str, Any] = await self.store.async_load()
        data[self.entity_description.key] = value.isoformat()
        await self.store.async_save(data)
        self._attr_native_value = value

        await self.coordinator.async_request_refresh()
