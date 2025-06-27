"""Sensor platform for Scene Router integration."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from config.custom_components.scene_router.entity import SceneRouterEntity
from homeassistant.components.sensor import (
    EntityCategory,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_SCENE_ROUTERS, DOMAIN
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SceneRouterSensorEntityDescription(SensorEntityDescription):
    """Class describing Scene Router sensor entities."""

    value_func: Callable[[SceneRouter], Any]


ENTITY_DESCRIPTIONS = [
    SceneRouterSensorEntityDescription(
        key="selected_scene",
        translation_key="selected_scene",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_func=lambda router: router.selected_scene_friendly_name,
    ),
    SceneRouterSensorEntityDescription(
        key="selected_scene_entity_id",
        translation_key="selected_scene_entity_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_func=lambda router: router.selected_scene_entity_id,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform for Scene Router integration."""

    scene_routers: list[SceneRouter] = hass.data.get(DOMAIN, {}).get(
        DATA_SCENE_ROUTERS, []
    )

    if not scene_routers:
        _LOGGER.debug(
            "No SceneRouter instances found in hass.data, skipping scene platform"
        )
        return

    async_add_entities(
        SceneRouterSensorEntity(config_entry, scene_router, entity_description)
        for scene_router in scene_routers
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SceneRouterSensorEntity(SceneRouterEntity, SensorEntity):
    """Sensor entity for Scene Router integration."""

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""

        return self.entity_description.value_func(self.router)
