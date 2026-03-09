from aiogram import Router

from .start import router as start_router
from .registration import router as reg_router
from .profile import router as profile_router
from .browse import router as browse_router
from .matches import router as matches_router
from .chat import router as chat_router
from .settings import router as settings_router
from .admin import router as admin_router

main_router = Router()
main_router.include_routers(
    start_router,
    reg_router,
    profile_router,
    browse_router,
    matches_router,
    chat_router,
    settings_router,
    admin_router,
)
