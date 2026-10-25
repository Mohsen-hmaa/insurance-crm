"""add mortgage premium to policies

Revision ID: 57b5948e424e
Revises: fd74f99fede4
Create Date: 2026-09-29 20:44:40.318043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "57b5948e424e"
down_revision: Union[str, Sequence[str], None] = "fd74f99fede4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "policies",
        sa.Column(
            "mortgage_premium",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "policies",
        "mortgage_premium",
    )