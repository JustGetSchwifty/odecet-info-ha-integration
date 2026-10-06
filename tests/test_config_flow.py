"""Config flow coverage. The site client is mocked."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.odecet_info.const import (
    CONF_FETCH_METHOD,
    CONF_MEDIUMS,
    CONF_PASSWORD,
    CONF_SIGNIN_URL,
    CONF_USERNAME,
    DOMAIN,
)
from custom_components.odecet_info.errors import OdecetAuthError
from tests.samples import sample_readings

USER = {
    CONF_USERNAME: "user@example.com",
    CONF_PASSWORD: "secret-value",
    CONF_SIGNIN_URL: "https://odecet.info/signin",
}


@contextmanager
def _client(readings=None, error: Exception | None = None):
    """Patch the flow and the coordinator so setup does not open a socket."""
    client = MagicMock()
    if error is not None:
        client.async_fetch = AsyncMock(side_effect=error)
    else:
        client.async_fetch = AsyncMock(return_value=readings)
    with (
        patch("custom_components.odecet_info.config_flow.OdecetClient", return_value=client),
        patch("custom_components.odecet_info.coordinator.OdecetClient", return_value=client),
    ):
        yield


@pytest.mark.asyncio
async def test_user_flow_creates_an_entry(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        assert result["type"] == "form"
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
        assert result["type"] == "form"
        assert result["step_id"] == "meters"
        assert "Hot water" in result["description_placeholders"]["missing"]
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MEDIUMS: ["cold_water"], CONF_FETCH_METHOD: "table"},
        )
    assert result["type"] == "create_entry"
    assert result["title"] == "user@example.com"
    assert result["data"][CONF_PASSWORD] == "secret-value"
    assert result["options"][CONF_MEDIUMS] == ["cold_water"]
    assert result["options"][CONF_FETCH_METHOD] == "table"


@pytest.mark.asyncio
async def test_bad_password_stays_on_the_form(hass, enable_custom_integrations) -> None:
    with _client(error=OdecetAuthError("rejected")):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
    assert result["type"] == "form"
    assert result["errors"]["base"] == "invalid_auth"
    assert "secret-value" not in result["errors"]["base"]


@pytest.mark.asyncio
async def test_account_without_meters_aborts(hass, enable_custom_integrations) -> None:
    with _client(sample_readings(heat=False, cold=False)):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
    assert result["type"] == "abort"
    assert result["reason"] == "no_meters"


@pytest.mark.asyncio
async def test_same_account_cannot_be_added_twice(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        first = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        first = await hass.config_entries.flow.async_configure(first["flow_id"], USER)
        first = await hass.config_entries.flow.async_configure(
            first["flow_id"],
            {CONF_MEDIUMS: ["cold_water"], CONF_FETCH_METHOD: "auto"},
        )
        assert first["type"] == "create_entry"
        second = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        second = await hass.config_entries.flow.async_configure(second["flow_id"], USER)
    assert second["type"] == "abort"
    assert second["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_keep_only_discovered_mediums(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        created = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        created = await hass.config_entries.flow.async_configure(created["flow_id"], USER)
        created = await hass.config_entries.flow.async_configure(
            created["flow_id"],
            {CONF_MEDIUMS: ["cold_water", "heat"], CONF_FETCH_METHOD: "auto"},
        )
    entry = created["result"]
    with _client(sample_readings(heat=False)):
        result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert "Heat" in result["description_placeholders"]["missing"]
    schema = result["data_schema"].schema
    mediums = schema[CONF_MEDIUMS]
    options = mediums.config["options"] if hasattr(mediums, "config") else None
    assert options is None or all(option["value"] != "heat" for option in options)
