"""Sensor platform for Scene Router integration."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    EntityCategory,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DATA_SCENE_ROUTERS, DOMAIN
from .coordinator import SceneRouterCoordinator
from .entity import SceneRouterEntity, SceneRouterEntityDescription
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SceneRouterSensorEntityDescription(
    SceneRouterEntityDescription, SensorEntityDescription
):
    """Class describing Scene Router sensor entities."""

    value_func: Callable[[tuple[str, str]], str]


ENTITY_DESCRIPTIONS = [
    SceneRouterSensorEntityDescription(
        key="selected_scene",
        translation_key="selected_scene",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_func=lambda selected_scene: selected_scene[1],
    ),
    SceneRouterSensorEntityDescription(
        key="selected_scene_entity_id",
        translation_key="selected_scene_entity_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_func=lambda selected_scene: selected_scene[0],
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform for Scene Router integration."""
    data: dict[str, Any] = hass.data[DOMAIN]
    scene_routers: dict[str, SceneRouter] = data[DATA_SCENE_ROUTERS]
    coordinators: dict[str, SceneRouterCoordinator] = data[DATA_COORDINATORS]

    scene_router = scene_routers[config_entry.entry_id]
    coordinator = coordinators[config_entry.entry_id]

    async_add_entities(
        SceneRouterSensorEntity(
            config_entry, scene_router, coordinator, entity_description
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SceneRouterSensorEntity(SceneRouterEntity, SensorEntity):
    """Sensor entity for Scene Router integration."""

    entity_description: SceneRouterSensorEntityDescription
    _value: str | None = None

    def _handle_coordinator_update(self) -> None:
        """Handle updates from the coordinator."""
        super()._handle_coordinator_update()

        if not self.coordinator.data:
            return

        self._value = self.entity_description.value_func(self.coordinator.data)
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""

        return self._value
