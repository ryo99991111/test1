import hashlib
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Institution
from ..config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def generate_api_key() -> str:
    raw = secrets.token_urlsafe(32)
    return f"{settings.api_key_prefix}{raw}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_current_institution(
    api_key: str = Security(API_KEY_HEADER),
    db: Session = Depends(get_db),
) -> Institution:
    key_hash = hash_api_key(api_key)
    institution = (
        db.query(Institution)
        .filter(Institution.api_key_hash == key_hash, Institution.is_active == True)
        .first()
    )
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return institution
