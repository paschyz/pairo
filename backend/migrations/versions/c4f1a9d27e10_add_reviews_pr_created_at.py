"""add reviews.pr_created_at

Revision ID: c4f1a9d27e10
Revises: b262cc5c634d
Create Date: 2026-09-30 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f1a9d27e10'
down_revision: Union[str, Sequence[str], None] = 'b262cc5c634d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reviews', sa.Column('pr_created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('reviews', 'pr_created_at')
