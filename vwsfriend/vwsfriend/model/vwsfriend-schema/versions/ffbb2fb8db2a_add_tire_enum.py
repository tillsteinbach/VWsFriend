"""Add TIRE Enum

Revision ID: ffbb2fb8db2a
Revises: aff91a2c4232
Create Date: 2022-10-13 14:06:43.668308

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ffbb2fb8db2a'
down_revision = 'aff91a2c4232'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE category ADD VALUE 'TIRE'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE category RENAME TO category_old")
        op.execute("CREATE TYPE category AS ENUM('LIGHTING', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN category TYPE category USING "
            "category::text::category"
        ))
        op.execute("DROP TYPE category_old")
