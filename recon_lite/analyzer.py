"""Offline analysis of user-supplied HTTP response headers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ACCEPTED_REFERRER_POLICIES = {
    "no-referrer",
    "no-referrer-when-downgrade",
    "same-origin",
    "origin",
    "strict-origin",
    "origin-when-cross-origin",
    "strict-origin-when-cross-origin",
}

def parse_headers_text(content: str) -> dict[str, str]:
    """Parse a raw response-header block or a JSON header mapping."""
    stripped = content.strip()
    if not stripped:
        raise ValueError("The input file is empty.")

    if stripped.startswith("{"):
        try:
            raw: Any = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON input: {exc.msg}") from exc
        if not isinstance(raw, dict):
            raise ValueError("JSON input must be an object of header names and values.")
        headers: dict[str, str] = {}
        for name, value in raw.items():
            if not isinstance(name, str) or not isinstance(value, (str, int, float)):
                raise ValueError("JSON header names must be strings and values must be strings or numbers.")
            headers[name.strip().lower()] = str(value).strip()
        return headers

    headers = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        line = line.strip("\r")
        if not line.strip():
            continue
        if line.upper().startswith("HTTP/"):
            continue
        if line[:1].isspace():
            # Obsolete folded headers are ignored rather than interpreted.
            continue
        if ":" not in line:
            raise ValueError(f"Malformed header on line {line_number}: expected 'Name: value'.")
        name, value = line.split(":", 1)
        name = name.strip().lower()
        if not name or any(char.isspace() for char in name):
            raise ValueError(f"Invalid header name on line {line_number}.")
        value = value.strip()
        if name in headers:
            headers[name] = f"{headers[name]}, {value}"
        else:
            headers[name] = value

    if not headers:
        raise ValueError("No HTTP headers were found in the input.")
    return headers


def analyze_headers(headers: dict[str, str]) -> dict[str, Any]:
    """Return a deterministic, context-limited review of common response headers."""
    normalized = {str(k).strip().lower(): str(v).strip() for k, v in headers.items()}
    findings: list[dict[str, str]] = []

    def add(name: str, status: str, severity: str, detail: str, recommendation: str) -> None:
        findings.append({
            "header": name,
            "status": status,
            "severity": severity,
            "detail": detail,
            "recommendation": recommendation,
        })

    csp = normalized.get("content-security-policy", "")
    if not csp:
        add("Content-Security-Policy", "missing", "high",
            "No Content Security Policy was supplied.",
            "Define a policy that matches the application's required scripts, styles, images, connections, and framing behavior. Start with Report-Only when introducing a policy to an existing application.")
    elif "default-src" not in csp.lower() and "script-src" not in csp.lower():
        add("Content-Security-Policy", "review", "medium",
            "A CSP is present, but common baseline directives were not detected.",
            "Review the policy against the application's actual resource-loading requirements.")
    else:
        add("Content-Security-Policy", "present", "info",
            "A Content Security Policy was supplied. Its effectiveness was not validated.",
            "Review directives, sources, nonces or hashes, and report handling.")

    hsts = normalized.get("strict-transport-security", "")
    if not hsts:
        add("Strict-Transport-Security", "missing", "high",
            "No HTTP Strict Transport Security header was supplied.",
            "For HTTPS-only sites, consider an appropriate max-age and carefully assess includeSubDomains and preload before enabling them.")
    elif "max-age=" not in hsts.lower():
        add("Strict-Transport-Security", "review", "medium",
            "The HSTS header does not contain a recognizable max-age directive.",
            "Set and validate a deliberate max-age value for the deployment.")
    else:
        add("Strict-Transport-Security", "present", "info",
            "An HSTS max-age directive was detected.",
            "Confirm HTTPS works across the relevant hosts before increasing enforcement.")

    xcto = normalized.get("x-content-type-options", "")
    if xcto.lower() != "nosniff":
        add("X-Content-Type-Options", "missing" if not xcto else "review", "medium",
            "The expected nosniff value was not detected.",
            "For typical web applications, send X-Content-Type-Options: nosniff and use correct Content-Type values.")
    else:
        add("X-Content-Type-Options", "present", "info",
            "The nosniff value was detected.",
            "Ensure resources are served with accurate Content-Type values.")

    xfo = normalized.get("x-frame-options", "").lower()
    csp_frame_ancestors = "frame-ancestors" in csp.lower()
    if xfo not in {"deny", "sameorigin"} and not csp_frame_ancestors:
        add("X-Frame-Options / CSP frame-ancestors", "missing", "medium",
            "No common framing restriction was detected.",
            "Use CSP frame-ancestors; X-Frame-Options may be retained for compatibility with older browsers.")
    else:
        add("X-Frame-Options / CSP frame-ancestors", "present", "info",
            "A common framing restriction was detected.",
            "Confirm the allowed embedding origins match the product's intended behavior.")

    referrer = normalized.get("referrer-policy", "").lower()
    if not referrer:
        add("Referrer-Policy", "missing", "low",
            "No Referrer-Policy was supplied.",
            "Consider strict-origin-when-cross-origin or a stricter policy appropriate to the application.")
    elif referrer not in ACCEPTED_REFERRER_POLICIES:
        add("Referrer-Policy", "review", "low",
            "The supplied policy is not in the analyzer's recognized policy list.",
            "Check the value against current browser support and the application's privacy requirements.")
    else:
        add("Referrer-Policy", "present", "info",
            f"Recognized policy detected: {referrer}.",
            "Confirm the policy does not expose more URL information than intended.")

    permissions = normalized.get("permissions-policy", "")
    if not permissions:
        add("Permissions-Policy", "missing", "low",
            "No Permissions-Policy was supplied.",
            "Consider explicitly restricting browser features the application does not need.")
    else:
        add("Permissions-Policy", "present", "info",
            "A Permissions-Policy was supplied. Its directives were not semantically validated.",
            "Review each directive and allow only required origins and features.")

    for name in ("server", "x-powered-by"):
        if normalized.get(name):
            add(name.title(), "disclosure", "info",
                f"The response discloses this value: {normalized[name]}.",
                "Consider whether the value is operationally necessary; removing it is a minor hardening measure, not a substitute for patching.")

    deductions = {"high": 20, "medium": 10, "low": 5, "info": 0}
    score = max(0, 100 - sum(deductions[item["severity"]] for item in findings))
    counts = {
        status: sum(1 for item in findings if item["status"] == status)
        for status in ("missing", "review", "disclosure", "present")
    }
    return {
        "tool": "Recon Lite",
        "version": "0.1.0",
        "scope": "Supplied headers only; no network requests were made.",
        "score": score,
        "score_note": "Educational heuristic only. Not a security rating or compliance result.",
        "summary": counts,
        "findings": findings,
    }


def analyze_file(path: str | Path) -> dict[str, Any]:
    """Read a local file and analyze its supplied headers."""
    input_path = Path(path)
    try:
        content = input_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ValueError(f"Cannot read input file '{input_path}': {exc}") from exc
    return analyze_headers(parse_headers_text(content))
