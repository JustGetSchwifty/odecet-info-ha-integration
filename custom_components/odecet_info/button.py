"""Manual sync. The button stays unavailable during the one-minute cooldown."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.odecet_info.const import DOMAIN
from custom_components.odecet_info.coordinator import OdecetCoordinator
from custom_components.odecet_info.entry import OdecetConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OdecetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the account-level sync button."""
    async_add_entities([SyncNowButton(entry.runtime_data)])


class SyncNowButton(CoordinatorEntity[OdecetCoordinator], ButtonEntity):
    """Ask for a sync now, unless the last attempt was less than a minute ago."""

    _attr_has_entity_name = True
    _attr_translation_key = "sync_now"

    def __init__(self, coordinator: OdecetCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_sync_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="odecet.info",
            model="Account",
            configuration_url="https://odecet.info/",
        )

    @property
    def available(self) -> bool:
        """Unavailable while the shared cooldown is running."""
        return self.coordinator.manual_sync_allowed

    @property
    def extra_state_attributes(self) -> dict[str, int]:
        return {"cooldown_seconds": self.coordinator.cooldown_seconds}

    async def async_press(self) -> None:
        if not self.coordinator.manual_sync_allowed:
            remaining = self.coordinator.cooldown_seconds
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="sync_cooldown",
                translation_placeholders={"seconds": str(remaining)},
            )
        await self.coordinator.async_request_refresh()
