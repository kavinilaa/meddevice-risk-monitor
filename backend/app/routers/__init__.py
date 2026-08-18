from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.predictions import router as predictions_router
from app.routers.metadata import router as metadata_router
from app.routers.admin import router as admin_router
from app.routers.health import router as health_router

__all__ = [
    "auth_router",
    "users_router",
    "predictions_router",
    "metadata_router",
    "admin_router",
    "health_router"
]
