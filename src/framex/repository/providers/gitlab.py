"""GitLab repository version provider."""

from urllib.parse import ParseResult, quote

from framex.config import settings

from .base import RepositoryVersionProvider

GITLAB_PRIMARY_HOST = "gitlab.com"
GITLAB_HOST_SUFFIX = ".gitlab.com"
GITLAB_RESERVED_PATH_MARKERS = {"-", "tree", "blob", "raw", "commits", "branches", "tags", "merge_requests"}


class GitLabRepositoryVersionProvider(RepositoryVersionProvider):
    """Resolve latest release versions for GitLab repositories."""

    name = "gitlab"

    def matches(self, parsed_url: ParseResult) -> bool:
        host = parsed_url.netloc.lower()
        return (
            host == GITLAB_PRIMARY_HOST
            or host.endswith(GITLAB_HOST_SUFFIX)
            or host in settings.repository.auth.gitlab.configured_hosts()
        )

    def get_latest_version(self, parsed_url: ParseResult) -> str | None:
        headers = settings.repository.auth.gitlab.build_headers_for_url(parsed_url.netloc, parsed_url.path) or None
        project_path = self._resolve_project_path(parsed_url, headers=headers, require_fetch=False)
        if project_path is None:
            return None

        api_url = self._build_release_api_url(parsed_url, project_path)
        payload = self.fetch_json(api_url, headers=headers)
        return self.extract_version(payload)

    def is_public_repository(self, parsed_url: ParseResult) -> bool | None:
        return self.can_fetch(self._build_repository_web_url(parsed_url), follow_redirects=False)

    def has_repository_access(self, parsed_url: ParseResult, access_token: str) -> bool:
        if not access_token:
            return False

        headers = {"Authorization": f"Bearer {access_token}"}
        return self._resolve_project_path(parsed_url, headers=headers, require_fetch=True) is not None

    def _resolve_project_path(
        self,
        parsed_url: ParseResult,
        headers: dict[str, str] | None = None,
        require_fetch: bool = True,
    ) -> str | None:
        candidates = self._iter_project_path_candidates(parsed_url)
        if not candidates:
            return None
        if not require_fetch and len(candidates) == 1:
            return candidates[0]

        for candidate in candidates:
            if self.can_fetch(self._build_project_api_url(parsed_url, candidate), headers=headers):
                return candidate
        return None

    def _iter_project_path_candidates(self, parsed_url: ParseResult) -> list[str]:
        parts = self.extract_repository_parts(parsed_url)
        if len(parts) < 2:
            return []

        marker_index = next((index for index, part in enumerate(parts) if part in GITLAB_RESERVED_PATH_MARKERS), None)
        max_length = marker_index if marker_index is not None else len(parts)
        if max_length < 2:
            return []

        return ["/".join(parts[:length]) for length in range(max_length, 1, -1)]

    def _build_project_api_url(self, parsed_url: ParseResult, project_path: str) -> str:
        project_id = quote(project_path, safe="")
        return f"{parsed_url.scheme}://{parsed_url.netloc}/api/v4/projects/{project_id}"

    def _build_release_api_url(self, parsed_url: ParseResult, project_path: str) -> str:
        project_id = quote(project_path, safe="")
        return f"{parsed_url.scheme}://{parsed_url.netloc}/api/v4/projects/{project_id}/releases/permalink/latest"

    def _build_repository_web_url(self, parsed_url: ParseResult) -> str:
        normalized = parsed_url._replace(params="", query="", fragment="")
        return normalized.geturl()


GITLAB_PROVIDER = GitLabRepositoryVersionProvider()

__all__ = ["GITLAB_PROVIDER", "GitLabRepositoryVersionProvider"]
