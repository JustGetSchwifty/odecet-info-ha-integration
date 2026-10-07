"""Config and options flow for an odecet.info account."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    DateSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.translation import async_get_translations

from custom_components.odecet_info.client import OdecetClient
from custom_components.odecet_info.const import (
    CONF_FETCH_METHOD,
    CONF_MEDIUMS,
    CONF_PASSWORD,
    CONF_SIGNIN_URL,
    CONF_SYNC_FROM,
    CONF_USERNAME,
    DEFAULT_SIGNIN_URL,
    DOMAIN,
)
from custom_components.odecet_info.errors import OdecetError, flow_error_key
from custom_components.odecet_info.models import FetchMethod, Medium, ReadingSet

_LOGGER = logging.getLogger(__name__)

_FETCH_OPTIONS: list[SelectOptionDict] = [
    SelectOptionDict(value=FetchMethod.AUTO.value, label="Auto (CSV, then table)"),
    SelectOptionDict(value=FetchMethod.CSV.value, label="CSV export"),
    SelectOptionDict(value=FetchMethod.TABLE.value, label="History table"),
]


def _auth_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    suggested = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=suggested.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(type=TextSelectorType.PASSWORD)
            ),
            vol.Required(
                CONF_SIGNIN_URL,
                default=suggested.get(CONF_SIGNIN_URL, DEFAULT_SIGNIN_URL),
            ): str,
        }
    )


def _meter_schema(
    available: list[str],
    defaults: dict[str, Any],
) -> vol.Schema:
    selected = [item for item in defaults.get(CONF_MEDIUMS, available) if item in available]
    if not selected:
        selected = list(available)
    return vol.Schema(
        {
            vol.Required(CONF_MEDIUMS, default=selected): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=medium.value, label=medium.label)
                        for medium in Medium
                        if medium.value in available
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.LIST,
                    translation_key="medium",
                )
            ),
            vol.Required(
                CONF_FETCH_METHOD,
                default=defaults.get(CONF_FETCH_METHOD, FetchMethod.AUTO.value),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=_FETCH_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN,
                    translation_key="fetch_method",
                )
            ),
            vol.Optional(
                CONF_SYNC_FROM, description={"suggested_value": defaults.get(CONF_SYNC_FROM, "")}
            ): DateSelector(),
        }
    )


def _options_from_input(user_input: dict[str, Any]) -> dict[str, Any]:
    options = {
        CONF_MEDIUMS: list(user_input[CONF_MEDIUMS]),
        CONF_FETCH_METHOD: user_input[CONF_FETCH_METHOD],
    }
    if user_input.get(CONF_SYNC_FROM):
        options[CONF_SYNC_FROM] = user_input[CONF_SYNC_FROM]
    return options


_EN_HEAT_DOCS = (
    "https://github.com/JustGetSchwifty/odecet-info-ha-integration/blob/main/"
    "docs/heat-cost-allocation.md"
)
_CS_HEAT_DOCS = (
    "https://github.com/JustGetSchwifty/odecet-info-ha-integration/blob/main/"
    "docs/cs/heat-cost-allocation.md"
)


def heat_docs_url(language: str) -> str:
    """Czech gets the Czech explanation. Everyone else gets English."""
    if language.casefold().startswith("cs"):
        return _CS_HEAT_DOCS
    return _EN_HEAT_DOCS


async def async_active_language(hass: HomeAssistant) -> str:
    """Language for strings this integration fills in itself.

    The form and the device list are drawn in the profile language. The system
    language (Settings, System, General) is a different setting, and using it
    here pastes Czech into an English screen. One active owner has one profile.
    Several owners, or a profile with no language yet, use the system language.
    """
    system = hass.config.language or "en"
    users = await hass.auth.async_get_users()
    owners = [user for user in users if user.is_owner and user.is_active]
    if len(owners) != 1:
        return system
    # Same file the frontend writes for the profile. Importing the frontend
    # component would make hassfest require it as a dependency.
    saved_store: Store[dict[str, Any]] = Store(
        hass, 1, f"frontend.user_data_{owners[0].id}"
    )
    saved = (await saved_store.async_load() or {}).get("language")
    if isinstance(saved, dict):
        language = saved.get("language")
        if isinstance(language, str) and language.strip():
            return language.strip()
    return system


_ALL_FOUND = "Cold water, hot water, and heat were all found."
_SOME_MISSING = "Not on this account, so not listed: {names}."


def _translated(catalog: dict[str, str], key: str, fallback: str) -> str:
    return catalog.get(f"component.{DOMAIN}.selector.{key}", fallback)


def missing_text(found: set[str], catalog: dict[str, str] | None = None) -> str:
    """Name the meter types the account did not return, in the active language."""
    translations = catalog or {}
    missing = [medium for medium in Medium if medium.value not in found]
    if not missing:
        return _translated(translations, "missing_mediums.options.all_found", _ALL_FOUND)
    names = ", ".join(
        _translated(translations, f"medium.options.{medium.value}", medium.label)
        for medium in missing
    )
    template = _translated(translations, "missing_mediums.options.some_missing", _SOME_MISSING)
    return template.format(names=names)


_DEVICE_NAMES = {
    Medium.COLD_WATER: "Cold water [S/N {serial}]",
    Medium.HOT_WATER: "Hot water [S/N {serial}]",
    Medium.HEAT: "Heat [S/N {serial}]",
}


def device_name(medium: Medium, serial: str, catalog: dict[str, str] | None = None) -> str:
    """Meter device name in the catalog language. English is the fallback."""
    translations = catalog or {}
    template = translations.get(
        f"component.{DOMAIN}.device.{medium.value}.name",
        _DEVICE_NAMES[medium],
    )
    return template.format(serial=serial)


async def _flow_copy(hass: HomeAssistant, found: set[str]) -> tuple[str, str]:
    """Missing-types sentence and heat-docs link in the active language."""
    language = await async_active_language(hass)
    catalog = await async_get_translations(hass, language, "selector", [DOMAIN])
    return missing_text(found, catalog), heat_docs_url(language)


class OdecetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Sign in, then choose which discovered meter types to keep."""

    VERSION = 1

    def __init__(self) -> None:
        self._auth: dict[str, Any] = {}
        self._available: list[str] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                readings = await self._probe(user_input)
            except OdecetError as err:
                errors["base"] = flow_error_key(err)
                _LOGGER.debug("Sign-in check failed: %s", err)
            else:
                found = [medium.value for medium in readings.mediums()]
                if not found:
                    return self.async_abort(reason="no_meters")
                await self.async_set_unique_id(user_input[CONF_USERNAME].strip().casefold())
                self._abort_if_unique_id_configured()
                self._auth = user_input
                self._available = found
                return await self.async_step_meters()
        return self.async_show_form(
            step_id="user",
            data_schema=_auth_schema(user_input),
            errors=errors,
        )

    async def async_step_meters(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_MEDIUMS):
                errors["base"] = "mediums_required"
            else:
                return self.async_create_entry(
                    title=self._auth[CONF_USERNAME].strip(),
                    data={
                        CONF_USERNAME: self._auth[CONF_USERNAME].strip(),
                        CONF_PASSWORD: self._auth[CONF_PASSWORD],
                        CONF_SIGNIN_URL: self._auth[CONF_SIGNIN_URL].strip(),
                    },
                    options=_options_from_input(user_input),
                )
        missing, docs_url = await _flow_copy(self.hass, set(self._available))
        return self.async_show_form(
            step_id="meters",
            data_schema=_meter_schema(self._available, user_input or {}),
            errors=errors,
            description_placeholders={"missing": missing, "heat_docs_url": docs_url},
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            candidate = {
                CONF_USERNAME: entry.data[CONF_USERNAME],
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_SIGNIN_URL: entry.data[CONF_SIGNIN_URL],
            }
            try:
                await self._probe(candidate)
            except OdecetError as err:
                errors["base"] = flow_error_key(err)
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]},
                    reason="reauth_successful",
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            try:
                await self._probe(user_input)
            except OdecetError as err:
                errors["base"] = flow_error_key(err)
            else:
                username = user_input[CONF_USERNAME].strip().casefold()
                other = self.hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, username)
                if other is not None and other.entry_id != entry.entry_id:
                    return self.async_abort(reason="already_configured")
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=username,
                    title=user_input[CONF_USERNAME].strip(),
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SIGNIN_URL: user_input[CONF_SIGNIN_URL].strip(),
                    },
                    reason="reconfigure_successful",
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_auth_schema(dict(entry.data)),
            errors=errors,
        )

    async def _probe(self, credentials: dict[str, Any]) -> ReadingSet:
        session = async_create_clientsession(self.hass, auto_cleanup=False)
        try:
            client = OdecetClient(
                session,
                credentials[CONF_SIGNIN_URL].strip(),
                credentials[CONF_USERNAME].strip(),
                credentials[CONF_PASSWORD],
            )
            return await client.async_fetch(FetchMethod.AUTO)
        finally:
            session.detach()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OdecetOptionsFlow:
        return OdecetOptionsFlow()


class OdecetOptionsFlow(OptionsFlow):
    """Change meter types, the fetch method, and the start date."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_MEDIUMS):
                errors["base"] = "mediums_required"
            else:
                return self.async_create_entry(data=_options_from_input(user_input))

        available, error = await self._available_mediums()
        if error:
            errors["base"] = error
        if not available:
            available = list(self.config_entry.options.get(CONF_MEDIUMS, []))
        missing, docs_url = await _flow_copy(self.hass, set(available))
        return self.async_show_form(
            step_id="init",
            data_schema=_meter_schema(available, dict(self.config_entry.options)),
            errors=errors,
            description_placeholders={"missing": missing, "heat_docs_url": docs_url},
        )

    async def _available_mediums(self) -> tuple[list[str], str | None]:
        session = async_create_clientsession(self.hass, auto_cleanup=False)
        try:
            readings = await OdecetClient(
                session,
                self.config_entry.data[CONF_SIGNIN_URL],
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_PASSWORD],
            ).async_fetch(FetchMethod.AUTO)
        except OdecetError as err:
            _LOGGER.debug("Options discovery failed: %s", err)
            return [], flow_error_key(err)
        finally:
            session.detach()
        return [medium.value for medium in readings.mediums()], None
