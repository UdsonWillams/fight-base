from fastapi import APIRouter

from app.api.v1.auth.views import router as auth_router
from app.api.v1.fighters.views import router as fighters_router
from app.api.v1.products.views import router as products_router
from app.api.v1.simulations.views import router as simulations_router
from app.api.v1.users.views import router as users_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router, tags=["Auth"])
v1_router.include_router(users_router, tags=["Users"])
v1_router.include_router(products_router, tags=["Products"])

# FightBase endpoints
v1_router.include_router(fighters_router)
v1_router.include_router(simulations_router)
