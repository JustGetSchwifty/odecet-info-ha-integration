"""Failures the odecet.info client can report.

Home Assistant maps these differently: authentication starts a reauth flow,
rate limits and transport errors are retried, and a structure error means the
site no longer matches the parser.
"""

from __future__ import annotations


class OdecetError(Exception):
    """Base error for sign-in and parsing."""


class OdecetValidationError(OdecetError):
    """The username or password failed a local check and was not sent."""


class OdecetAuthError(OdecetError):
    """The site rejected the credentials or the session expired."""


class OdecetRateLimitError(OdecetError):
    """The site answered HTTP 429."""


class OdecetTransportError(OdecetError):
    """The site could not be reached, or it returned HTTP 5xx."""


class OdecetStructureError(OdecetError):
    """The HTML or CSV no longer matches the known page contract."""


def flow_error_key(err: OdecetError) -> str:
    """Map a client error to a config-flow translation key."""
    if isinstance(err, OdecetValidationError):
        return "invalid_input"
    if isinstance(err, OdecetAuthError):
        return "invalid_auth"
    if isinstance(err, OdecetRateLimitError):
        return "rate_limited"
    if isinstance(err, OdecetTransportError):
        return "cannot_connect"
    return "unknown"
