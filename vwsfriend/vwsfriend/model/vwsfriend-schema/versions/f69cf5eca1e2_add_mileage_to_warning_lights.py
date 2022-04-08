"""add mileage to warning lights

Revision ID: f69cf5eca1e2
Revises: bd42a6f71742
Create Date: 2022-04-08 21:56:59.115989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f69cf5eca1e2'
down_revision = 'bd42a6f71742'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('warning_lights', sa.Column('start_mileage', sa.Integer(), nullable=True))
    op.add_column('warning_lights', sa.Column('end_mileage', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('warning_lights', 'end_mileage')
    op.drop_column('warning_lights', 'start_mileage')
