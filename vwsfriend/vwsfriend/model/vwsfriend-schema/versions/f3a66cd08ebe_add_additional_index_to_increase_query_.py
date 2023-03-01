"""add additional index to increase query performance

Revision ID: f3a66cd08ebe
Revises: 1647742c9297
Create Date: 2023-03-01 16:07:55.295749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a66cd08ebe'
down_revision = '1647742c9297'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('charges_idx_vehicle_vin_chargepower_kw', 'charges', ['vehicle_vin', 'chargePower_kW'], unique=False)


def downgrade():
    op.drop_index('charges_idx_vehicle_vin_chargepower_kw', table_name='charges')
