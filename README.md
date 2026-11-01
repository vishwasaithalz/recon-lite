# Recon Lite

A small, local-first HTTP security-header analyzer. Feed it a saved response-header block or JSON header map and it produces an educational review of common browser security headers.

**No network scanning. No target requests. No telemetry.** Recon Lite analyzes files you provide, making it suitable for offline learning, lab notes, and repeatable defensive reviews.

## Features

- Parses raw HTTP response headers or a JSON header map.
- Checks Content Security Policy, HSTS, MIME-sniffing protection, framing controls, Referrer Policy, and Permissions Policy.
- Flags potentially revealing `Server` and `X-Powered-By` headers.
- Produces readable text or machine-readable JSON.
- Includes sample input and offline unit tests.
- Uses only the Python standard library at runtime.

## Requirements

- Python 3.10 or newer
- No runtime third-party dependencies

## Quick start

From the repository root:

```powershell
py -3 -m recon_lite samples/headers-example.txt
```

JSON output:

```powershell
py -3 -m recon_lite samples/headers-example.txt --format json
```

If the `py` launcher is unavailable, use `python` instead.

## Analyze your own saved headers

Save a response-header block to a text file, for example:

```text
HTTP/2 200
content-type: text/html; charset=utf-8
strict-transport-security: max-age=31536000; includeSubDomains
content-security-policy: default-src 'self'
x-content-type-options: nosniff
```

Then run:

```powershell
py -3 -m recon_lite path\to\your-headers.txt
```

You can also provide a JSON object whose keys are header names and whose values are strings:

```json
{
  "content-type": "text/html",
  "x-content-type-options": "nosniff"
}
```

## Install as a command

```powershell
py -3 -m pip install .
recon-lite samples/headers-example.txt
```

## What the result means

The score is a lightweight learning aid based only on the headers supplied. It is **not** a vulnerability scan, penetration test, compliance assessment, or proof that a site is secure. Header requirements depend on application architecture and deployment context. Review each finding before changing production configuration.

## Development

Run the offline test suite:

```powershell
py -3 -m unittest discover -s tests -v
```

Run the CLI directly from the repository root:

```powershell
py -3 -m recon_lite samples/headers-example.txt
```

## Safety and privacy

- The program never makes HTTP requests or opens network connections.
- Input files are read locally and are not uploaded.
- Do not commit real customer response headers, cookies, authorization values, internal hostnames, or other sensitive data.
- Use only data you are authorized to inspect.

See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Project status

This is an initial, deliberately narrow implementation. It focuses on repeatable analysis of supplied HTTP response headers before adding any network-facing functionality.
