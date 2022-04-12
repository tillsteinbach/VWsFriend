"""create maintenance table and add priority to warning lights table

Revision ID: 3500b84eb1f1
Revises: f69cf5eca1e2
Create Date: 2022-04-12 12:16:04.988381

"""
from alembic import op
import sqlalchemy as sa

from vwsfriend.model.datetime_decorator import DatetimeDecorator

# revision identifiers, used by Alembic.
revision = '3500b84eb1f1'
down_revision = 'f69cf5eca1e2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('maintenance',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('vehicle_vin', sa.String(), nullable=True),
                    sa.Column('date', DatetimeDecorator(timezone=True), nullable=True),
                    sa.Column('mileage', sa.Integer(), nullable=True),
                    sa.Column('type', sa.Enum('INSPECTION', 'OIL_SERVICE', 'UNKNOWN', name='maintenancetype'), nullable=True),
                    sa.Column('due_in_days', sa.Integer(), nullable=True),
                    sa.Column('due_in_km', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['vehicle_vin'], ['vehicles.vin'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.add_column('warning_lights', sa.Column('priority', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('warning_lights', 'priority')
    op.drop_table('maintenance')
