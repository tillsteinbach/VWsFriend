"""Added battery temperature table

Revision ID: 6c4cdc5006ba
Revises: f3a66cd08ebe
Create Date: 2023-10-27 12:12:09.450271

"""
from alembic import op
import sqlalchemy as sa

from vwsfriend.model.datetime_decorator import DatetimeDecorator

# revision identifiers, used by Alembic.
revision = '6c4cdc5006ba'
down_revision = 'f3a66cd08ebe'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('battery_temperature',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('vehicle_vin', sa.String(), nullable=True),
    sa.Column('carCapturedTimestamp', DatetimeDecorator(timezone=True), nullable=False),
    sa.Column('temperatureHvBatteryMin_K', sa.Float(), nullable=True),
    sa.Column('temperatureHvBatteryMax_K', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['vehicle_vin'], ['vehicles.vin'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vehicle_vin', 'carCapturedTimestamp')
    )


def downgrade():
    op.drop_table('battery_temperature')
