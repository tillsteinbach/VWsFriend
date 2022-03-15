"""Add invalid climatization state

Revision ID: 027f3fc22787
Revises: 79ac0505ad35
Create Date: 2022-03-15 08:25:02.114964

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '027f3fc22787'
down_revision = '79ac0505ad35'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE climatizationstate ADD VALUE 'INVALID'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE climatizationstate RENAME TO climatizationstate_old")
        op.execute("CREATE TYPE climatizationstate AS ENUM('UNKNOWN', 'VENTILATION', 'COOLING', 'HEATING', 'OFF')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN climatizationstate TYPE climatizationstate USING "
            "climatizationstate::text::climatizationstate"
        ))
        op.execute("DROP TYPE climatizationstate_old")
