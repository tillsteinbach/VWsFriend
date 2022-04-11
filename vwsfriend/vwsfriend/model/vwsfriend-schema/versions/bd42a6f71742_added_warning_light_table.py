"""Added account table

Revision ID: bd42a6f71742
Revises: 027f3fc22787
Create Date: 2022-04-08 21:33:03.935283

"""
from alembic import op
import sqlalchemy as sa

from vwsfriend.model.datetime_decorator import DatetimeDecorator

# revision identifiers, used by Alembic.
revision = 'bd42a6f71742'
down_revision = '027f3fc22787'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('warning_lights',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('vehicle_vin', sa.String(), nullable=True),
                    sa.Column('start', DatetimeDecorator(timezone=True), nullable=False),
                    sa.Column('end', DatetimeDecorator(timezone=True), nullable=True),
                    sa.Column('text', sa.String(), nullable=True),
                    sa.Column('category', sa.Enum('LIGHTING', 'UNKNOWN', name='category'), nullable=True),
                    sa.Column('messageId', sa.String(), nullable=True),
                    sa.Column('serviceLead', sa.Boolean(), nullable=True),
                    sa.Column('customerRelevance', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['vehicle_vin'], ['vehicles.vin'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('vehicle_vin', 'messageId', 'start')
                    )


def downgrade():
    op.drop_table('warning_lights')
