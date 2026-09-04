from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    applications,
    auth,
    citizen,
    conversation,
    coverage,
    match,
    partner_console,
    partners,
    schemes,
    webhook,
)

api_router = APIRouter()
api_router.include_router(match.router, prefix="/match", tags=["matching"])
# The published catalogue. No login: a citizen should be able to read the terms before
# deciding whether to hand over any data at all.
api_router.include_router(schemes.router, prefix="/schemes", tags=["schemes"])
# Included BEFORE `partners` and at the same prefix, because `/partners/{partner_id}`
# would otherwise match `/partners/coverage` and fail to parse it as a UUID.
api_router.include_router(coverage.router, prefix="/partners", tags=["partners"])
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
# Sign-in, shared by every role. The citizen surfaces above need no login.
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# The optional citizen account. It adds persistence — a saved profile and a list of your
# own applications — and grants nothing a signed-out citizen cannot already do.
api_router.include_router(citizen.router, prefix="/citizen", tags=["citizen"])
api_router.include_router(
    partner_console.router, prefix="/partner", tags=["partner console"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# The feature-phone entry point. Same orchestrator, plain-text rendering.
api_router.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
