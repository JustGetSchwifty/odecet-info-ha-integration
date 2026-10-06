"""Log in with .env and save a redacted map of the odecet.info pages.

Writes under dev/capture/, which is gitignored. The script prints paths and
status codes only. It does not print the password, the email, or tokens.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "dev" / "capture"
ENV_PATH = ROOT / ".env"

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
TOKEN_RE = re.compile(r"(CfDJ8[A-Za-z0-9_\-]{20,})")


def load_env(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Values are not logged."""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def redact(text: str, username: str) -> str:
    """Remove the account email and antiforgery tokens from saved HTML."""
    cleaned = text.replace(username, "[redacted-email]")
    cleaned = EMAIL_RE.sub("[redacted-email]", cleaned)
    cleaned = TOKEN_RE.sub("[redacted-token]", cleaned)
    return cleaned


def write_text(name: str, text: str, username: str) -> Path:
    CAPTURE.mkdir(parents=True, exist_ok=True)
    path = CAPTURE / name
    path.write_text(redact(text, username), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    return path


async def main() -> None:
    env = load_env(ENV_PATH)
    signin_url = env["ODECET_INFO_SIGNIN_URL"]
    username = env["ODECET_INFO_USERNAME"]
    password = env["ODECET_INFO_PASSWORD"]
    origin = f"{urlparse(signin_url).scheme}://{urlparse(signin_url).netloc}"

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(signin_url) as response:
            html = await response.text()
            print(f"GET signin -> {response.status} final={response.url}")
        write_text("01-signin.html", html, username)

        soup = BeautifulSoup(html, "html.parser")
        token_node = soup.find("input", {"name": "__RequestVerificationToken"})
        if token_node is None or not token_node.get("value"):
            raise SystemExit("signin form has no antiforgery token")
        form = soup.find("form")
        action = urljoin(signin_url, form.get("action") or signin_url)

        form_data = aiohttp.FormData()
        form_data.add_field("email", username)
        form_data.add_field("password", password)
        form_data.add_field("__RequestVerificationToken", token_node["value"])
        form_data.add_field("website", "")
        async with session.post(action, data=form_data) as response:
            body = await response.text()
            print(f"POST signin -> {response.status} bytes={len(body)} ok={body == 'True'}")
        write_text("02-signin-response.txt", body, username)
        if body != "True":
            raise SystemExit("login did not return True")

        async with session.get(origin + "/") as response:
            home = await response.text()
            print(f"GET / -> {response.status} final={response.url} bytes={len(home)}")
        home_path = write_text("03-home.html", home, username)
        links = collect_links(home, str(response_url(origin)))
        write_text("04-links.txt", "\n".join(links), username)

        keywords = (
            "export",
            "csv",
            "excel",
            "histori",
            "meren",
            "měřen",
            "meter",
            "vod",
            "tepl",
            "report",
            "download",
        )
        interesting = [link for link in links if any(word in link.lower() for word in keywords)]
        print(f"interesting links: {len(interesting)}")
        for index, link in enumerate(interesting[:25], start=1):
            await save_page(session, link, f"05-{index:02d}", username)

        await probe_paths(session, origin, username)
        summarize(home_path)


def response_url(origin: str) -> str:
    return origin + "/"


def collect_links(html: str, base: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for tag in soup.find_all(["a", "form"]):
        raw = tag.get("href") or tag.get("action")
        if not raw or raw.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urljoin(base, raw)
        if urlparse(absolute).netloc == urlparse(base).netloc:
            found.append(absolute.split("#")[0])
    # Also keep script URLs that mention export or data endpoints.
    for match in re.findall(r"""["'](/[^"']+)["']""", html):
        if any(word in match.lower() for word in ("export", "csv", "api", "meren", "histori")):
            found.append(urljoin(base, match))
    return sorted(set(found))


async def save_page(
    session: aiohttp.ClientSession, url: str, prefix: str, username: str
) -> None:
    try:
        async with session.get(url) as response:
            body = await response.text(errors="replace")
            content_type = response.headers.get("content-type", "")
            print(f"GET {url} -> {response.status} {content_type} bytes={len(body)}")
    except aiohttp.ClientError as err:
        print(f"GET {url} failed: {type(err).__name__}")
        return
    suffix = "csv" if "csv" in content_type or url.lower().endswith(".csv") else "html"
    write_text(f"{prefix}.{suffix}", body[:500_000], username)


async def probe_paths(
    session: aiohttp.ClientSession, origin: str, username: str
) -> None:
    """Request a short list of likely history and export paths."""
    candidates = [
        "/measurements",
        "/measurement",
        "/history",
        "/historie",
        "/mereni",
        "/meters",
        "/export",
        "/export/csv",
        "/readings",
        "/dashboard",
        "/home",
    ]
    notes: list[str] = []
    for path in candidates:
        url = origin + path
        try:
            async with session.get(url, allow_redirects=False) as response:
                notes.append(f"{response.status} {path} location={response.headers.get('location', '')}")
        except aiohttp.ClientError as err:
            notes.append(f"ERR {path} {type(err).__name__}")
    write_text("06-probes.txt", "\n".join(notes), username)
    for line in notes:
        print(line)


def summarize(home_path: Path) -> None:
    text = home_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    print(f"home title: {title}")
    print(f"tables: {len(soup.find_all('table'))}")
    print(f"forms: {len(soup.find_all('form'))}")


if __name__ == "__main__":
    asyncio.run(main())
