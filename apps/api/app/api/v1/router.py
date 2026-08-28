from fastapi import APIRouter

# Versioned API surface. Routers are registered here as each phase lands them:
# Phase 2 -> /match, /partners.  Phase 3 -> /conversation.  Phase 5 -> /applications.
api_router = APIRouter()
