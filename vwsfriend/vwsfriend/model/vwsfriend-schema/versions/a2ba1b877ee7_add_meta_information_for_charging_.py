"""Add meta information for charging session

Revision ID: a2ba1b877ee7
Revises: d13dfd852ab8
Create Date: 2023-02-20 10:36:21.132908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2ba1b877ee7'
down_revision = 'd13dfd852ab8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('charging_sessions', sa.Column('meterStart_kWh', sa.Float(), nullable=True))
    op.add_column('charging_sessions', sa.Column('meterEnd_kWh', sa.Float(), nullable=True))
    op.add_column('charging_sessions', sa.Column('pricePerKwh_ct', sa.Float(), nullable=True))
    op.add_column('charging_sessions', sa.Column('pricePerMinute_ct', sa.Float(), nullable=True))
    op.add_column('charging_sessions', sa.Column('pricePerSession_ct', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('charging_sessions', 'pricePerSession_ct')
    op.drop_column('charging_sessions', 'pricePerMinute_ct')
    op.drop_column('charging_sessions', 'pricePerKwh_ct')
    op.drop_column('charging_sessions', 'meterEnd_kWh')
    op.drop_column('charging_sessions', 'meterStart_kWh')
