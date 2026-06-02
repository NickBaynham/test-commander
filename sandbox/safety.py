"""Safe-by-default sandbox targeting (Phase 12 Step 12.4).

A sandbox may only be aimed at an allow-listed host, and private/loopback/
link-local ranges are blocked by default so it cannot be pointed at an internal
network. The guards read the sandbox config's `allowed_domains` and
`block_private_ranges`.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlparse

PRIVATE_REASON = "private/loopback/link-local range blocked by default"


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str


def _host(target: str) -> str:
    parsed = urlparse(target if "//" in target else f"//{target}")
    return (parsed.hostname or "").lower()


def is_private_host(host: str) -> bool:
    """True for an IP literal in a private, loopback, or link-local range."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def host_allowed(host: str, allowed_domains) -> bool:
    """True if the host matches an allow-list entry (exact, subdomain, or `*.` wildcard)."""
    host = (host or "").lower()
    for pattern in allowed_domains or ():
        p = str(pattern).lower()
        base = p[2:] if p.startswith("*.") else p
        if host == base or host.endswith("." + base):
            return True
    return False


def check_target(target: str, config: dict) -> SafetyDecision:
    """Decide whether the sandbox may be aimed at `target`. Default deny."""
    host = _host(target)
    if not host:
        return SafetyDecision(False, "no host in target")
    if config.get("block_private_ranges", True) and is_private_host(host):
        return SafetyDecision(False, f"{host}: {PRIVATE_REASON}")
    if not host_allowed(host, config.get("allowed_domains", [])):
        return SafetyDecision(False, f"{host}: not on the allow-list")
    return SafetyDecision(True, f"{host}: allowed")
