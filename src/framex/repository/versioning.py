"""Repository version lookup entrypoints."""

import re
from functools import lru_cache
from urllib.parse import urlparse

from .providers import REPOSITORY_VERSION_PROVIDERS

VERSION_PATTERN = re.compile(r"\d+(?:\.\d+)*")


@lru_cache(maxsize=128)
def get_latest_repository_version(repo_url: str) -> str | None:
    parsed_url = urlparse(repo_url)
    for provider in REPOSITORY_VERSION_PROVIDERS:
        if provider.matches(parsed_url):
            return provider.get_latest_version(parsed_url)
    return None


def has_newer_release_version(current_version: str, latest_version: str) -> bool:
    current_parts = _normalize_version(current_version)
    latest_parts = _normalize_version(latest_version)
    if current_parts is None or latest_parts is None:
        return False

    max_length = max(len(current_parts), len(latest_parts))
    current_padded = current_parts + (0,) * (max_length - len(current_parts))
    latest_padded = latest_parts + (0,) * (max_length - len(latest_parts))
    return latest_padded > current_padded


def _normalize_version(version: str) -> tuple[int, ...] | None:
    match = VERSION_PATTERN.search(version)
    if match is None:
        return None
    return tuple(int(part) for part in match.group(0).split("."))
