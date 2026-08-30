"""Enumerations backed by native PostgreSQL enum types.

Values are stored as the member *name* (see `native_enum` usage in the models), so
renaming a member is a migration, not a silent data change.
"""

from enum import StrEnum


class SchemeFamily(StrEnum):
    """The three scheme families the problem statement requires us to distinguish."""

    MICRO_FINANCE = "MICRO_FINANCE"
    TERM_LOAN = "TERM_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"


class RuleSeverity(StrEnum):
    """HARD_BLOCK makes a scheme INELIGIBLE. SOFT_WARN only annotates the match."""

    HARD_BLOCK = "HARD_BLOCK"
    SOFT_WARN = "SOFT_WARN"


class PartnerType(StrEnum):
    """Channel Partner categories in the Channel Finance System."""

    SCA = "SCA"  # State Channelising Agency
    PSB = "PSB"  # Public Sector Bank
    RRB = "RRB"  # Regional Rural Bank
    NBFC_MFI = "NBFC_MFI"


class ApplicationStatus(StrEnum):
    """Application lifecycle. Transitions are recorded in `applications.status_history`."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PARTNER_ACKNOWLEDGED = "PARTNER_ACKNOWLEDGED"
    DOCS_REQUESTED = "DOCS_REQUESTED"
    UNDER_APPRAISAL = "UNDER_APPRAISAL"
    SANCTIONED = "SANCTIONED"
    DISBURSED = "DISBURSED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class DocumentValidationStatus(StrEnum):
    """OCR pre-validation outcome. WARNING never blocks submission (Phase 5 rule)."""

    PENDING = "PENDING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"


class GovIdType(StrEnum):
    """Type of government ID presented. The number itself is never stored in full."""

    AADHAAR = "AADHAAR"
    PAN = "PAN"
    VOTER_ID = "VOTER_ID"
    OTHER = "OTHER"


class SocialCategory(StrEnum):
    SC = "SC"
    ST = "ST"
    OBC = "OBC"
    GENERAL = "GENERAL"


class Gender(StrEnum):
    FEMALE = "FEMALE"
    MALE = "MALE"
    OTHER = "OTHER"
    UNDISCLOSED = "UNDISCLOSED"


class UserRole(StrEnum):
    """Console roles. The citizen journey needs no login — a reference number is the key."""

    CITIZEN = "CITIZEN"
    PARTNER = "PARTNER"
    ADMIN = "ADMIN"
