from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
import jwt
from fastapi import Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader
from starlette.requests import Request

from framex.config import settings
from framex.consts import AUTH_COOKIE_NAME, DOCS_URL, OAUTH_STATE_COOKIE_NAME

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
SESSION_LIFETIME = timedelta(hours=24)
OAUTH_STATE_LIFETIME = timedelta(minutes=10)
OAUTH_REDIRECT_MAX_LENGTH = 2048
_AUTH_SESSIONS: dict[str, dict[str, Any]] = {}


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _purge_expired_sessions(now_utc: datetime | None = None) -> None:
    current = now_utc or _now_utc()
    expired_session_ids = [
        session_id for session_id, payload in _AUTH_SESSIONS.items() if payload.get("expires_at", current) <= current
    ]
    for session_id in expired_session_ids:
        _AUTH_SESSIONS.pop(session_id, None)


def create_jwt(payload: dict[str, Any]) -> str:
    if not settings.auth.oauth:
        raise RuntimeError("OAuth not configured")

    now_utc = _now_utc()
    token_payload = {
        **payload,
        "iat": int(now_utc.timestamp()),
        "exp": int((now_utc + SESSION_LIFETIME).timestamp()),
    }
    return jwt.encode(token_payload, settings.auth.oauth.jwt_secret, algorithm=settings.auth.oauth.jwt_algorithm)


def create_auth_session(session_payload: dict[str, Any]) -> str:
    now_utc = _now_utc()
    expires_at = now_utc + SESSION_LIFETIME
    session_id = token_urlsafe(32)
    _AUTH_SESSIONS[session_id] = {
        **session_payload,
        "expires_at": expires_at,
    }
    _purge_expired_sessions(now_utc)
    return session_id


def decode_auth_token(token: str | None) -> dict[str, Any] | None:
    if not settings.auth.oauth or not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.auth.oauth.jwt_secret,
            algorithms=[settings.auth.oauth.jwt_algorithm],
        )
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return None

    if not isinstance(payload, dict):
        return None

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return None

    now_utc = _now_utc()
    _purge_expired_sessions(now_utc)
    session_payload = _AUTH_SESSIONS.get(session_id)
    if session_payload is None:
        return None

    expires_at = session_payload.get("expires_at")
    if not isinstance(expires_at, datetime) or expires_at <= now_utc:
        _AUTH_SESSIONS.pop(session_id, None)
        return None

    return {
        **payload,
        **{key: value for key, value in session_payload.items() if key != "expires_at"},
    }


def get_auth_payload(request: Request) -> dict[str, Any] | None:
    return decode_auth_token(request.cookies.get(AUTH_COOKIE_NAME))


def auth_jwt(request: Request) -> bool:
    return get_auth_payload(request) is not None


def _get_post_auth_redirect_url(state: str | None) -> str:
    if not state or len(state) > OAUTH_REDIRECT_MAX_LENGTH:
        return DOCS_URL

    parsed = urlsplit(state)
    if parsed.scheme or parsed.netloc or not state.startswith("/") or state.startswith("//"):
        return DOCS_URL
    return state


def _get_canonical_oauth_request_url(request: Request) -> str | None:
    oauth = settings.auth.oauth
    if oauth is None:
        return None

    app_url = urlsplit(oauth.app_url)
    request_url = urlsplit(str(request.url))
    if not app_url.scheme or not app_url.netloc:
        return None
    if (app_url.scheme.lower(), app_url.netloc.lower()) == (
        request_url.scheme.lower(),
        request_url.netloc.lower(),
    ):
        return None

    base_path = app_url.path.rstrip("/")
    canonical_path = f"{base_path}{request_url.path}" or "/"
    return urlunsplit(
        (
            app_url.scheme,
            app_url.netloc,
            canonical_path,
            request_url.query,
            "",
        )
    )


def create_oauth_redirect(post_auth_redirect: str | None = None) -> tuple[str, str]:
    oauth = settings.auth.oauth
    if oauth is None:
        raise RuntimeError("OAuth not configured")

    state = token_urlsafe(32)
    state_cookie = jwt.encode(
        {
            "state": state,
            "redirect_url": _get_post_auth_redirect_url(post_auth_redirect),
            "exp": _now_utc() + OAUTH_STATE_LIFETIME,
        },
        oauth.jwt_secret,
        algorithm=oauth.jwt_algorithm,
    )
    cookie_response = Response()
    cookie_response.set_cookie(
        OAUTH_STATE_COOKIE_NAME,
        state_cookie,
        max_age=int(OAUTH_STATE_LIFETIME.total_seconds()),
        path="/",
        secure=oauth.use_secure_cookie,
        httponly=True,
        samesite="lax",
    )
    query = urlencode(
        {
            "client_id": oauth.client_id,
            "response_type": "code",
            "redirect_uri": oauth.call_back_url,
            "scope": "read_user read_api",
            "state": state,
        }
    )
    return (
        f"{oauth.authorization_url}?{query}",
        cookie_response.headers["set-cookie"],
    )


def _consume_oauth_state(request: Request, state: str | None) -> str:
    oauth = settings.auth.oauth
    state_cookie = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if oauth is None or not state or not state_cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")

    try:
        state_payload = jwt.decode(state_cookie, oauth.jwt_secret, algorithms=[oauth.jwt_algorithm])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        ) from None

    redirect_url = state_payload.get("redirect_url")
    if state_payload.get("state") != state or not isinstance(redirect_url, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")
    return redirect_url


def authenticate(request: Request, api_key: str | None = Depends(api_key_header)) -> None:
    if settings.auth.oauth:
        if get_auth_payload(request) is not None:
            return

        if api_key and api_key in (settings.auth.get_auth_keys(request.url.path) or []):
            return

        if canonical_url := _get_canonical_oauth_request_url(request):
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                headers={"Location": canonical_url},
            )

        redirect_path = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
        redirect_url, state_cookie = create_oauth_redirect(redirect_path)
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={
                "Location": redirect_url,
                "Set-Cookie": state_cookie,
            },
        )


async def oauth_callback(request: Request, code: str, state: str | None = None) -> Response:
    if not settings.auth.oauth:  # pragma: no cover
        raise RuntimeError("OAuth not configured")

    redirect_url = _consume_oauth_state(request, state)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            settings.auth.oauth.token_url,
            data={
                "client_id": settings.auth.oauth.client_id,
                "client_secret": settings.auth.oauth.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.auth.oauth.call_back_url,
            },
        )
        resp.raise_for_status()
        token_resp = resp.json()

        if not (auth_token := token_resp.get("access_token")):  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitLab token exchange failed")

        resp = await client.get(
            settings.auth.oauth.user_info_url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        user_resp = resp.json()

    if not (username := user_resp.get("username")):  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get GitLab user")

    user_info = {
        "message": f"Welcome {username}",
        "username": username,
        "email": user_resp.get("email"),
        "oauth_provider": settings.auth.oauth.provider,
        "oauth_access_token": auth_token,
    }
    session_id = create_auth_session(user_info)

    res = RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_302_FOUND,
    )
    res.set_cookie(
        AUTH_COOKIE_NAME,
        create_jwt(
            {
                "message": user_info["message"],
                "username": username,
                "email": user_info["email"],
                "oauth_provider": settings.auth.oauth.provider,
                "session_id": session_id,
            }
        ),
        httponly=True,
        samesite="lax",
    )
    res.delete_cookie(OAUTH_STATE_COOKIE_NAME)
    return res
