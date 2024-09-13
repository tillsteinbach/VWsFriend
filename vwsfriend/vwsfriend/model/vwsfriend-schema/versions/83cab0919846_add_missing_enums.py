"""add missing Enums

Revision ID: 83cab0919846
Revises: 6c4cdc5006ba
Create Date: 2024-09-13 08:06:20.121117

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83cab0919846'
down_revision = '6c4cdc5006ba'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE category ADD VALUE 'OTHER'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE category RENAME TO category_old")
        op.execute("CREATE TYPE category AS ENUM('ENGINE', 'LIGHTING', 'TIRE', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN category TYPE category USING "
            "category::text::category"
        ))
        op.execute("DROP TYPE category_old")