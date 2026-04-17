"""Repository version lookup entrypoints."""

import re
from urllib.parse import ParseResult, urlparse

from framex.repository.providers.base import RepositoryVersionProvider

from .providers import REPOSITORY_VERSION_PROVIDERS

VERSION_PATTERN = re.compile(r"\d+(?:\.\d+)*")


def _get_provider_for_url(repo_url: str) -> tuple[RepositoryVersionProvider | None, ParseResult]:
    parsed_url = urlparse(repo_url)
    provider = next((provider for provider in REPOSITORY_VERSION_PROVIDERS if provider.matches(parsed_url)), None)
    return provider, parsed_url


async def get_latest_repository_version(repo_url: str) -> str | None:
    provider, parsed_url = _get_provider_for_url(repo_url)
    if provider is None:
        return None
    return await provider.get_latest_version(parsed_url)


async def is_private_repository(repo_url: str) -> bool | None:
    provider, parsed_url = _get_provider_for_url(repo_url)
    if provider is None:
        return None

    is_public = await provider.is_public_repository(parsed_url)
    if is_public is None:
        return None
    return not is_public


async def can_access_repository(repo_url: str, provider_name: str | None, access_token: str | None) -> bool | None:
    provider, parsed_url = _get_provider_for_url(repo_url)
    if provider is None:
        return None

    if not provider_name or provider.name != provider_name:
        return None
    if not access_token:
        return False

    return await provider.has_repository_access(parsed_url, access_token)


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
