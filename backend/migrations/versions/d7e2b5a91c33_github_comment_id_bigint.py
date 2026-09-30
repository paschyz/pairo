"""widen finding_decisions.github_comment_id to BigInteger

GitHub comment ids exceed 2^31 (e.g. 4149431117) and overflow a 32-bit integer.

Revision ID: d7e2b5a91c33
Revises: c4f1a9d27e10
Create Date: 2026-09-30 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7e2b5a91c33'
down_revision: Union[str, Sequence[str], None] = 'c4f1a9d27e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('finding_decisions') as batch:
        batch.alter_column(
            'github_comment_id', existing_type=sa.Integer(), type_=sa.BigInteger()
        )


def downgrade() -> None:
    with op.batch_alter_table('finding_decisions') as batch:
        batch.alter_column(
            'github_comment_id', existing_type=sa.BigInteger(), type_=sa.Integer()
        )
