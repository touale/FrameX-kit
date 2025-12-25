# Authentication & Authorization

This section describes how to configure **documentation authentication** and **API authentication** in the system, including proxy-related authorization for remote services.

______________________________________________________________________

## 1) Documentation Authentication

The system supports **HTTP Basic Authentication** for built-in API documentation pages.

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

### Default Behavior

- **docs_user**

  - Default value: `admin`

- **docs_password**

  - If not set or left empty, the system uses the default password: `admin`

### Authentication Failure

- **HTTP Status Code**: `401 Unauthorized`

______________________________________________________________________

## 2) API Authentication (Rules-Based)

The system supports API-level authentication using **access keys**, configured through a
**rules-based authorization model**.

### Overview

- Authentication is defined by a single `rules` mapping
- Each rule maps an **API path** to a list of **allowed access keys**
- Only URLs explicitly defined in rules are protected
- URL matching supports:
  - Exact match
  - Prefix wildcard match using `/*`
- For wildcard rules, the longest matching prefix wins

### Configuration

```toml
[auth]
rules = {
  "/api/v1/echo_model" = ["key-1", "key-2"],
  "/api/v2/*" = ["key-3"]
}
```

### Runtime Behavior

- If a request URL does not match any rule, authentication is not required
- If a request URL matches a rule, a valid access key must be provided
- Missing or invalid keys result in:
  - **HTTP Status Code**: `401 Unauthorized`

______________________________________________________________________

## 3) Proxy Plugin Authentication

The proxy plugin uses the same rules-based authentication mechanism
as standard API authentication.

### Configuration

```toml
[plugins.proxy.auth]
rules = {
  "/api/v1/proxy/remote" = ["proxy-key"],
  "/api/v1/echo_model" = ["echo-key"]
}
```
