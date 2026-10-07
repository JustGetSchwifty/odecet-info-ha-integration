"""Odecet.info integration setup."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.odecet_info.const import CONF_MEDIUMS, DOMAIN, PLATFORMS
from custom_components.odecet_info.coordinator import OdecetCoordinator
from custom_components.odecet_info.entry import OdecetConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: OdecetConfigEntry) -> bool:
    """Log in once, then expose the meters."""
    coordinator = OdecetCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # The account device has to exist before meter devices reference it.
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="odecet.info",
        model="Account",
        configuration_url="https://odecet.info/",
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OdecetConfigEntry) -> bool:
    """Remove platforms. The dedicated session closes with the entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: OdecetConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Allow deleting a meter that the latest successful fetch did not return."""
    del hass
    data = config_entry.runtime_data.data
    if data is None:
        return False
    enabled = set(config_entry.options.get(CONF_MEDIUMS, []))
    current = {
        f"{config_entry.entry_id}_{meter.medium.value}_{meter.serial}"
        for meter in data.meters()
        if meter.medium.value in enabled
    }
    identifiers = {ident for domain, ident in device_entry.identifiers if domain == DOMAIN}
    if config_entry.entry_id in identifiers:
        return False
    return bool(identifiers) and identifiers.isdisjoint(current)


async def _async_reload(hass: HomeAssistant, entry: OdecetConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
