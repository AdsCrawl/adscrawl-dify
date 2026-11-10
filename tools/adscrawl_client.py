"""Minimal, bounded HTTPS client for the AdsCrawl browser-task APIs."""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


API_ORIGIN = "https://api.adscrawl.net"
MAX_REQUEST_BYTES = 1_048_576
MAX_RESULT_BYTES = 1_048_576
MAX_URL_CHARS = 4096
MAX_SELECTOR_CHARS = 512
MAX_FIELDS = 30
DEFAULT_TIMEOUT_MS = 60_000
MAX_TIMEOUT_MS = 90_000


class AdsCrawlClientError(ValueError):
    """A safe, user-facing AdsCrawl request error without raw response content."""

    def __init__(self, public_message: str):
        super().__init__(public_message)
        self.public_message = public_message


class _NoRedirect(HTTPRedirectHandler):
    """Never forward the API-key header through an HTTP redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_target_url(value: Any) -> str:
    if not isinstance(value, str):
        raise AdsCrawlClientError("Provide a public HTTP or HTTPS page URL.")
    url = value.strip()
    if not url or len(url) > MAX_URL_CHARS:
        raise AdsCrawlClientError("Provide a non-empty URL of at most 4,096 characters.")
    if any(ord(char) < 32 for char in url):
        raise AdsCrawlClientError("The URL contains unsupported control characters.")

    try:
        parsed = urlsplit(url)
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        port = parsed.port
    except ValueError:
        raise AdsCrawlClientError("The URL is malformed or uses an invalid port.") from None

    if scheme not in {"http", "https"} or not host:
        raise AdsCrawlClientError("Only complete HTTP or HTTPS page URLs are supported.")
    if parsed.username is not None or parsed.password is not None:
        raise AdsCrawlClientError("URLs containing embedded usernames or passwords are not allowed.")
    if port is not None and port not in {80, 443}:
        raise AdsCrawlClientError("AdsCrawl supports target URLs on ports 80 and 443 only.")

    normalized_host = host.rstrip(".").lower()
    if "%" in normalized_host:
        raise AdsCrawlClientError("IP addresses with zone identifiers are not allowed.")
    if normalized_host in {"localhost", "localhost.localdomain"} or normalized_host.endswith(
        (".localhost", ".local", ".internal", ".test", ".home.arpa")
    ):
        raise AdsCrawlClientError("Local or private network hostnames are not allowed.")

    # Reject private, loopback, link-local, reserved, and other non-global IP literals.
    address = None
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        # inet_aton also recognizes legacy numeric IPv4 forms (for example 2130706433).
        try:
            packed = socket.inet_aton(normalized_host)
            address = ipaddress.IPv4Address(packed)
        except OSError:
            pass
    if address is not None and not address.is_global:
        raise AdsCrawlClientError("Local or non-public IP addresses are not allowed.")

    try:
        normalized_host.encode("idna")
    except UnicodeError:
        raise AdsCrawlClientError("The URL hostname is invalid.") from None
    return url


def normalize_timeout_ms(value: Any) -> int:
    if value is None or value == "":
        return DEFAULT_TIMEOUT_MS
    if isinstance(value, bool):
        raise AdsCrawlClientError("Timeout must be a number from 1,000 to 90,000 milliseconds.")
    try:
        timeout_ms = int(value)
    except (TypeError, ValueError, OverflowError):
        raise AdsCrawlClientError("Timeout must be a number from 1,000 to 90,000 milliseconds.") from None
    if timeout_ms < 1000 or timeout_ms > MAX_TIMEOUT_MS:
        raise AdsCrawlClientError("Timeout must be from 1,000 to 90,000 milliseconds.")
    return timeout_ms


def normalize_wait_until(value: Any) -> str:
    wait_until = "domcontentloaded" if value is None or value == "" else value
    if not isinstance(wait_until, str) or wait_until not in {"load", "domcontentloaded", "networkidle"}:
        raise AdsCrawlClientError("wait_until must be load, domcontentloaded, or networkidle.")
    return wait_until


def normalize_selector(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise AdsCrawlClientError("CSS selector must be text.")
    selector = value.strip()
    if not selector or len(selector) > MAX_SELECTOR_CHARS:
        raise AdsCrawlClientError("CSS selector must contain 1 to 512 characters.")
    return selector


def parse_selector_schema(value: Any) -> dict[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise AdsCrawlClientError(
            'fields_json must be a JSON object such as {"title":"h1","price":".price"}.'
        )
    if len(value) > 16_384:
        raise AdsCrawlClientError("fields_json must be no larger than 16 KiB.")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        raise AdsCrawlClientError("fields_json is not valid JSON.") from None
    if not isinstance(parsed, dict) or not parsed:
        raise AdsCrawlClientError("fields_json must be a non-empty JSON object.")
    if len(parsed) > MAX_FIELDS:
        raise AdsCrawlClientError(f"fields_json may define at most {MAX_FIELDS} fields.")

    result: dict[str, str] = {}
    for name, selector in parsed.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,63}", name):
            raise AdsCrawlClientError("Field names must start with a letter or underscore and use at most 64 safe characters.")
        normalized = normalize_selector(selector)
        if normalized is None:
            raise AdsCrawlClientError(f"The CSS selector for field '{name}' is empty.")
        result[name] = normalized
    return result


def post_json(path: str, payload: dict[str, Any], api_key: str, timeout_ms: int) -> tuple[str, bytes]:
    if path not in {"/html", "/spa-extract"}:
        raise AdsCrawlClientError("This operation is not available through the plugin.")
    if not isinstance(api_key, str) or not api_key.strip():
        raise AdsCrawlClientError("Configure an AdsCrawl API key in the provider settings.")

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_REQUEST_BYTES:
        raise AdsCrawlClientError("The request is larger than AdsCrawl's 1 MiB request limit.")
    request = Request(
        f"{API_ORIGIN}{path}",
        data=body,
        headers={
            "x-api-key": api_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json, text/markdown, text/html",
        },
        method="POST",
    )
    transport_timeout = min(105, timeout_ms / 1000 + 15)
    opener = build_opener(_NoRedirect)

    try:
        with opener.open(request, timeout=transport_timeout) as response:
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            result = response.read(MAX_RESULT_BYTES + 1)
    except HTTPError as error:
        raise AdsCrawlClientError(_http_error_message(error.code)) from None
    except (TimeoutError, socket.timeout):
        raise AdsCrawlClientError("The AdsCrawl request timed out. Try a shorter wait strategy or a faster page.") from None
    except URLError as error:
        if isinstance(getattr(error, "reason", None), (TimeoutError, socket.timeout)):
            raise AdsCrawlClientError("The AdsCrawl request timed out. Try a faster page.") from None
        raise AdsCrawlClientError("Could not reach AdsCrawl. Check the network and try again later.") from None
    except OSError:
        raise AdsCrawlClientError("Could not reach AdsCrawl. Check the network and try again later.") from None

    if len(result) > MAX_RESULT_BYTES:
        raise AdsCrawlClientError(
            "The result is larger than the plugin's 1 MiB output limit. Use a CSS selector or a narrower extraction."
        )
    return content_type, result


def _http_error_message(status: int) -> str:
    messages = {
        400: "AdsCrawl rejected the request. Check the URL and selected options.",
        401: "AdsCrawl rejected the API key. Check the provider credentials.",
        402: "The AdsCrawl account has insufficient credits for this request.",
        422: "AdsCrawl could not complete the page task. Check the URL, selector, or extraction fields.",
        429: "AdsCrawl rate-limited the request. Reduce request frequency and try again later.",
        502: "The target page, proxy, or returned result could not be reached. Check the URL and try again later.",
        503: "AdsCrawl browser or proxy capacity is temporarily unavailable. Try again later.",
        504: "The target page or browser task timed out. Try a shorter wait strategy or a faster page.",
    }
    return messages.get(status, f"AdsCrawl returned an HTTP {status} error. Try again later.")
