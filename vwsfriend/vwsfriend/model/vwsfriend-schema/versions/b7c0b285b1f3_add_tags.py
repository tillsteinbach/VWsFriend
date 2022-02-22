"""Add tags

Revision ID: b7c0b285b1f3
Revises: ae1799a66935
Create Date: 2022-02-21 16:04:53.710946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c0b285b1f3'
down_revision = 'ae1799a66935'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('tag',
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('use_trips', sa.Boolean(), nullable=False),
                    sa.Column('use_charges', sa.Boolean(), nullable=False),
                    sa.Column('use_refueling', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('name')
                    )
    op.create_table('refuel_tag',
                    sa.Column('refuel_sessions_id', sa.Integer(), nullable=True),
                    sa.Column('tag_name', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['refuel_sessions_id'], ['refuel_sessions.id'], ),
                    sa.ForeignKeyConstraint(['tag_name'], ['tag.name'], )
                    )
    op.create_table('trip_tag',
                    sa.Column('trips_id', sa.Integer(), nullable=True),
                    sa.Column('tag_name', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['tag_name'], ['tag.name'], ),
                    sa.ForeignKeyConstraint(['trips_id'], ['trips.id'], )
                    )
    op.create_table('charging_tag',
                    sa.Column('charging_sessions_id', sa.Integer(), nullable=True),
                    sa.Column('tag_name', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['charging_sessions_id'], ['charging_sessions.id'], ),
                    sa.ForeignKeyConstraint(['tag_name'], ['tag.name'], )
                    )


def downgrade():
    op.drop_table('charging_tag')
    op.drop_table('trip_tag')
    op.drop_table('refuel_tag')
    op.drop_table('tag')
