import uuid

from fastapi import Cookie, Response


def get_or_create_session_id(
    response: Response,
    session_id: str | None = Cookie(default=None),
) -> str:
    if session_id is None:
        session_id = str(uuid.uuid4())

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
        )

    return session_id