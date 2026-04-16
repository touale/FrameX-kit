"""Base types and shared helpers for repository version providers."""

from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import ParseResult

import httpx

DEFAULT_HTTP_TIMEOUT = 2.0


class RepositoryVersionProvider(ABC):
    """Abstract interface for repository hosting providers."""

    name: str

    @abstractmethod
    def matches(self, parsed_url: ParseResult) -> bool:
        """Return whether this provider can handle the parsed repository URL."""

    @abstractmethod
    def get_latest_version(self, parsed_url: ParseResult) -> str | None:
        """Return the latest published version for the repository URL."""

    @staticmethod
    def extract_repository_parts(parsed_url: ParseResult) -> list[str]:
        """Split a repository path into normalized URL parts."""

        parts = [part for part in parsed_url.path.split("/") if part]
        if parts:
            parts[-1] = parts[-1].removesuffix(".git")
        return parts

    @staticmethod
    def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any] | None:
        """Fetch a JSON object and return `None` when it cannot be consumed."""

        try:
            with httpx.Client(timeout=DEFAULT_HTTP_TIMEOUT, headers=headers) as client:
                response = client.get(url, follow_redirects=True)
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        return payload if isinstance(payload, dict) else None

    @staticmethod
    def extract_version(payload: dict[str, Any] | None) -> str | None:
        """Read a version-like string from a release payload."""

        if payload is None:
            return None

        latest_version = payload.get("tag_name") or payload.get("name")
        if not isinstance(latest_version, str):
            return None

        latest_version = latest_version.strip()
        return latest_version or None
