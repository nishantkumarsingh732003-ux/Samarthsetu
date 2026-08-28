# Data model (Phase 0)

11 tables, 127 columns, 11 foreign keys, 21 indexes, 12 CHECK constraints.
Defined in `apps/api/app/models/`, migrated by `apps/api/alembic/versions/20260828_0001_initial_schema.py`.

```mermaid
erDiagram
    consents      ||--o{ citizens                      : "authorises storage of"
    citizens      ||--o| citizen_profiles              : "has"
    citizens      ||--o{ match_runs                    : "generated"
    citizens      ||--o{ applications                  : "files"
    schemes       ||--o{ scheme_rules                  : "is governed by"
    schemes       ||--o{ partner_scheme_authorisations : "is processed under"
    channel_partners ||--o{ partner_scheme_authorisations : "is authorised for"
    schemes       ||--o{ applications                  : "applied for"
    channel_partners ||--o{ applications               : "routed to"
    match_runs    ||--o{ applications                  : "justifies"
    applications  ||--o{ documents                     : "supported by"

    consents {
        uuid id PK
        string purpose
        timestamptz granted_at
        timestamptz revoked_at
        string policy_version
        string ip_hash "salted"
    }
    citizens {
        uuid id PK
        enum gov_id_type
        string gov_id_last4 "CHECK ^[0-9]{4}$"
        string gov_id_hash "salted sha256, unique"
        uuid consent_id FK "NOT NULL"
        string preferred_language
        string district
        string state
        geography geom "POINT 4326, GIST"
    }
    citizen_profiles {
        uuid id PK
        uuid citizen_id FK "unique"
        numeric annual_family_income
        enum category
        enum gender
        smallint age
        string occupation_type
        string education_level
        numeric existing_loans
        numeric project_cost
        string project_sector
        bool is_pwd
        bool is_safai_karamchari
    }
    schemes {
        uuid id PK
        string code UK
        string official_name "verbatim, never translated"
        jsonb name_i18n
        enum family "MICRO_FINANCE|TERM_LOAN|EDUCATION_LOAN"
        numeric max_amount
        numeric max_funding_pct
        numeric interest_rate_min
        numeric interest_rate_max
        string source_url "provenance"
        string circular_ref "provenance"
        date effective_from "provenance"
        date last_verified_on "provenance"
        bool needs_verification
        vector embedding "768, pgvector"
    }
    scheme_rules {
        uuid id PK
        uuid scheme_id FK
        string rule_id "e.g. MF_INCOME_CEILING"
        jsonb expression
        enum severity "HARD_BLOCK|SOFT_WARN"
        jsonb message_i18n
        string suggest_instead "anti-misrouting redirect"
    }
    channel_partners {
        uuid id PK
        string name
        enum type "SCA|PSB|RRB|NBFC_MFI"
        string ifsc "CHECK IFSC format"
        string district
        string state
        string pincode "CHECK ^[0-9]{6}$"
        geography geom "POINT 4326, GIST"
        bool is_active
    }
    partner_scheme_authorisations {
        uuid id PK
        uuid partner_id FK
        uuid scheme_id FK
        numeric min_ticket
        numeric max_ticket
        bool is_currently_accepting
        int avg_turnaround_days
        int active_load "0-100"
        array service_districts "GIN"
    }
    match_runs {
        uuid id PK
        uuid citizen_id FK
        jsonb input_snapshot "NOT NULL"
        string engine_version "NOT NULL"
        jsonb results "NOT NULL"
        timestamptz at
    }
    applications {
        uuid id PK
        uuid citizen_id FK
        uuid scheme_id FK
        uuid partner_id FK
        uuid match_run_id FK "reproducibility"
        string engine_version "snapshot"
        enum status
        numeric amount_requested
        string reference_no UK "SETU-2026-MH-000431"
        jsonb status_history
    }
    documents {
        uuid id PK
        uuid application_id FK
        string doc_type
        string storage_key
        jsonb ocr_extract "IDs already masked"
        enum validation_status
        bool redaction_applied
    }
    audit_log {
        uuid id PK
        string actor
        string action
        string entity
        string entity_id
        timestamptz at
        jsonb meta
    }
```

## Why the schema looks like this

**Consent is structural, not procedural.** `citizens.consent_id` is `NOT NULL` with
`ON DELETE RESTRICT`. There is no code path that stores a citizen without a consent row,
because the database will not accept one.

**A full government ID is unstorable.** The column is `VARCHAR(4)` *and* carries a
`CHECK (~ '^[0-9]{4}$')`. Even a bug that tries to write a full Aadhaar number fails at
the database. Only the last 4 digits plus a salted hash are retained (DPDP Act 2023).

**Provenance is columns, not comments.** `schemes` carries `source_url`, `circular_ref`,
`effective_from`, `last_verified_on`, and `needs_verification`. A figure the problem
statement does not state cannot be recorded as though it were sourced.

**`match_runs` is the governance artefact.** Every eligibility decision writes the input
snapshot, the engine version, and the full result set. Rows are never deleted, and
`applications` snapshots `match_run_id` + `engine_version`, so a sanction can be replayed
against the exact rules that were live when the citizen applied — even after the YAML
changes. This is the evidence behind "the LLM never decides eligibility".

**Authorisation is a table, not a flag.** A partner is routable for a scheme only if a
`partner_scheme_authorisations` row exists. A missing row is what the routing engine
reports as `why_not` — the anti-misrouting feature — and the GIN index on
`service_districts` plus the GIST index on `channel_partners.geom` make that filter and
the distance sort fast enough to run on every request.

## Enum types

| Type | Values |
|---|---|
| `scheme_family` | MICRO_FINANCE, TERM_LOAN, EDUCATION_LOAN |
| `rule_severity` | HARD_BLOCK, SOFT_WARN |
| `partner_type` | SCA, PSB, RRB, NBFC_MFI |
| `application_status` | DRAFT, SUBMITTED, PARTNER_ACKNOWLEDGED, DOCS_REQUESTED, UNDER_APPRAISAL, SANCTIONED, DISBURSED, REJECTED, WITHDRAWN |
| `document_validation_status` | PENDING, PASSED, WARNING, FAILED |
| `gov_id_type` | AADHAAR, PAN, VOTER_ID, OTHER |
| `social_category` | SC, ST, OBC, GENERAL |
| `gender` | FEMALE, MALE, OTHER, UNDISCLOSED |
