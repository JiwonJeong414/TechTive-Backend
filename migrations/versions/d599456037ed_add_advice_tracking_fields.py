"""Add advice tracking fields

Revision ID: d599456037ed
Revises: 9f6c9e281437
Create Date: 2025-07-10 01:32:47.730213

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd599456037ed'
down_revision = '9f6c9e281437'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('weekly_advices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('trigger_type', sa.String(length=50), nullable=False))
        batch_op.add_column(sa.Column('notes_analyzed_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('avg_joy', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('avg_sadness', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('avg_anger', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('avg_fear', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('avg_neutral', sa.Float(), nullable=True))
        batch_op.alter_column('of_week',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('weekly_advices', schema=None) as batch_op:
        batch_op.alter_column('of_week',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               nullable=False)
        batch_op.drop_column('avg_neutral')
        batch_op.drop_column('avg_fear')
        batch_op.drop_column('avg_anger')
        batch_op.drop_column('avg_sadness')
        batch_op.drop_column('avg_joy')
        batch_op.drop_column('notes_analyzed_count')
        batch_op.drop_column('trigger_type')

    # ### end Alembic commands ###
