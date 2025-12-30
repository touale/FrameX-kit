from datetime import UTC, datetime, timedelta

import httpx
import jwt
from fastapi import Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader
from starlette.requests import Request

from framex.config import settings
from framex.consts import DOCS_URL

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def create_jwt(payload: dict) -> str:
    if not settings.auth.oauth:
        raise RuntimeError("OAuth not configured")

    now_utc = datetime.now(UTC)

    payload.update(
        {
            "iat": int(now_utc.timestamp()),
            "exp": int((now_utc + timedelta(hours=24)).timestamp()),
        }
    )
    return jwt.encode(payload, settings.auth.oauth.jwt_secret, algorithm=settings.auth.oauth.jwt_algorithm)


def auth_jwt(request: Request) -> bool:
    if not settings.auth.oauth:
        return False

    token = request.cookies.get("token")
    if not token:
        return False

    try:
        jwt.decode(
            token,
            settings.auth.oauth.jwt_secret,
            algorithms=[settings.auth.oauth.jwt_algorithm],
        )
        return True
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
        return False


def authenticate(request: Request, api_key: str | None = Depends(api_key_header)) -> None:
    if settings.auth.oauth:
        if token := request.cookies.get("token"):
            try:
                jwt.decode(
                    token,
                    settings.auth.oauth.jwt_secret,
                    algorithms=[settings.auth.oauth.jwt_algorithm],
                )
                return

            except Exception as e:
                from framex.log import logger

                logger.warning(f"JWT decode failed: {e}")

        if api_key and api_key in (settings.auth.get_auth_keys(request.url.path) or []):
            return

        raise HTTPException(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            headers={
                "Location": (
                    f"{settings.auth.oauth.authorization_url}"
                    f"?client_id={settings.auth.oauth.client_id}"
                    "&response_type=code"
                    f"&redirect_uri={settings.auth.oauth.call_back_url}"
                    "&scope=read_user"
                )
            },
        )


async def oauth_callback(code: str) -> Response:
    if not settings.auth.oauth:  # pragma: no cover
        raise RuntimeError("OAuth not configured")

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
    }

    res = RedirectResponse(url=DOCS_URL, status_code=status.HTTP_302_FOUND)
    res.set_cookie(
        "token",
        create_jwt(user_info),
        httponly=True,
        samesite="lax",
    )
    return res
