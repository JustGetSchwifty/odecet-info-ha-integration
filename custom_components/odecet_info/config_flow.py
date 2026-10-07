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
from homeassistant.core import callback
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
                )
            ),
            vol.Required(
                CONF_FETCH_METHOD,
                default=defaults.get(CONF_FETCH_METHOD, FetchMethod.AUTO.value),
            ): SelectSelector(
                SelectSelectorConfig(options=_FETCH_OPTIONS, mode=SelectSelectorMode.DROPDOWN)
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


def _missing_text(found: set[str]) -> str:
    missing = [medium.label for medium in Medium if medium.value not in found]
    if not missing:
        return "Cold water, hot water, and heat were all found."
    names = ", ".join(missing)
    return f"Not on this account, so not listed: {names}."


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
        return self.async_show_form(
            step_id="meters",
            data_schema=_meter_schema(self._available, user_input or {}),
            errors=errors,
            description_placeholders={"missing": _missing_text(set(self._available))},
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
        return self.async_show_form(
            step_id="init",
            data_schema=_meter_schema(available, dict(self.config_entry.options)),
            errors=errors,
            description_placeholders={"missing": _missing_text(set(available))},
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
