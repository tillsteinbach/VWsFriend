"""Add total capacity to settings

Revision ID: ae1799a66935
Revises: 901e3e466d03
Create Date: 2022-02-18 09:57:06.622149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae1799a66935'
down_revision = '901e3e466d03'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vehicle_settings', sa.Column('primary_capacity_total', sa.Integer(), nullable=True))
    op.add_column('vehicle_settings', sa.Column('secondary_capacity_total', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('vehicle_settings', 'secondary_capacity_total')
    op.drop_column('vehicle_settings', 'primary_capacity_total')
