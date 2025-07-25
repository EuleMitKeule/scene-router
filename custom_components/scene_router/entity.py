"""Base entity for Scene Router integration."""

from dataclasses import dataclass
import logging

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.time import DOMAIN as TIME_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ConditionType
from .coordinator import SceneRouterCoordinator
from .models import SceneRouterConfig
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)

CONDITION_TO_DOMAIN = {
    ConditionType.SUN_BELOW: NUMBER_DOMAIN,
    ConditionType.TIME_AFTER: TIME_DOMAIN,
}


@dataclass(frozen=True, kw_only=True)
class SceneRouterEntityDescription(EntityDescription):
    """Base class for Scene Router entity descriptions."""


@dataclass(frozen=True, kw_only=True)
class SceneRouterConditionEntityDescription(SceneRouterEntityDescription):
    """Base class for Scene Router condition entity descriptions."""

    domain: str
    scene_entity_id: str
    condition_type: ConditionType


def _get_entity_key(
    scene_router_name: str,
    scene_entity_id: str,
    condition: ConditionType,
) -> str:
    """Generate a unique key for the number entity based on scene and condition."""
    match condition:
        case ConditionType.SUN_BELOW:
            return f"{scene_router_name}_{scene_entity_id.split('.')[1]}_sun_below"
        case ConditionType.TIME_AFTER:
            return f"{scene_router_name}_{scene_entity_id.split('.')[1]}_time_after"
        case _:
            raise ValueError(f"Unsupported condition type: {condition}")


def _get_translation_key(condition: ConditionType) -> str:
    """Get the translation key for the condition."""
    match condition:
        case ConditionType.SUN_BELOW:
            return "sun_below"
        case ConditionType.TIME_AFTER:
            return "time_after"
        case _:
            raise ValueError(f"Unsupported condition type: {condition}")


def _get_entity_id(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    domain: str,
    scene_router_name: str,
    scene_entity_id: str,
    condition: ConditionType,
) -> str:
    """Generate a unique entity ID for the entity."""
    entity_registry = er.async_get(hass)
    return entity_registry.async_get_entity_id(
        domain,
        DOMAIN,
        _get_unique_id(config_entry, scene_router_name, scene_entity_id, condition),
    )


def _get_unique_id(
    config_entry: ConfigEntry,
    scene_router_name: str,
    scene_entity_id: str,
    condition: ConditionType,
) -> str:
    """Generate a unique ID for the entity."""
    return f"{config_entry.entry_id}{f'_{_get_entity_key(scene_router_name, scene_entity_id, condition)}'}"


def _get_unique_id_from_description(
    config_entry: ConfigEntry,
    entity_description: SceneRouterEntityDescription,
) -> str:
    """Generate a unique ID for the entity based on the config entry and description."""
    return f"{config_entry.entry_id}_{entity_description.key}"


async def _on_entry_updated(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    scene_router: SceneRouter,
    previous_scene_router_config: SceneRouterConfig,
    new_scene_router_config: SceneRouterConfig,
) -> None:
    """Handle updates to the scene router configuration."""
    for previous_scene_config in previous_scene_router_config.scene_configs:
        new_scene_config = next(
            scene_config
            for scene_config in new_scene_router_config.scene_configs
            if scene_config.scene == previous_scene_config.scene
        )
        if previous_scene_config.condition != new_scene_config.condition:
            entity_id = _get_entity_id(
                hass,
                config_entry,
                CONDITION_TO_DOMAIN[previous_scene_config.condition],
                scene_router.scene_router_config.name,
                previous_scene_config.scene,
                previous_scene_config.condition,
            )

            _LOGGER.debug(
                "Removing entity '%s' for scene '%s' and condition '%s'",
                entity_id,
                previous_scene_config.scene,
                previous_scene_config.condition,
            )
            er.async_get(hass).async_remove(entity_id)

            condition_entities = scene_router.condition_entities.get(
                previous_scene_config.scene
            )
            if condition_entities:
                condition_entities.pop(previous_scene_config.condition, None)


class SceneRouterEntity(CoordinatorEntity[SceneRouterCoordinator]):
    """Base entity for Scene Router integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        scene_router: SceneRouter,
        coordinator: SceneRouterCoordinator,
        entity_description: SceneRouterEntityDescription,
    ) -> None:
        """Initialize the SceneRouterEntity."""
        super().__init__(coordinator)
        self.scene_router = scene_router
        self.config_entry = config_entry
        self.entity_description = entity_description

        self._attr_unique_id = _get_unique_id_from_description(
            config_entry, entity_description
        )
        self._attr_device_info = scene_router.device_info


class SceneRouterConditionEntity(SceneRouterEntity):
    """Base class for Scene Router condition entities."""

    def __init__(
        self,
        store: Store,
        config_entry: ConfigEntry,
        scene_router: SceneRouter,
        coordinator: SceneRouterCoordinator,
        entity_description: SceneRouterConditionEntityDescription,
    ) -> None:
        """Initialize the SceneRouterConditionEntity."""
        super().__init__(config_entry, scene_router, coordinator, entity_description)

        condition_entities = scene_router.condition_entities.setdefault(
            entity_description.scene_entity_id, {}
        )
        condition_entities[entity_description.condition_type] = self

        self.store = store
