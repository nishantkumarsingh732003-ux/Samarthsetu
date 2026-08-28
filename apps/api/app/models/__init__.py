"""Model package.

Importing this module registers every table on `Base.metadata`, which is what Alembic
autogenerate reflects against. Add new model modules here or they will be invisible to
migrations.
"""

from app.db.base import Base
from app.models.application import Application, Document
from app.models.audit import AuditLog, MatchRun
from app.models.citizen import Citizen, CitizenProfile, Consent
from app.models.enums import (
    ApplicationStatus,
    DocumentValidationStatus,
    Gender,
    GovIdType,
    PartnerType,
    RuleSeverity,
    SchemeFamily,
    SocialCategory,
)
from app.models.partner import ChannelPartner, PartnerSchemeAuthorisation
from app.models.scheme import Scheme, SchemeRule

__all__ = [
    "Base",
    "Application",
    "ApplicationStatus",
    "AuditLog",
    "ChannelPartner",
    "Citizen",
    "CitizenProfile",
    "Consent",
    "Document",
    "DocumentValidationStatus",
    "Gender",
    "GovIdType",
    "MatchRun",
    "PartnerSchemeAuthorisation",
    "PartnerType",
    "RuleSeverity",
    "Scheme",
    "SchemeFamily",
    "SchemeRule",
    "SocialCategory",
]
