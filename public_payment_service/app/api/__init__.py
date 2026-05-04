from fastapi import APIRouter

from .payments import router as payments_router
from .institutions import router as institutions_router
from .health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(institutions_router, prefix="/institutions", tags=["institutions"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
