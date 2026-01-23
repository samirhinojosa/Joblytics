from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


@dataclass(frozen=True)
class RobotsDecision:
    allowed: bool
    reason: str


@lru_cache(maxsize=128)
def _parser_for_base(base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    rp.set_url(f"{base_url.rstrip('/')}/robots.txt")
    try:
        rp.read()
    except Exception:
        # best-effort: if robots cannot be fetched, allow
        pass
    return rp


def is_allowed(url: str, user_agent: str) -> RobotsDecision:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = _parser_for_base(base)
    try:
        allowed = rp.can_fetch(user_agent, url)
        return RobotsDecision(allowed=allowed, reason="robots.txt")
    except Exception:
        return RobotsDecision(allowed=True, reason="robots_unavailable")
