from fastapi import APIRouter

from .auth import router as auth_router
from .procurement import router as procurement_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(procurement_router)

__all__ = ["router"]
