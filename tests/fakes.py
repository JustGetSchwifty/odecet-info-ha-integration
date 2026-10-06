"""Scripted HTTP session for client tests. It never opens a socket."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


class Response:
    """Async context manager with the slice of aiohttp the client uses."""

    def __init__(self, status: int, body: str, url: str) -> None:
        self.status = status
        self.url = url
        self.headers = {"content-type": "text/html; charset=utf-8"}
        self._body = body

    async def text(self, errors: str = "strict") -> str:
        return self._body

    async def __aenter__(self) -> Response:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False


class ScriptedSession:
    """Return prepared responses in order and record the calls."""

    def __init__(self, responses: list[Response | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> Response:
        return self._next("GET", url, kwargs)

    def post(self, url: str, **kwargs: object) -> Response:
        return self._next("POST", url, kwargs)

    def _next(self, method: str, url: str, kwargs: dict[str, object]) -> Response:
        self.calls.append({"method": method, "url": str(url), **kwargs})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def form_fields(payload: object) -> dict[str, str]:
    """Read names and values back out of an aiohttp FormData payload."""
    fields: dict[str, str] = {}
    for type_options, _headers, value in payload._fields:  # type: ignore[attr-defined]
        fields[type_options["name"]] = value
    return fields
