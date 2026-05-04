from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InstitutionTypeEnum(str, Enum):
    GOVERNMENT = "government"
    MUNICIPALITY = "municipality"
    PUBLIC_UTILITY = "public_utility"
    EDUCATIONAL = "educational"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class InstitutionCreate(BaseModel):
    name: str
    name_local: Optional[str] = None
    institution_type: InstitutionTypeEnum
    country_code: str
    region: Optional[str] = None
    contact_email: EmailStr
    supported_currencies: List[str] = ["USD"]
    webhook_url: Optional[str] = None

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if len(v) != 2:
            raise ValueError("Country code must be ISO 3166-1 alpha-2")
        return v.upper()

    @field_validator("supported_currencies")
    @classmethod
    def validate_currencies(cls, v: List[str]) -> List[str]:
        return [c.upper() for c in v if len(c) == 3]


class InstitutionResponse(BaseModel):
    id: str
    name: str
    name_local: Optional[str] = None
    institution_type: InstitutionTypeEnum
    country_code: str
    region: Optional[str] = None
    contact_email: str
    is_active: bool
    supported_currencies: str
    webhook_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InstitutionApiKeyResponse(BaseModel):
    institution_id: str
    api_key: str  # shown only once on creation
    message: str = "Store this API key securely. It will not be shown again."
