"""Add tags for journey

Revision ID: 79ac0505ad35
Revises: b7c0b285b1f3
Create Date: 2022-02-21 17:04:29.272843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79ac0505ad35'
down_revision = 'b7c0b285b1f3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('journey_tag',
                    sa.Column('journey_id', sa.Integer(), nullable=True),
                    sa.Column('tag_name', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['journey_id'], ['journey.id'], ),
                    sa.ForeignKeyConstraint(['tag_name'], ['tag.name'], )
                    )
    op.add_column('tag', sa.Column('use_journey', sa.Boolean(), nullable=True))
    op.execute("UPDATE tag SET use_journey = false")
    op.alter_column('tag', 'use_journey', nullable=False)


def downgrade():
    op.drop_column('tag', 'use_journey')
    op.drop_table('journey_tag')
