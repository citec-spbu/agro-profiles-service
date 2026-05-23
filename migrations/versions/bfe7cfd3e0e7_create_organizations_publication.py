"""create_organizations_publication

Revision ID: bfe7cfd3e0e7
Revises: acdb241e344d
Create Date: 2026-05-23 23:15:37.049344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfe7cfd3e0e7'
down_revision: Union[str, None] = 'acdb241e344d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_publication WHERE pubname = 'organizations_publication'
            ) THEN
                CREATE PUBLICATION organizations_publication FOR TABLE organizations;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.execute("DROP PUBLICATION IF EXISTS organizations_publication")
