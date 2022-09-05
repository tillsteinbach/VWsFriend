"""Add setting for order and hiding of vehicles

Revision ID: aff91a2c4232
Revises: f917fc564c1d
Create Date: 2022-09-05 11:33:54.780537

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aff91a2c4232'
down_revision = 'f917fc564c1d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vehicle_settings', sa.Column('sorting_order', sa.Integer(), nullable=True))
    op.add_column('vehicle_settings', sa.Column('hide', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('vehicle_settings', 'hide')
    op.drop_column('vehicle_settings', 'sorting_order')
