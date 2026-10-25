
"""add indexes and numeric fields
Revision ID: fd74f99fede4
Revises: e2c0d437cebf
Create Date: 2026-09-22 20:34:51.028686
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision: str = "fd74f99fede4"
down_revision: Union[str, Sequence[str], None] = "e2c0d437cebf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    """Upgrade schema."""
    # ============================================================
    # 1. commission_configs
    # ============================================================
    with op.batch_alter_table(
        "commission_configs",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "vat",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=False,
        )
    # ============================================================
    # 2. insurance_type_commissions
    # ============================================================
    with op.batch_alter_table(
        "insurance_type_commissions",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "normal_commission",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "mortgage_commission",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "issuance_percent",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=False,
        )
    # ============================================================
    # 3. marketer_commission_rules
    # ============================================================
    with op.batch_alter_table(
        "marketer_commission_rules",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "commission_percent",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=False,
        )
    # ============================================================
    # 4. marketers
    # ============================================================
    with op.batch_alter_table(
        "marketers",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "third_party_commission",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "other_commission",
            existing_type=sa.FLOAT(),
            type_=sa.Numeric(precision=5, scale=2),
            existing_nullable=False,
        )
    # ============================================================
    # 5. policies
    #
    # customer_id already has a FK to customers.id.
    # The model now requires ON DELETE RESTRICT.
    #
    # SQLite requires batch mode for this structural change.
    # A naming convention gives the existing unnamed FK a
    # predictable name during reflection.
    # ============================================================
    with op.batch_alter_table(
        "policies",
        schema=None,
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
        },
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_policies_customer_id_customers",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_policies_customer_id_customers",
            "customers",
            ["customer_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    # ============================================================
    # 6. Indexes
    # ============================================================
    op.create_index(
        op.f("ix_collections_collection_date"),
        "collections",
        ["collection_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_collections_due_date"),
        "collections",
        ["due_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_type_commissions_effective_date"),
        "insurance_type_commissions",
        ["effective_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_type_commissions_insurance_type_id"),
        "insurance_type_commissions",
        ["insurance_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_insurance_type_mappings_insurance_type_id"),
        "insurance_type_mappings",
        ["insurance_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marketer_commission_rules_customer_id"),
        "marketer_commission_rules",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marketer_commission_rules_insurance_type_id"),
        "marketer_commission_rules",
        ["insurance_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marketer_commission_rules_marketer_id"),
        "marketer_commission_rules",
        ["marketer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_marketer_commission_rules_policy_id"),
        "marketer_commission_rules",
        ["policy_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_customer_id"),
        "policies",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_end_date"),
        "policies",
        ["end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_insurance_company_id"),
        "policies",
        ["insurance_company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_insurance_type_id"),
        "policies",
        ["insurance_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_issue_date"),
        "policies",
        ["issue_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_marketer_id"),
        "policies",
        ["marketer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_policies_start_date"),
        "policies",
        ["start_date"],
        unique=False,
    )
def downgrade() -> None:
    """Downgrade schema."""
    # ============================================================
    # Remove indexes
    # ============================================================
    op.drop_index(
        op.f("ix_policies_start_date"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_marketer_id"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_issue_date"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_insurance_type_id"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_insurance_company_id"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_end_date"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_policies_customer_id"),
        table_name="policies",
    )
    op.drop_index(
        op.f("ix_marketer_commission_rules_policy_id"),
        table_name="marketer_commission_rules",
    )
    op.drop_index(
        op.f("ix_marketer_commission_rules_marketer_id"),
        table_name="marketer_commission_rules",
    )
    op.drop_index(
        op.f("ix_marketer_commission_rules_insurance_type_id"),
        table_name="marketer_commission_rules",
    )
    op.drop_index(
        op.f("ix_marketer_commission_rules_customer_id"),
        table_name="marketer_commission_rules",
    )
    op.drop_index(
        op.f("ix_insurance_type_mappings_insurance_type_id"),
        table_name="insurance_type_mappings",
    )
    op.drop_index(
        op.f("ix_insurance_type_commissions_insurance_type_id"),
        table_name="insurance_type_commissions",
    )
    op.drop_index(
        op.f("ix_insurance_type_commissions_effective_date"),
        table_name="insurance_type_commissions",
    )
    op.drop_index(
        op.f("ix_collections_due_date"),
        table_name="collections",
    )
    op.drop_index(
        op.f("ix_collections_collection_date"),
        table_name="collections",
    )
    # ============================================================
    # Restore policies FK to its previous behavior
    # ============================================================
    with op.batch_alter_table(
        "policies",
        schema=None,
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
        },
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_policies_customer_id_customers",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_policies_customer_id_customers",
            "customers",
            ["customer_id"],
            ["id"],
        )
    # ============================================================
    # Restore FLOAT columns
    # ============================================================
    with op.batch_alter_table(
        "marketers",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "other_commission",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "third_party_commission",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
    with op.batch_alter_table(
        "marketer_commission_rules",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "commission_percent",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
    with op.batch_alter_table(
        "insurance_type_commissions",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "issuance_percent",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "mortgage_commission",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "normal_commission",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=True,
        )
    with op.batch_alter_table(
        "commission_configs",
        schema=None,
    ) as batch_op:
        batch_op.alter_column(
            "vat",
            existing_type=sa.Numeric(precision=5, scale=2),
            type_=sa.FLOAT(),
            existing_nullable=False,
        )

