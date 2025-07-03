"""add note tables

Revision ID: 003_add_note_tables
Revises: 002_add_friendship_table
Create Date: 2024-12-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create note table
    op.create_table('note',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('privacy', sa.Enum('private', 'public', name='noteprivacy'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_note_created_by_user_id'), 'note', ['created_by_user_id'], unique=False)
    op.create_index(op.f('ix_note_privacy'), 'note', ['privacy'], unique=False)
    op.create_index(op.f('ix_note_created_at'), 'note', ['created_at'], unique=False)
    op.create_index(op.f('ix_note_deleted_at'), 'note', ['deleted_at'], unique=False)

    # Create note_author association table
    op.create_table('noteauthor',
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('added_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['note_id'], ['note.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('note_id', 'user_id')
    )
    op.create_index(op.f('ix_noteauthor_note_id'), 'noteauthor', ['note_id'], unique=False)
    op.create_index(op.f('ix_noteauthor_user_id'), 'noteauthor', ['user_id'], unique=False)
    op.create_index(op.f('ix_noteauthor_added_by_user_id'), 'noteauthor', ['added_by_user_id'], unique=False)


def downgrade() -> None:
    # Drop note_author table first (due to foreign key constraints)
    op.drop_index(op.f('ix_noteauthor_added_by_user_id'), table_name='noteauthor')
    op.drop_index(op.f('ix_noteauthor_user_id'), table_name='noteauthor')
    op.drop_index(op.f('ix_noteauthor_note_id'), table_name='noteauthor')
    op.drop_table('noteauthor')
    
    # Drop note table
    op.drop_index(op.f('ix_note_deleted_at'), table_name='note')
    op.drop_index(op.f('ix_note_created_at'), table_name='note')
    op.drop_index(op.f('ix_note_privacy'), table_name='note')
    op.drop_index(op.f('ix_note_created_by_user_id'), table_name='note')
    op.drop_table('note')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS noteprivacy") 