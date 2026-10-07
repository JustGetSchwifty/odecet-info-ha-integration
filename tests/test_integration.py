"""Sensors, the cooldown, statistics import, and diagnostics."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.odecet_info import async_remove_config_entry_device
from custom_components.odecet_info.button import SyncNowButton
from custom_components.odecet_info.const import DOMAIN
from custom_components.odecet_info.coordinator import OdecetCoordinator
from custom_components.odecet_info.diagnostics import async_get_config_entry_diagnostics
from custom_components.odecet_info.errors import OdecetAuthError, OdecetTransportError
from custom_components.odecet_info.sensor import MeterSensor
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from tests.samples import sample_readings


def _entry(**options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="user@example.com",
        unique_id="user@example.com",
        data={
            "username": "user@example.com",
            "password": "secret-value",
            "signin_url": "https://odecet.info/signin",
        },
        options={
            "mediums": options.get("mediums", ["cold_water", "heat"]),
            "fetch_method": options.get("fetch_method", "auto"),
        },
    )


def _patch_fetch(readings):
    client = MagicMock()
    client.async_fetch = AsyncMock(return_value=readings)
    return patch(
        "custom_components.odecet_info.coordinator.OdecetClient",
        return_value=client,
    )


@pytest.mark.asyncio
async def test_sensors_statistics_and_disabled_medium(hass, enable_custom_integrations) -> None:
    entry = _entry(mediums=["cold_water"])
    entry.add_to_hass(hass)
    with (
        _patch_fetch(sample_readings()),
        patch("custom_components.odecet_info.sensor.async_import_statistics") as imported,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    states = {state.entity_id: state for state in hass.states.async_all()}
    readings = [state for state in states.values() if state.entity_id.endswith("_reading")]
    assert len(readings) == 1
    cold = readings[0]
    assert cold.state == "12.0" or cold.state == "12"
    assert cold.attributes["unit_of_measurement"] == "m³"
    assert cold.attributes["device_class"] == "water"
    assert cold.attributes["state_class"] == "total_increasing"
    assert all("1003" not in state.entity_id for state in states.values())

    metadata = imported.call_args.args[1]
    points = imported.call_args.args[2]
    assert len(points) == 2
    assert points[0]["start"] != points[1]["start"]
    assert metadata["source"] == "recorder"
    assert metadata["statistic_id"] == cold.entity_id
    assert metadata["unit_class"] == "volume"
    assert points[-1]["sum"] == 2.0
    assert imported.call_count == 1

    countdown = next(
        state for state in states.values() if state.entity_id.endswith("next_manual_sync")
    )
    assert countdown.state not in {"unknown", "unavailable"}
    button = next(state for state in states.values() if state.entity_id.endswith("sync_now"))
    assert button.state == "unavailable"

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert "secret-value" not in str(diagnostics)
    assert diagnostics["meters"][0]["serial"] == "1001"
    assert diagnostics["meters"][0]["oldest_at"]
    assert diagnostics["meters"][0]["statistic_points"] == 2


@pytest.mark.asyncio
async def test_heat_without_a_unit_raises_a_repair(hass, enable_custom_integrations) -> None:
    entry = _entry(mediums=["heat"])
    entry.add_to_hass(hass)
    with (
        _patch_fetch(sample_readings(cold=False)),
        patch("custom_components.odecet_info.sensor.async_import_statistics") as imported,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    heat = next(state for state in hass.states.async_all() if state.entity_id.endswith("_reading"))
    assert heat.state in {"140", "140.0"}
    assert "unit_of_measurement" not in heat.attributes
    assert "device_class" not in heat.attributes
    assert "state_class" not in heat.attributes
    imported.assert_not_called()
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "missing_unit_1003")
    assert issue is not None


@pytest.mark.asyncio
async def test_manual_sync_is_rejected_during_cooldown(hass, enable_custom_integrations) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    with _patch_fetch(sample_readings()):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        button = next(state for state in hass.states.async_all() if state.domain == "button")
        assert button.state == "unavailable"
        coordinator = entry.runtime_data
        with pytest.raises(HomeAssistantError):
            await SyncNowButton(coordinator).async_press()
        coordinator._last_attempt = dt_util.utcnow() - timedelta(seconds=61)
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        await SyncNowButton(coordinator).async_press()
        await hass.async_block_till_done()
    assert coordinator.manual_sync_allowed is False


@pytest.mark.asyncio
async def test_repeated_failures_open_a_repair(hass, enable_custom_integrations) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    coordinator = OdecetCoordinator(hass, entry)
    with patch.object(
        coordinator,
        "_fetch",
        side_effect=OdecetTransportError("down"),
    ):
        for _ in range(5):
            await coordinator.async_refresh()
            assert coordinator.last_update_success is False
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "sync_failed")
    assert issue is not None
    assert issue.translation_placeholders["attempts"] == "5"


@pytest.mark.asyncio
async def test_sync_from_is_passed_to_the_client(hass, enable_custom_integrations) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "sync_from": "2026-10-06"}
    )
    with _patch_fetch(sample_readings()) as client_cls:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    sync_from = client_cls.return_value.async_fetch.await_args.args[1]
    assert sync_from.isoformat() == "2026-10-06"


@pytest.mark.asyncio
async def test_fetch_uses_a_dedicated_session(hass, enable_custom_integrations) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    with _patch_fetch(sample_readings()):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = entry.runtime_data
    assert coordinator.session is not async_get_clientsession(hass)


@pytest.mark.asyncio
async def test_a_meter_that_disappears_is_removed(hass, enable_custom_integrations) -> None:
    entry = _entry(mediums=["cold_water", "heat"])
    entry.add_to_hass(hass)
    with _patch_fetch(sample_readings()):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    registry = dr.async_get(hass)
    heat_id = f"{entry.entry_id}_heat_1003"
    assert registry.async_get_device(identifiers={(DOMAIN, heat_id)}) is not None

    with _patch_fetch(sample_readings(heat=False)):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

    assert registry.async_get_device(identifiers={(DOMAIN, heat_id)}) is None
    account = registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert account is not None
    assert await async_remove_config_entry_device(hass, entry, account) is False
    cold = registry.async_get_device(identifiers={(DOMAIN, f"{entry.entry_id}_cold_water_1001")})
    assert cold is not None
    assert await async_remove_config_entry_device(hass, entry, cold) is False
    with _patch_fetch(sample_readings(heat=False)):
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, "fetch_method": "csv"}
        )
        await hass.async_block_till_done()


@pytest.mark.asyncio
async def test_a_failed_sync_is_logged_once(hass, caplog, enable_custom_integrations) -> None:
    caplog.set_level("ERROR", logger="custom_components.odecet_info.coordinator")
    entry = _entry()
    entry.add_to_hass(hass)
    coordinator = OdecetCoordinator(hass, entry)
    with patch.object(coordinator, "_fetch", side_effect=OdecetTransportError("down")):
        await coordinator.async_refresh()
        await coordinator.async_refresh()
    errors = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(errors) == 1
    assert "odecet_info" in errors[0].message
    assert coordinator.manual_sync_allowed is False
    fresh = OdecetCoordinator(hass, entry)
    assert fresh.manual_sync_allowed is True
    assert fresh.cooldown_seconds == 0
    fresh.config_entry = None  # type: ignore[assignment]
    with pytest.raises(UpdateFailed):
        await fresh._fetch()
    with pytest.raises(ConfigEntryAuthFailed):
        with patch.object(coordinator, "_fetch", side_effect=OdecetAuthError("no")):
            await coordinator._async_update_data()
    await coordinator._handle_scheduled(dt_util.utcnow())
    meter = sample_readings().meters()[0]
    sensor = MeterSensor(coordinator, meter, "uid", None)
    coordinator.data = None
    assert sensor.available is False
    assert sensor.native_value is None
    assert sensor.native_unit_of_measurement is None
    assert sensor.device_class is None
    assert sensor.extra_state_attributes == {}
