"""Scene Router Implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    condition as condition_helper,
    config_validation as cv,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.sun import get_astral_location
from homeassistant.util import dt as dt_util
from astral.sun import SunDirection, time_at_elevation
from datetime import datetime

from .const import DOMAIN, ConditionType
from .models import SceneConfig, SceneRouterConfig

_LOGGER = logging.getLogger(__name__)


class SceneRouter:
    """Scene Router for managing scenes in Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the SceneRouter."""
        self.hass = hass
        self.config_entry = config_entry
        self.scene_router_config: SceneRouterConfig = SceneRouterConfig.from_dict(
            config_entry.options
        )
        self.condition_entities: dict[str, dict[ConditionType, Entity]] = {}

        dr.async_get(hass).async_get_or_create(
            config_entry_id=config_entry.entry_id,
            **self.device_info,
        )

        _LOGGER.debug(
            "SceneRouter initialized for router '%s'", self.scene_router_config.name
        )

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return the device information for this scene router."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self.scene_router_config.name,
        )

    @property
    async def selected_scene_entity_id(self) -> str | None:
        """Return the currently selected scene entity ID."""
        entity_id, _ = await self.selected_scene
        if not entity_id:
            _LOGGER.warning(
                "SceneRouter '%s' has no selected scene", self.scene_router_config.name
            )
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'",
            self.scene_router_config.name,
            entity_id,
        )
        return entity_id

    @property
    async def selected_scene_friendly_name(self) -> str | None:
        """Return the currently selected scene friendly name."""
        _, friendly_name = await self.selected_scene
        if not friendly_name:
            _LOGGER.warning(
                "SceneRouter '%s' has no selected scene", self.scene_router_config.name
            )
            return None
        _LOGGER.debug(
            "SceneRouter '%s' selected scene: '%s'",
            self.scene_router_config.name,
            friendly_name,
        )
        return friendly_name

    async def _evaluate_custom(self, cfg: dict[str, Any]) -> bool:
        """Compile & evaluate a Home Assistant custom condition dict asynchronously."""
        _LOGGER.debug(
            "Evaluating custom condition: %s for scene: %s",
            cfg,
            self.scene_router_config.name,
        )
        _LOGGER.debug(
            "cfg type: %s, cfg: %s",
            type(cfg),
            cfg,
        )
        cfg = cv.CONDITION_SCHEMA(cfg)
        config = await condition_helper.async_validate_condition_config(self.hass, cfg)
        test = await condition_helper.async_from_config(self.hass, config)
        result = test(self.hass, {})
        if asyncio.iscoroutine(result):
            result = await result
        _LOGGER.debug(
            "Custom condition result for scene '%s': %s",
            self.scene_router_config.name,
            result,
        )
        return bool(result)

    @property
    async def selected_scene(self) -> tuple[str, str] | None:
        """Asynchronously select the best scene based on required, forcing, and builtin conditions."""
        raw_candidates: list[tuple[SceneConfig, int, bool, datetime]] = []

        for cfg in self.scene_router_config.scene_configs:
            # 1) required_custom_conditions
            if cfg.required_custom_conditions:
                results = await asyncio.gather(
                    *(
                        self._evaluate_custom(cond)
                        for cond in cfg.required_custom_conditions
                    )
                )
                if not all(results):
                    continue

            # 2) forcing_custom_conditions
            if cfg.forcing_custom_conditions:
                results = await asyncio.gather(
                    *(
                        self._evaluate_custom(cond)
                        for cond in cfg.forcing_custom_conditions
                    )
                )
                forced = any(results)
            else:
                forced = False

            # Builtin conditions match count
            matched = 0
            times: list[datetime] = []
            now_dt = dt_util.now()

            for condition in cfg.conditions:
                ent = self.condition_entities.get(cfg.scene, {}).get(condition)
                if not ent or ent.state in (None, ""):
                    continue

                # SUN_ABOVE / SUN_BELOW
                if condition in (ConditionType.SUN_ABOVE, ConditionType.SUN_BELOW):
                    try:
                        threshold = float(ent.state)
                    except (ValueError, TypeError):
                        continue

                    try:
                        location, _ = get_astral_location(self.hass)
                        direction = (
                            SunDirection.RISING
                            if condition == ConditionType.SUN_ABOVE
                            else SunDirection.SETTING
                        )
                        ev_time = time_at_elevation(
                            location.observer,
                            threshold,
                            date=now_dt.date(),
                            direction=direction,
                            tzinfo=now_dt.tzinfo,
                        )
                    except Exception:  # pragma: no cover - astronomic calc may fail
                        continue

                    if now_dt >= ev_time:
                        matched += 1
                        times.append(ev_time)

                # TIME_AFTER / TIME_BEFORE
                if condition in (ConditionType.TIME_AFTER, ConditionType.TIME_BEFORE):
                    thresh = dt_util.parse_time(ent.state)
                    if not thresh:
                        continue
                    now_time = now_dt.time()
                    cond_dt = datetime.combine(now_dt.date(), thresh, tzinfo=now_dt.tzinfo)
                    if condition == ConditionType.TIME_AFTER and now_time >= thresh:
                        matched += 1
                        times.append(cond_dt)
                    if condition == ConditionType.TIME_BEFORE and now_time < thresh:
                        matched += 1
                        times.append(dt_util.start_of_local_day())

            last_time = max(times) if times else dt_util.start_of_local_day()
            raw_candidates.append((cfg, matched, forced, last_time))

        if not raw_candidates:
            return None

        # If any forced scenes exist, only consider those
        forced_list = [item for item in raw_candidates if item[2]]
        candidates = forced_list if forced_list else raw_candidates

        # Pick the scene with the highest matched count and latest trigger time
        max_matched = max(item[1] for item in candidates)
        best_cfg, _, _, _ = max(
            [item for item in candidates if item[1] == max_matched],
            key=lambda x: x[3],
        )

        state = self.hass.states.get(best_cfg.scene)
        entity_id = best_cfg.scene
        friendly = (
            state.attributes.get("friendly_name")
            if state and state.attributes.get("friendly_name")
            else entity_id
        )
        return entity_id, friendly
