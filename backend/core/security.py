import secrets

from fastapi import Header, HTTPException, status

from backend.core.config import settings


def require_generation_api_key(
    generation_api_key: str | None = Header(
        default=None,
        alias="X-Generation-Key",
    ),
) -> None:
    if (
        generation_api_key is None
        or not secrets.compare_digest(
            generation_api_key,
            settings.GENERATION_API_KEY,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Generation access denied",
        )
