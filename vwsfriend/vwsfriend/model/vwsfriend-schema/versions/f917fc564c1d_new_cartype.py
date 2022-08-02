"""New cartype

Revision ID: f917fc564c1d
Revises: 9a21960991c1
Create Date: 2022-08-02 08:13:48.359712

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f917fc564c1d'
down_revision = '9a21960991c1'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE cartype ADD VALUE IF NOT EXISTS 'PETROL '")
            op.execute("ALTER TYPE cartype ADD VALUE IF NOT EXISTS 'DIESEL'")
            op.execute("ALTER TYPE cartype ADD VALUE IF NOT EXISTS 'CNG'")
            op.execute("ALTER TYPE cartype ADD VALUE IF NOT EXISTS 'LPG'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE cartype RENAME TO cartype_old")
        op.execute("CREATE TYPE cartype AS ENUM('ELECTRIC', 'HYBRID', 'GASOLINE', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN cartype TYPE cartype USING "
            "cartype::text::cartype"
        ))
        op.execute("DROP TYPE cartype_old")
