# Security Policy

## Scope

Recon Lite currently analyzes HTTP response headers supplied in local text or JSON files. It does not make network requests, scan hosts, execute supplied content, or transmit input data.

## Reporting

Please report suspected vulnerabilities privately to the repository owner where GitHub private vulnerability reporting is available. Do not publish sensitive details before a fix is available.

## Safe use

- Do not add network scanning or target interaction without an explicit, documented authorization model and security review.
- Never commit cookies, authorization headers, API keys, private URLs, customer data, or internal infrastructure details.
- Treat imported header files as potentially sensitive.
- Keep dependencies minimal and review any proposed runtime dependency.
