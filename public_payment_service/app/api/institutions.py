from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Institution
from ..models.institution import InstitutionType
from ..schemas.institution import InstitutionCreate, InstitutionResponse, InstitutionApiKeyResponse
from ..security.auth import generate_api_key, hash_api_key

router = APIRouter()


@router.post("", response_model=InstitutionApiKeyResponse, status_code=status.HTTP_201_CREATED)
def register_institution(data: InstitutionCreate, db: Session = Depends(get_db)):
    """Register a new public institution."""
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    institution = Institution(
        name=data.name,
        name_local=data.name_local,
        institution_type=InstitutionType(data.institution_type.value),
        country_code=data.country_code,
        region=data.region,
        contact_email=data.contact_email,
        api_key_hash=api_key_hash,
        supported_currencies=",".join(data.supported_currencies),
        webhook_url=data.webhook_url,
    )

    db.add(institution)
    db.commit()
    db.refresh(institution)

    return InstitutionApiKeyResponse(
        institution_id=institution.id,
        api_key=api_key,
    )


@router.get("/me", response_model=InstitutionResponse)
def get_my_institution(
    db: Session = Depends(get_db),
    # Admin endpoint: in production, add admin auth here
):
    """Get institution profile (placeholder for admin access)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use API key authentication to access institution details",
    )
