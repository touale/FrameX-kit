# Security & Authorization

This chapter shows how to configure authentication in FrameX.

In practice, there are three common cases:

- protect your own API routes
- protect `/docs` and `/api/v1/openapi.json` with OAuth login
- let the built-in `proxy` plugin call a protected upstream service

## Protect API Routes

Use `auth.rules` when you want specific API paths to require authentication.

```toml
[auth]
rules = {
  "/api/v1/base/version" = ["version-key"],
  "/api/v1/base/*" = ["service-key"]
}
```

With this config:

- `/api/v1/base/version` accepts `version-key`
- other routes under `/api/v1/base/*` accept `service-key`
- routes that do not match any rule stay public

Callers should send the key through the `Authorization` header.

```bash
curl -H 'Authorization: service-key' http://127.0.0.1:8080/api/v1/base/hello
```

The current implementation matches the header value directly. It does not add a `Bearer ` prefix automatically.

If you use both an exact rule and a wildcard rule, the exact rule wins. Among wildcard rules, the longest matching prefix wins.

## Protect Docs And OpenAPI With OAuth

Use `auth.oauth` when you want these routes to go through an OAuth login flow:

- `/docs`
- `/redoc`
- `/api/v1/openapi.json`

Minimal config:

```toml
[auth]
rules = {
  "/docs" = ["docs-key"],
  "/redoc" = ["docs-key"],
  "/api/v1/openapi.json" = ["docs-key"]
}

[auth.oauth]
base_url = "https://gitlab.example.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "/oauth/callback"
app_url = "http://127.0.0.1:8080"
```

With this config:

- FrameX mounts the callback route at `redirect_uri`
- `app_url + redirect_uri` becomes the callback URL sent to the OAuth provider
- visiting `/docs` without a valid login redirects the user to the provider login page
- after login, FrameX stores a `framex_token` cookie and redirects back to `/docs`

If you need to override provider endpoints directly, you can also set:

- `authorization_url`
- `token_url`
- `user_info_url`

If `auth.oauth` is not configured, this OAuth login flow is disabled.

## Let Proxy Call A Protected Upstream Service

If you use the built-in `proxy` plugin to connect to another protected service, configure auth under `plugins.proxy.auth.rules`.

```toml
load_builtin_plugins = ["proxy"]

[server]
enable_proxy = true

[plugins.proxy]
white_list = ["/api/v1/*"]

[plugins.proxy.proxy_urls."http://127.0.0.1:9000"]
enable = ["/api/v1/*"]
disable = []

[plugins.proxy.auth]
rules = {
  "/api/v1/openapi.json" = ["docs-key"],
  "/api/v1/base/version" = ["service-key"],
  "/api/v1/base/*" = ["service-key"]
}
```

Use this when the upstream service itself is protected and the local proxy still needs to:

- fetch the upstream `/api/v1/openapi.json`
- forward protected upstream API requests
- call the proxy-function endpoint used by advanced proxy invocation

One important detail from the current implementation: the proxy plugin uses only the first matched key for each protected path.

So if you configure multiple keys in one rule, the first one is the key that will actually be forwarded upstream.

For proxy-specific usage patterns, see [System Proxy Plugin (Fastapi API Compatibility)](./system_proxy_plugin.md).

## Rule Of Thumb

Use `auth.rules` to protect your own API routes.

Use `auth.oauth` when you want browser access to `/docs`, `/redoc`, or `/api/v1/openapi.json` to go through OAuth login.

Use `plugins.proxy.auth.rules` when your local service needs to call a protected upstream service through the built-in `proxy` plugin.
