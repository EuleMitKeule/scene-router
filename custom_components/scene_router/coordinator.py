"""Coordinator for Scene Router integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_UPDATE_INTERVAL_SECONDS
from .scene_router import SceneRouter

_LOGGER = logging.getLogger(__name__)


class SceneRouterCoordinator(DataUpdateCoordinator[tuple[str, str] | None]):
    """Coordinator for Scene Router integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        scene_router: SceneRouter,
    ) -> None:
        """Initialize the SceneRouterCoordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=scene_router.scene_router_config.name,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )

        self.scene_router = scene_router

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        _LOGGER.debug(
            "Setting up SceneRouterCoordinator for router '%s'",
            self.scene_router.scene_router_config.name,
        )
        await self._async_update_data()

    async def async_shutdown(self):
        """Shutdown the coordinator."""
        return await super().async_shutdown()

    async def _async_update_data(self) -> tuple[str, str] | None:
        """Fetch data from the SceneRouter."""
        _LOGGER.debug(
            "Updating data for SceneRouterCoordinator '%s'",
            self.scene_router.scene_router_config.name,
        )
        selected_scene = await self.scene_router.selected_scene
        self.data = selected_scene
        return selected_scene
