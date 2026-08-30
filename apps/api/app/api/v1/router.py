from fastapi import APIRouter

from app.api.v1.routes import applications, conversation, match, partners

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
