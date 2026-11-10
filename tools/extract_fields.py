from collections.abc import Generator
from typing import Any
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.adscrawl_client import (
    AdsCrawlClientError,
    normalize_timeout_ms,
    normalize_wait_until,
    parse_selector_schema,
    post_json,
    validate_target_url,
)


class ExtractFieldsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            url = validate_target_url(tool_parameters.get("url"))
            selectors = parse_selector_schema(tool_parameters.get("fields_json"))
            wait_until = normalize_wait_until(tool_parameters.get("wait_until"))
            timeout_ms = normalize_timeout_ms(tool_parameters.get("timeout_ms"))
            payload = {
                "url": url,
                "mode": "extract",
                "schema": selectors,
                "waitUntil": wait_until,
                "timeoutMs": timeout_ms,
            }
            _, result = post_json(
                "/spa-extract",
                payload,
                self.runtime.credentials.get("api_key", ""),
                timeout_ms,
            )
            try:
                parsed = json.loads(result.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise AdsCrawlClientError("AdsCrawl returned an invalid JSON extraction response.") from None
            if not isinstance(parsed, (dict, list)):
                raise AdsCrawlClientError("AdsCrawl returned an unexpected extraction response.")
            yield self.create_json_message(parsed)
        except AdsCrawlClientError as error:
            yield self.create_json_message({"error": error.public_message})
