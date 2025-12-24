# Authentication & Authorization

This section describes how to configure **documentation authentication** and **API authentication** in the system, including proxy-related authorization for remote services.

______________________________________________________________________

## 1) Documentation Authentication

The system supports HTTP Basic Authentication for built-in API documentation pages.

### Protected Endpoints

The following endpoints are protected when documentation authentication is enabled:

- `/docs`
- `/redoc`
- `/api/v1/openapi.json`

### Configuration

Documentation authentication is configured in `config.toml`:

```toml
[server]
docs_user = "admin"
docs_password = "admin"
```

**Default Behavior**

- **docs_user**

  - Default value: `admin`
  - If not specified, it defaults to `admin`

- **docs_password**

  - If not set or left empty, the system will automatically generate a UUID as the password
  - The generated password will be printed in the startup logs

**If authentication fails, the server returns:**

- **HTTP Status Code**: `401 Unauthorized`

______________________________________________________________________

## 2) API Authentication

The system supports API-level authentication using access keys.

### Enabling API Authentication

Configure the `[auth]` section in `config.toml`:

```toml
[auth]
general_auth_keys = ["your key"]
auth_urls = ["/api/v1/echo_model", "/api/v2/*"]
special_auth_keys = { "/api/v1/echo_model" = ["other key"] }
```

### Configuration Fields

**auth_urls**

- A list of API paths that require authentication
- Supports wildcard matching (e.g. `/api/v2/*`)
- Only URLs listed here are protected

**general_auth_keys**

- Common authentication keys for all URLs listed in `auth_urls`
- Can access any URL in `auth_urls`
- **Cannot** be used for URLs protected by `special_auth_keys`

**special_auth_keys**

- Per-URL authentication keys for sensitive APIs
- Have higher priority than `general_auth_keys`
- `general_auth_keys` are **not valid** for these URLs
- URLs defined here **must also exist** in `auth_urls`

______________________________________________________________________

## 3) Proxy Plugin Authentication

The proxy plugin allows forwarding APIs from third-party FastAPI or other FrameX services into the current instance.

### Configuration

```toml
[plugins.proxy.auth]
general_auth_keys = ["your key"]
auth_urls = ["/api/v1/proxy/remote", "/api/v1/echo_model"]
special_auth_keys = { "/api/v1/echo_model" = ["other key"] }
```
