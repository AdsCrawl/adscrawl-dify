# AdsCrawl for Dify

**Author:** adscrawl  
**Version:** 0.0.1  
**Type:** Tool plugin

Bring AdsCrawl's browser-rendered page extraction into Dify workflows and agents.

## Tools

- **Render Page** calls AdsCrawl `POST /html` to return HTML, readable Markdown, or article JSON. It can optionally wait for a CSS selector and supports the documented `load`, `domcontentloaded`, and `networkidle` wait strategies.
- **Extract Fields** calls AdsCrawl `POST /spa-extract` in `extract` mode. Provide a JSON object mapping output names to CSS selectors, for example `{"title":"h1","price":".price"}`.

Both tools use the AdsCrawl HTTPS API and return results to the calling Dify app. Requests may consume AdsCrawl credits. The plugin makes one API request per tool invocation and does not automatically retry.

## Setup

1. Create or sign in to an AdsCrawl account and create an API key in the [AdsCrawl dashboard](https://app.adscrawl.net/dashboard/keys).
2. Install the plugin in Dify and configure the **AdsCrawl API key** in the provider credentials form. Keep the key in that secret field; do not put it in a prompt or target URL.
3. Use the Render Page or Extract Fields tool in an Agent or Workflow.

The API key is sent as `x-api-key` only to `https://api.adscrawl.net` over HTTPS. See the [AdsCrawl authentication guide](https://api.adscrawl.net/auth.md).

## Safety and limits

These tools fetch user-provided URLs through AdsCrawl's browser service. Only complete HTTP(S) URLs on ports 80 or 443 are accepted; embedded credentials, localhost, private IP literals, and local hostnames are rejected. The plugin bounds navigation timeouts to 90 seconds and results to 1 MiB. It does not accept cookies, user-supplied proxy credentials, or CDP/browser-control commands. AdsCrawl's service may apply its documented managed routing. Do not use the plugin to bypass access controls or collect data without permission; follow the [AdsCrawl Terms of Service](https://www.adscrawl.net/terms-of-service/) and the target site's terms and privacy requirements. Avoid URLs or page content containing passwords, API keys, or sensitive personal data.

## Documentation and support

- [AdsCrawl Browser Tasks API](https://www.adscrawl.net/docs/browser-tasks/)
- [AdsCrawl Privacy Policy](https://www.adscrawl.net/privacy-policy/)
- Support: [support@adscrawl.net](mailto:support@adscrawl.net)

**Source repository:** [https://github.com/AdsCrawl/adscrawl-dify](https://github.com/AdsCrawl/adscrawl-dify)
