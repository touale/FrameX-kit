"""Repository hosting providers used by version lookup."""

from .base import RepositoryVersionProvider
from .github import GITHUB_PROVIDER
from .gitlab import GITLAB_PROVIDER

REPOSITORY_VERSION_PROVIDERS: tuple[RepositoryVersionProvider, ...] = (
    GITHUB_PROVIDER,
    GITLAB_PROVIDER,
)

__all__ = [
    "GITHUB_PROVIDER",
    "GITLAB_PROVIDER",
    "REPOSITORY_VERSION_PROVIDERS",
    "RepositoryVersionProvider",
]
