from fastapi import APIRouter

from app.api.v1.admin.views import router

admin_router = APIRouter()
admin_router.include_router(router, tags=["Admin"])

__all__ = ["admin_router"]
