import uuid

from fastapi import Cookie, Response
from itsdangerous import BadData, URLSafeTimedSerializer

from backend.core.config import settings


serializer = URLSafeTimedSerializer(
    settings.SESSION_SECRET_KEY,
    salt="decisionforge-browser-session",
)


def get_or_create_session_id(
    response: Response,
    session_id: str | None = Cookie(default=None),
) -> str:
    verified_session_id: str | None = None

    if session_id is not None:
        try:
            candidate = serializer.loads(
                session_id,
                max_age=settings.SESSION_MAX_AGE_SECONDS,
            )
            verified_session_id = str(uuid.UUID(candidate))
        except (BadData, ValueError, TypeError):
            verified_session_id = None

    if verified_session_id is None:
        verified_session_id = str(uuid.uuid4())

        response.set_cookie(
            key="session_id",
            value=serializer.dumps(verified_session_id),
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
            max_age=settings.SESSION_MAX_AGE_SECONDS,
        )

    return verified_session_id
