from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    applications,
    auth,
    conversation,
    match,
    partner_console,
    partners,
)

api_router = APIRouter()
api_router.include_router(match.router, prefix="/match", tags=["matching"])
api_router.include_router(partners.router, prefix="/partners", tags=["partners"])
api_router.include_router(
    conversation.router, prefix="/conversation", tags=["conversation"]
)
api_router.include_router(
    applications.router, prefix="/applications", tags=["applications"]
)
# The checklist is useful before an application exists — a citizen should be able to see
# what to bring while still deciding whether to apply.
api_router.include_router(
    applications.checklist_router, prefix="/documents", tags=["documents"]
)
# Role-gated consoles. The citizen surface above needs no login; these do.
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    partner_console.router, prefix="/partner", tags=["partner console"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
