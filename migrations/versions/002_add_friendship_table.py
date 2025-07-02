"""Add friendship table

Revision ID: 002
Revises: 001
Create Date: 2025-07-02 19:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create friendship table with VARCHAR status for simplicity
    op.create_table('friendship',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('addressee_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['addressee_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['requester_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for better performance
    op.create_index('ix_friendship_requester_id', 'friendship', ['requester_id'])
    op.create_index('ix_friendship_addressee_id', 'friendship', ['addressee_id'])
    op.create_index('ix_friendship_status', 'friendship', ['status'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_friendship_status', 'friendship')
    op.drop_index('ix_friendship_addressee_id', 'friendship')
    op.drop_index('ix_friendship_requester_id', 'friendship')
    
    # Drop friendship table
    op.drop_table('friendship')
    
    # Drop enum type
    op.execute("DROP TYPE friendshipstatus") 