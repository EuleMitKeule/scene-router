"""Number platform for Scene Router integration."""

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
class SceneRouterNumberEntityDescription(
    SceneRouterConditionEntityDescription, NumberEntityDescription
):
    """Number entity description for Scene Router integration."""

    domain: str = NUMBER_DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform for Scene Router integration."""
    _LOGGER.debug("Setting up number platform for Scene Router integration")

    data: dict[str, Any] = hass.data[DOMAIN]
    scene_routers: dict[str, SceneRouter] = data[DATA_SCENE_ROUTERS]
    coordinators: dict[str, SceneRouterCoordinator] = data[DATA_COORDINATORS]
    store: Store = data[DATA_STORE]

    scene_router = scene_routers[config_entry.entry_id]
    coordinator = coordinators[config_entry.entry_id]

    entity_descriptions: list[NumberEntityDescription] = []

    for scene_config in scene_router.scene_router_config.scene_configs:
        scene_entity_id = scene_config.scene
        scene = er.async_get(hass).async_get(scene_entity_id)
        if not scene:
            _LOGGER.warning(
                "Scene '%s' not found in entity registry, skipping conditions",
                scene_entity_id,
            )
            continue

        for condition in scene_config.conditions:
            if condition not in [
                ConditionType.SUN_ABOVE,
                ConditionType.SUN_BELOW,
            ]:
                continue

            entity_description = SceneRouterNumberEntityDescription(
                key=_get_entity_key(
                    scene_router.scene_router_config.name,
                    scene_entity_id,
                    condition,
                ),
                translation_key=_get_translation_key(condition),
                translation_placeholders={
                    "scene": scene.name or scene.original_name or scene_entity_id,
                },
                entity_category=EntityCategory.CONFIG,
                native_min_value=-90.0,
                native_max_value=90.0,
                native_step=1.0,
                native_unit_of_measurement=DEGREE,
                mode=NumberMode.BOX,
                condition_type=condition,
                scene_entity_id=scene_entity_id,
            )
            entity_descriptions.append(entity_description)

    async_add_entities(
        SceneRouterNumberEntity(
            store,
            config_entry,
            scene_router,
            coordinator,
            entity_description,
        )
        for entity_description in entity_descriptions
    )


class SceneRouterNumberEntity(SceneRouterConditionEntity, NumberEntity):
    """Number entity for Scene Router integration."""

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added to hass."""
        await super().async_added_to_hass()

        data: dict[str, Any] = await self.store.async_load()
        self._attr_native_value = data.get(self.entity_description.key, 0.0)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        _LOGGER.debug(
            "Setting number for SceneRouter '%s' to '%s'",
            self.scene_router.scene_router_config.name,
            value,
        )

        data: dict[str, Any] = await self.store.async_load()
        data[self.entity_description.key] = value
        await self.store.async_save(data)
        self._attr_native_value = value

        await self.coordinator.async_request_refresh()
