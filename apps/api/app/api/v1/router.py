from fastapi import APIRouter

from app.api.v1.routes import conversation, match, partners

# Versioned API surface. Routers are registered here as each phase lands them:
# Phase 5 -> /applications, /documents.
api_router = APIRouter()
api_router.include_router(match.router, prefix="/match", tags=["matching"])
api_router.include_router(partners.router, prefix="/partners", tags=["partners"])
api_router.include_router(
    conversation.router, prefix="/conversation", tags=["conversation"]
)
