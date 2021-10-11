"""Added attributes for real refueled amount and cost

Revision ID: f6785099280a
Revises: f2fc2726507f
Create Date: 2021-10-11 21:26:49.789401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6785099280a'
down_revision = 'f2fc2726507f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('refuel_sessions', sa.Column('realRefueled_l', sa.Float(), nullable=True))
    op.add_column('refuel_sessions', sa.Column('realCost_ct', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('refuel_sessions', 'realCost_ct')
    op.drop_column('refuel_sessions', 'realRefueled_l')
    # ### end Alembic commands ###
