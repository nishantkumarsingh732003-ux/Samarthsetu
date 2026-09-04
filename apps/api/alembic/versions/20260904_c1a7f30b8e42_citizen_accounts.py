"""citizen accounts: an optional login over the anonymous journey

Adds three things and removes nothing:

- `users.citizen_id` — the link from a login to a stored profile. NULL for the two
  console roles, and a CHECK makes that structural rather than a convention.
- `citizens.city` / `citizens.pincode` — the rest of the address the onboarding asks
  for. Routing still uses `district` and `geom`; these are for the citizen to read back.
- the enterprise half of `citizen_profiles` — business name, status, own contribution,
  loan required, and the timestamp that says onboarding finished. None of these columns
  is in the rule engine's contract, and none of them moves a verdict.

The anonymous path is untouched by design: `POST /match` still takes a profile in the
body and stores nothing, and an application is still trackable by reference number with
no account at all.

Revision ID: c1a7f30b8e42
Revises: 9604dc45523d
Create Date: 2026-09-04 17:10:22.114508

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'c1a7f30b8e42'
down_revision: str | None = '9604dc45523d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- citizens: the rest of the address ------------------------------------------
    op.add_column('citizens', sa.Column('city', sa.String(length=120), nullable=True))
    op.add_column('citizens', sa.Column('pincode', sa.String(length=6), nullable=True))
    op.create_check_constraint(
        op.f('ck_citizens_pincode_is_six_digits'),
        'citizens',
        "pincode IS NULL OR pincode ~ '^[1-9][0-9]{5}$'",
    )

    # --- citizen_profiles: collected by onboarding, not read by the engine -----------
    op.add_column(
        'citizen_profiles', sa.Column('business_name', sa.String(length=160), nullable=True)
    )
    op.add_column('citizen_profiles', sa.Column('business_description', sa.Text(), nullable=True))
    op.add_column(
        'citizen_profiles', sa.Column('business_status', sa.String(length=16), nullable=True)
    )
    op.add_column(
        'citizen_profiles', sa.Column('own_contribution', sa.Numeric(precision=14, scale=2), nullable=True)
    )
    op.add_column(
        'citizen_profiles', sa.Column('loan_required', sa.Numeric(precision=14, scale=2), nullable=True)
    )
    op.add_column(
        'citizen_profiles', sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    op.create_check_constraint(
        op.f('ck_citizen_profiles_own_contribution_non_negative'),
        'citizen_profiles',
        'own_contribution IS NULL OR own_contribution >= 0',
    )
    op.create_check_constraint(
        op.f('ck_citizen_profiles_loan_required_non_negative'),
        'citizen_profiles',
        'loan_required IS NULL OR loan_required >= 0',
    )
    # The share a citizen brings cannot exceed the project it is brought to. The upper
    # bound on what may be *borrowed* is a scheme rule with provenance
    # (`max_funding_pct`), not a number frozen into a constraint here.
    op.create_check_constraint(
        op.f('ck_citizen_profiles_own_contribution_within_project_cost'),
        'citizen_profiles',
        'own_contribution IS NULL OR project_cost IS NULL OR own_contribution <= project_cost',
    )
    op.create_check_constraint(
        op.f('ck_citizen_profiles_business_status_is_known'),
        'citizen_profiles',
        "business_status IS NULL OR business_status IN ('NEW', 'EXISTING')",
    )

    # --- users: the link to a stored profile -----------------------------------------
    op.add_column('users', sa.Column('citizen_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f('fk_users_citizen_id_citizens'),
        'users',
        'citizens',
        ['citizen_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    # One login per citizen record. Two accounts sharing a profile would make "whose
    # data is this" unanswerable, which is the wrong property for a consent record.
    op.create_unique_constraint(op.f('uq_users_citizen_id'), 'users', ['citizen_id'])
    op.create_check_constraint(
        op.f('ck_users_only_a_citizen_role_has_a_citizen'),
        'users',
        "citizen_id IS NULL OR role = 'CITIZEN'",
    )


def downgrade() -> None:
    op.drop_constraint(op.f('ck_users_only_a_citizen_role_has_a_citizen'), 'users', type_='check')
    op.drop_constraint(op.f('uq_users_citizen_id'), 'users', type_='unique')
    op.drop_constraint(op.f('fk_users_citizen_id_citizens'), 'users', type_='foreignkey')
    op.drop_column('users', 'citizen_id')

    op.drop_constraint(op.f('ck_citizen_profiles_business_status_is_known'), 'citizen_profiles', type_='check')
    op.drop_constraint(
        op.f('ck_citizen_profiles_own_contribution_within_project_cost'),
        'citizen_profiles',
        type_='check',
    )
    op.drop_constraint(op.f('ck_citizen_profiles_loan_required_non_negative'), 'citizen_profiles', type_='check')
    op.drop_constraint(op.f('ck_citizen_profiles_own_contribution_non_negative'), 'citizen_profiles', type_='check')
    op.drop_column('citizen_profiles', 'completed_at')
    op.drop_column('citizen_profiles', 'loan_required')
    op.drop_column('citizen_profiles', 'own_contribution')
    op.drop_column('citizen_profiles', 'business_status')
    op.drop_column('citizen_profiles', 'business_description')
    op.drop_column('citizen_profiles', 'business_name')

    op.drop_constraint(op.f('ck_citizens_pincode_is_six_digits'), 'citizens', type_='check')
    op.drop_column('citizens', 'pincode')
    op.drop_column('citizens', 'city')
