"""Typed config entry for this integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from custom_components.odecet_info.coordinator import OdecetCoordinator

type OdecetConfigEntry = ConfigEntry[OdecetCoordinator]
