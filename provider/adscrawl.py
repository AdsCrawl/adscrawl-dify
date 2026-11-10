from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


API_ORIGIN = "https://api.adscrawl.net"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AdscrawlProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = credentials.get("api_key")
        if not isinstance(api_key, str) or not api_key.strip():
            raise ToolProviderCredentialValidationError("Enter an AdsCrawl API key.")

        request = Request(
            f"{API_ORIGIN}/cdp/sessions",
            headers={"x-api-key": api_key.strip(), "Accept": "application/json"},
            method="GET",
        )
        opener = build_opener(_NoRedirect)
        try:
            with opener.open(request, timeout=15) as response:
                if response.status != 200:
                    raise ToolProviderCredentialValidationError(
                        "AdsCrawl did not accept this API key. Check the key and try again."
                    )
        except ToolProviderCredentialValidationError:
            raise
        except HTTPError as error:
            if error.code == 401:
                message = "AdsCrawl did not accept this API key. Check the key and try again."
            else:
                message = "AdsCrawl could not validate the key right now. Try again later."
            raise ToolProviderCredentialValidationError(message) from None
        except (URLError, TimeoutError, OSError):
            raise ToolProviderCredentialValidationError(
                "Could not reach AdsCrawl to validate the API key. Try again later."
            ) from None
