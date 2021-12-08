"""New enum values

Revision ID: 91dac376210b
Revises: f6785099280a
Create Date: 2021-12-03 09:02:25.107132

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '91dac376210b'
down_revision = 'f6785099280a'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE chargingstate ADD VALUE 'CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING'")
            op.execute("ALTER TYPE chargingstate ADD VALUE 'CHARGE_PURPOSE_REACHED_CONSERVATION'")


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE chargingstate RENAME TO chargingstate_old")
        op.execute("CREATE TYPE chargingstate AS ENUM('ERROR', 'CHARGING', 'READY_FOR_CHARGING', 'OFF', 'UNKNOWN')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN chargingstate TYPE chargingstate USING "
            "chargingstate::text::chargingstate"
        ))
        op.execute("DROP TYPE chargingstate_old")
