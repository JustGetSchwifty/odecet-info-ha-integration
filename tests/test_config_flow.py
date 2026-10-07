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
from custom_components.odecet_info.errors import (
    OdecetAuthError,
    OdecetRateLimitError,
    OdecetStructureError,
    OdecetTransportError,
    OdecetValidationError,
    flow_error_key,
)
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


def test_missing_sentence_uses_translated_medium_names() -> None:
    from custom_components.odecet_info.config_flow import missing_text

    catalog = {
        "component.odecet_info.selector.medium.options.hot_water": "Teplá voda",
        "component.odecet_info.selector.missing_mediums.options.some_missing": (
            "Na tomto účtu nejsou, proto nejsou v seznamu: {names}."
        ),
        "component.odecet_info.selector.missing_mediums.options.all_found": (
            "Studená voda, teplá voda i topení byly na účtu nalezeny."
        ),
    }
    assert (
        missing_text({"cold_water", "heat"}, catalog)
        == "Na tomto účtu nejsou, proto nejsou v seznamu: Teplá voda."
    )
    assert "nalezeny" in missing_text({"cold_water", "hot_water", "heat"}, catalog)
    assert "Hot water" in missing_text({"cold_water"})


def test_flow_error_keys_cover_each_client_failure() -> None:
    assert flow_error_key(OdecetValidationError("x")) == "invalid_input"
    assert flow_error_key(OdecetAuthError("x")) == "invalid_auth"
    assert flow_error_key(OdecetRateLimitError("x")) == "rate_limited"
    assert flow_error_key(OdecetTransportError("x")) == "cannot_connect"
    assert flow_error_key(OdecetStructureError("x")) == "unknown"


@pytest.mark.asyncio
async def test_meters_step_requires_a_selection(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_MEDIUMS: [], CONF_FETCH_METHOD: "auto", "sync_from": "2024-01-01"},
        )
    assert result["type"] == "form"
    assert result["errors"]["base"] == "mediums_required"


@pytest.mark.asyncio
async def test_reauth_replaces_the_password(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        created = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        created = await hass.config_entries.flow.async_configure(created["flow_id"], USER)
        created = await hass.config_entries.flow.async_configure(
            created["flow_id"],
            {CONF_MEDIUMS: ["cold_water"], CONF_FETCH_METHOD: "auto"},
        )
    entry = created["result"]
    with _client(sample_readings()):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": "reauth",
                "entry_id": entry.entry_id,
                "unique_id": entry.unique_id,
            },
            data=entry.data,
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "new-secret"},
        )
    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-secret"


@pytest.mark.asyncio
async def test_reconfigure_updates_the_account(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        created = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        created = await hass.config_entries.flow.async_configure(created["flow_id"], USER)
        created = await hass.config_entries.flow.async_configure(
            created["flow_id"],
            {CONF_MEDIUMS: ["cold_water"], CONF_FETCH_METHOD: "auto"},
        )
    entry = created["result"]
    updated = {
        CONF_USERNAME: "other@example.com",
        CONF_PASSWORD: "other-secret",
        CONF_SIGNIN_URL: "https://odecet.info/signin",
    }
    with _client(sample_readings()):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": entry.entry_id},
        )
        assert result["step_id"] == "reconfigure"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], updated)
    assert result["type"] == "abort"
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_USERNAME] == "other@example.com"


@pytest.mark.asyncio
async def test_options_keep_the_form_when_discovery_fails(hass, enable_custom_integrations) -> None:
    with _client(sample_readings()):
        created = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        created = await hass.config_entries.flow.async_configure(created["flow_id"], USER)
        created = await hass.config_entries.flow.async_configure(
            created["flow_id"],
            {CONF_MEDIUMS: ["cold_water"], CONF_FETCH_METHOD: "auto"},
        )
    entry = created["result"]
    with _client(error=OdecetTransportError("down")):
        result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"
    with _client(sample_readings()):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {CONF_MEDIUMS: [], CONF_FETCH_METHOD: "auto"},
        )
    assert result["errors"]["base"] == "mediums_required"
