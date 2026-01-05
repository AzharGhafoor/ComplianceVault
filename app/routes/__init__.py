from .auth import router as auth_router
from .organizations import router as organizations_router
from .controls import router as controls_router
from .evaluations import router as evaluations_router
from .dashboard import router as dashboard_router
from .history import router as history_router
from .bia import router as bia_router

__all__ = [
    "auth_router",
    "organizations_router",
    "controls_router",
    "evaluations_router",
    "dashboard_router",
    "history_router",
    "bia_router"
]
