"""Shared FastAPI dependencies.

Using `Annotated` aliases rather than `Depends()` in argument defaults keeps route
signatures readable and avoids the function-call-in-default pattern that linters flag.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
