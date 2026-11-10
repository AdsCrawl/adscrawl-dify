# Privacy Policy

This policy describes the data flow of the AdsCrawl Dify plugin. It applies to plugin version 0.0.1.

## Data processed

The plugin processes the page URL, optional CSS selector, output format or field-selector mapping, wait strategy, timeout, and the response returned by AdsCrawl. The AdsCrawl API key is configured in the Dify provider credential form and sent in the `x-api-key` header over HTTPS to `https://api.adscrawl.net`. The plugin does not intentionally collect a user's name, email address, or other account profile data.

Do not put passwords, API keys, cookies, or other secrets in a target URL or page content. This plugin does not accept cookies, login credentials, or user-configured proxy credentials.

## How data is used and shared

The plugin sends the requested URL and extraction parameters to AdsCrawl so its browser-task API can render the page or extract fields. The resulting page content is returned to the Dify app that invoked the tool. AdsCrawl's browser service then makes requests to the target website; AdsCrawl documents managed proxy routing for these tasks. The target website may receive the request and associated browser/network metadata.

The plugin itself does not persist tool inputs or outputs and does not write request headers, API keys, or page content to its own logs. Dify may process or retain tool inputs and outputs under the Dify workspace's own logging, retention, and privacy settings.

AdsCrawl's [Privacy Policy](https://www.adscrawl.net/privacy-policy/) describes its collection of API request, browser-session, usage, log, error, security, and support information; use of service providers; and retention practices. Its [Terms of Service](https://www.adscrawl.net/terms-of-service/) prohibit unauthorized access, access-control bypass, and unauthorized harvesting of sensitive personal information. Users are responsible for having the rights and permissions needed for a target site and its data. Avoid processing sensitive personal information through this plugin.

## Retention and user choices

The plugin has no separate database or retention period. AdsCrawl states that it keeps information for as long as needed to provide the service, meet legal obligations, resolve disputes, enforce agreements, and maintain security logs. For access, correction, export, or deletion requests relating to AdsCrawl, contact AdsCrawl support at [support@adscrawl.net](mailto:support@adscrawl.net). For Dify workspace logs or data, use the workspace administrator's Dify privacy and retention controls.

## Contact

For questions about this plugin's privacy behavior, contact [support@adscrawl.net](mailto:support@adscrawl.net).
