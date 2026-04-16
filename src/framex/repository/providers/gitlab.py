"""GitLab repository version provider."""

from urllib.parse import ParseResult, quote

from framex.config import settings

from .base import RepositoryVersionProvider

GITLAB_PRIMARY_HOST = "gitlab.com"
GITLAB_HOST_SUFFIX = ".gitlab.com"


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
        project_path = self._extract_project_path(parsed_url)
        if project_path is None:
            return None

        project_id = quote(project_path, safe="")
        api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/api/v4/projects/{project_id}/releases/permalink/latest"
        headers = settings.repository.auth.gitlab.build_headers_for_url(parsed_url.netloc, parsed_url.path) or None
        payload = self.fetch_json(api_url, headers=headers)
        return self.extract_version(payload)

    def _extract_project_path(self, parsed_url: ParseResult) -> str | None:
        parts = self.extract_repository_parts(parsed_url)
        if len(parts) < 2:
            return None
        return "/".join(parts)


GITLAB_PROVIDER = GitLabRepositoryVersionProvider()

__all__ = ["GITLAB_PROVIDER", "GitLabRepositoryVersionProvider"]
