from collections.abc import Generator
from typing import Any
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.adscrawl_client import (
    AdsCrawlClientError,
    normalize_selector,
    normalize_timeout_ms,
    normalize_wait_until,
    post_json,
    validate_target_url,
)


class RenderPageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        try:
            url = validate_target_url(tool_parameters.get("url"))
            content_mode = tool_parameters.get("content_mode") or "markdown"
            if not isinstance(content_mode, str) or content_mode not in {"html", "markdown", "json"}:
                raise AdsCrawlClientError("content_mode must be html, markdown, or json.")
            selector = normalize_selector(tool_parameters.get("selector"))
            wait_until = normalize_wait_until(tool_parameters.get("wait_until"))
            timeout_ms = normalize_timeout_ms(tool_parameters.get("timeout_ms"))

            payload: dict[str, Any] = {
                "url": url,
                "contentMode": content_mode,
                "waitUntil": wait_until,
                "timeoutMs": timeout_ms,
            }
            if selector:
                payload["selector"] = selector

            content_type, result = post_json(
                "/html",
                payload,
                self.runtime.credentials.get("api_key", ""),
                timeout_ms,
            )
            text = result.decode("utf-8", errors="replace")
            if content_mode == "json":
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    raise AdsCrawlClientError("AdsCrawl returned an invalid JSON response.") from None
                yield self.create_json_message(
                    {"url": url, "content_mode": content_mode, "content_type": content_type, "result": parsed}
                )
                return
            if not text.strip():
                raise AdsCrawlClientError("AdsCrawl returned an empty page result.")
            yield self.create_text_message(
                f"Source URL: {url}\nOutput format: {content_mode}\n\n{text}"
            )
        except AdsCrawlClientError as error:
            yield self.create_json_message({"error": error.public_message})
