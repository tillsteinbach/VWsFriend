"""New enum value gasloline carType

Revision ID: f38c424891c2
Revises: 91dac376210b
Create Date: 2021-12-08 12:31:41.706156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f38c424891c2'
down_revision = '91dac376210b'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE cartype ADD VALUE 'GASOLINE'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE cartype RENAME TO cartype_old")
        op.execute("CREATE TYPE cartype AS ENUM('ELECTRIC', 'HYBRID', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN cartype TYPE cartype USING "
            "cartype::text::cartype"
        ))
        op.execute("DROP TYPE cartype_old")
