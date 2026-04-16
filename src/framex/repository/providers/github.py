"""GitHub repository version provider."""

from urllib.parse import ParseResult

from framex.config import settings

from .base import RepositoryVersionProvider

GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})
GITHUB_API_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "framex-docs",
}


class GitHubRepositoryVersionProvider(RepositoryVersionProvider):
    """Resolve latest release versions for GitHub repositories."""

    name = "github"

    def matches(self, parsed_url: ParseResult) -> bool:
        return parsed_url.netloc in GITHUB_HOSTS

    def get_latest_version(self, parsed_url: ParseResult) -> str | None:
        repository = self._extract_owner_and_repository(parsed_url)
        if repository is None:
            return None

        owner, repo = repository
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        headers = {**GITHUB_API_HEADERS, **settings.repository.auth.github.build_headers()}
        payload = self.fetch_json(api_url, headers=headers)
        return self.extract_version(payload)

    def is_public_repository(self, parsed_url: ParseResult) -> bool | None:
        repository = self._extract_owner_and_repository(parsed_url)
        if repository is None:
            return None

        owner, repo = repository
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        return self.can_fetch(api_url, headers=GITHUB_API_HEADERS)

    def has_repository_access(self, parsed_url: ParseResult, access_token: str) -> bool:
        repository = self._extract_owner_and_repository(parsed_url)
        if repository is None or not access_token:
            return False

        owner, repo = repository
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {**GITHUB_API_HEADERS, "Authorization": f"Bearer {access_token}"}
        return self.can_fetch(api_url, headers=headers)

    def _extract_owner_and_repository(self, parsed_url: ParseResult) -> tuple[str, str] | None:
        parts = self.extract_repository_parts(parsed_url)
        if len(parts) < 2:
            return None
        return parts[0], parts[1]


GITHUB_PROVIDER = GitHubRepositoryVersionProvider()

__all__ = ["GITHUB_PROVIDER", "GitHubRepositoryVersionProvider"]
