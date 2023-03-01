"""add index to increase query performance

Revision ID: 1647742c9297
Revises: a2ba1b877ee7
Create Date: 2023-03-01 14:30:31.836580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1647742c9297'
down_revision = 'a2ba1b877ee7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_charges_chargePower_kW'), 'charges', ['chargePower_kW'], unique=False)
    op.create_index(op.f('ix_charges_chargingState'), 'charges', ['chargingState'], unique=False)
    op.create_index(op.f('ix_charging_sessions_acdc'), 'charging_sessions', ['acdc'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_charging_sessions_acdc'), table_name='charging_sessions')
    op.drop_index(op.f('ix_charges_chargingState'), table_name='charges')
    op.drop_index(op.f('ix_charges_chargePower_kW'), table_name='charges')
