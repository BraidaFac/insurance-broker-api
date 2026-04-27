"""add insurance models

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-27

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Client table
    op.create_table(
        'client',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.AutoString(length=255), nullable=False),
        sa.Column('industry', sqlmodel.AutoString(length=255), nullable=False),
        sa.Column('annual_turnover_nzd', sa.Float(), nullable=False),
        sa.Column('notes', sqlmodel.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Policy table (embedding added separately via raw SQL — requires pgvector extension)
    op.create_table(
        'policy',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('product_type', sa.Enum(
            'public_liability', 'professional_indemnity', 'cyber', 'business_interruption',
            name='producttype'
        ), nullable=False),
        sa.Column('insurer', sqlmodel.AutoString(length=255), nullable=False),
        sa.Column('sum_insured_nzd', sa.Float(), nullable=False),
        sa.Column('description', sqlmodel.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute("ALTER TABLE policy ADD COLUMN embedding vector(1536)")

    # Quote table
    op.create_table(
        'quote',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('premium_nzd', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'sent', 'accepted', name='quotestatus'), nullable=False),
        sa.Column('client_id', sa.Uuid(), nullable=False),
        sa.Column('policy_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['client.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policy.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('quote')
    op.drop_table('policy')
    op.drop_table('client')
    op.execute("DROP TYPE IF EXISTS producttype")
    op.execute("DROP TYPE IF EXISTS quotestatus")
