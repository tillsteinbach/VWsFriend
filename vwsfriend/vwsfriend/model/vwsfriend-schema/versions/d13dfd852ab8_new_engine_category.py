"""New ENGINE category

Revision ID: d13dfd852ab8
Revises: ffbb2fb8db2a
Create Date: 2023-02-20 10:27:41.958140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd13dfd852ab8'
down_revision = 'ffbb2fb8db2a'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE category ADD VALUE 'ENGINE'")

def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE category RENAME TO category_old")
        op.execute("CREATE TYPE category AS ENUM('LIGHTING', 'TIRE', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN category TYPE category USING "
            "category::text::category"
        ))
        op.execute("DROP TYPE category_old")
