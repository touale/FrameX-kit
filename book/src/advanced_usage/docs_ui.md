# Docs UI & Operations

FrameX extends Swagger UI at `/docs` with plugin metadata and optional operations controls.

Use these features when authenticated docs users need to:

- see whether a plugin has a newer release
- view sanitized plugin configuration
- trigger a server-side HTTP action
- open a protected operations link

## Plugin Release Checks

Each plugin tag includes its current version and repository link from `PluginMetadata`.

When `PluginMetadata.url` points to a supported GitHub or GitLab repository, the docs UI checks:

```text
/docs/plugin-release?plugin=<plugin-id>
```

FrameX compares the running plugin version with the repository's latest release and shows an update indicator when a newer release exists.

For private repositories, configure a server-side repository token:

```toml
[repository.auth.github]
token = "<github-token>"

[repository.auth.gitlab]
token = "<gitlab-token>"
```

For GitLab installations with multiple hosts or groups, configure endpoint-specific tokens:

```toml
[[repository.auth.gitlab.endpoints]]
host = "gitlab.example.com"
path_prefix = "/team-a"
token = "<team-a-token>"
```

## Sanitized Plugin Config Views

When `auth.oauth` is configured, plugin tags include a config link:

```text
/docs/plugin-config?plugin=<plugin-id>
```

For private repository checks, set `auth.oauth.provider` to the matching repository provider, such as `"github"` or `"gitlab"`.

The config view is deliberately restricted:

- an OAuth session is always required
- the plugin must have a repository URL in its metadata
- public repositories are shown after the OAuth check
- private repositories require repository access for the logged-in OAuth user
- the user's OAuth provider must match the repository provider
- sensitive config values are masked before rendering

### Referenced Config Files

The config view can also render referenced YAML or TOML files. File access is limited to the current workspace and an explicit whitelist:

```toml
[docs]
embedded_config_file_whitelist = [
  "configs/*.yaml",
  "configs/*.toml",
]
```

Files outside the workspace, files not matched by the whitelist, and unsupported file types are not embedded.

## Action Buttons

Define optional Swagger UI controls with `docs.action_buttons`.

Example:

```toml
[[docs.action_buttons]]
title = "Run maintenance"
variant = "warning"
url = "https://ops.example.com/api/jobs"
method = "POST"
timeout = 30
requires_confirmation = true
confirmation_message = "Start the maintenance job?"
headers = { Authorization = "Bearer <server-side-token>" }
query = { source = "framex-docs" }
body_type = "json"
body = { job = "maintenance" }
response_open_url = "result.web_url"

[docs.action_buttons.auth]
type = "oauth"
allowed_usernames = ["operator-a", "operator-b"]

[[docs.action_buttons.inputs]]
name = "environment"
label = "Environment"
placeholder = "dev"
required = true
target = "body"
```

The browser receives only presentation metadata and input definitions. Target URLs, fixed headers, fixed bodies, configured passwords, username allowlists, and response paths stay on the server.

### Button Fields

Common fields are:

- `title`
- `variant`: `default`, `primary`, `success`, `warning`, or `danger`
- `method`: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, or `LINK`
- `url`
- `timeout`
- `requires_confirmation`
- `confirmation_message`
- `headers`
- `query`
- `body_type`: `json` or `form`
- `body`
- `inputs`
- `auth`
- `response_open_url`

Inputs have explicit destinations:

- `target = "query"` adds the value to query parameters
- `target = "body"` adds the value to the JSON or form body

## Action Authentication

Each action button supports one authentication mode.

No extra action auth:

```toml
[docs.action_buttons.auth]
type = "none"
```

Require an OAuth docs session:

```toml
[docs.action_buttons.auth]
type = "oauth"
allowed_usernames = ["*"]
```

Require a button-specific password:

```toml
[docs.action_buttons.auth]
type = "password"
password = "<server-side-password>"
```

The docs page itself can still be protected separately through `auth.rules`.

## Link Buttons

Use `method = "LINK"` to open an operations page:

```toml
[[docs.action_buttons]]
title = "View logs"
variant = "primary"
url = "https://ops.example.com/logs"
method = "LINK"

[docs.action_buttons.auth]
type = "oauth"
allowed_usernames = ["*"]
```

LINK URLs stay server-side until FrameX applies the button auth rules. LINK actions only accept explicit `http://` or `https://` URLs.

## Response-Driven Links

For non-LINK actions, `response_open_url` can select a URL from the remote JSON response:

```toml
response_open_url = "result.web_url"
```

FrameX preserves the raw response body shown in the docs UI and adds an `open_url` field only when the selected value is an explicit `http://` or `https://` URL.
