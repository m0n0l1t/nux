from .auth import router as auth_router
from .proxy import router as proxy_router
from .wireguard import router as wireguard_router
from .invites import router as invites_router
from .admin import router as admin_router
from .billing import router as billing_router

__all__ = [
    "auth_router", 
    "proxy_router", 
    "wireguard_router", 
    "invites_router", 
    "admin_router", 
    "billing_router",
]
