"""New enum values

Revision ID: 9a21960991c1
Revises: b117e50b5aa4
Create Date: 2022-06-28 16:17:02.825165

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a21960991c1'
down_revision = 'b117e50b5aa4'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE chargingstate ADD VALUE 'DISCHARGING'")
            op.execute("ALTER TYPE chargingstate ADD VALUE 'UNSUPPORTED'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE chargingstate RENAME TO chargingstate_old")
        op.execute("CREATE TYPE chargingstate AS ENUM('ERROR', 'CHARGING', 'READY_FOR_CHARGING', 'OFF', 'UNKNOWN', 'NOT_READY_FOR_CHARGING', 'CONSERVATION', 'CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING', 'CHARGE_PURPOSE_REACHED_CONSERVATION')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN chargingstate TYPE chargingstate USING "
            "chargingstate::text::chargingstate"
        ))
        op.execute("DROP TYPE chargingstate_old")

