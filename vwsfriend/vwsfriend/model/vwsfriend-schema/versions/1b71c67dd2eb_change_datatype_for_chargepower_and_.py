"""Change datatype for chargepower and chargerate

Revision ID: 1b71c67dd2eb
Revises: f38c424891c2
Create Date: 2022-01-14 14:05:09.915985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b71c67dd2eb'
down_revision = 'f38c424891c2'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_context().dialect.name == 'postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE chargingstate ADD VALUE 'NOT_READY_FOR_CHARGING'")

        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE chargemode ADD VALUE 'TIMER'")
            op.execute("ALTER TYPE chargemode ADD VALUE 'ONLY_OWN_CURRENT'")
            op.execute("ALTER TYPE chargemode ADD VALUE 'PREFERRED_CHARGING_TIMES'")
            op.execute("ALTER TYPE chargemode ADD VALUE 'TIMER_CHARGING_WITH_CLIMATISATION'")

        op.alter_column('charges', 'chargePower_kW',
                        existing_type=sa.INTEGER(),
                        type_=sa.Float(),
                        existing_nullable=True)
        op.alter_column('charges', 'chargeRate_kmph',
                        existing_type=sa.INTEGER(),
                        type_=sa.Float(),
                        existing_nullable=True)
        op.alter_column('charging_sessions', 'maximumChargePower_kW',
                        existing_type=sa.INTEGER(),
                        type_=sa.Float(),
                        existing_nullable=True)


def downgrade():
    if op.get_context().dialect.name == 'postgresql':
        op.alter_column('charging_sessions', 'maximumChargePower_kW',
                        existing_type=sa.Float(),
                        type_=sa.INTEGER(),
                        existing_nullable=True)
        op.alter_column('charges', 'chargeRate_kmph',
                        existing_type=sa.Float(),
                        type_=sa.INTEGER(),
                        existing_nullable=True)
        op.alter_column('charges', 'chargePower_kW',
                        existing_type=sa.Float(),
                        type_=sa.INTEGER(),
                        existing_nullable=True)

    
        op.execute("ALTER TYPE chargingstate RENAME TO chargingstate_old")
        op.execute("CREATE TYPE chargingstate AS ENUM('ERROR', 'CHARGING', 'READY_FOR_CHARGING', 'OFF', 'UNKNOWN', 'CHARGE_PURPOSE_REACHED_CONSERVATION', 'CHARGE_PURPOSE_REACHED_NOT_CONSERVATION_CHARGING', 'CONSERVATION')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN chargingstate TYPE chargingstate USING "
            "chargingstate::text::chargingstate"
        ))
        op.execute("DROP TYPE chargingstate_old")

    if op.get_context().dialect.name == 'postgresql':
        op.execute("ALTER TYPE chargemode RENAME TO chargemode_old")
        op.execute("CREATE TYPE chargemode AS ENUM('MANUAL', 'INVALID', 'UNKNOWN', 'OFF')")
        op.execute((
            "ALTER TABLE transactions ALTER COLUMN chargemode TYPE chargemode USING "
            "chargemode::text::chargemode"
        ))
        op.execute("DROP TYPE chargemode_old")
