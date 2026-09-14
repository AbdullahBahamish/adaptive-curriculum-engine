"""Persistent learner profiles, skill mastery states, and interaction event stream.

Revision ID: 0002_persistent_learner_infrastructure
Revises: 0001_initial_ace_schema
Create Date: 2026-09-14 09:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0002_persistent_learner_infrastructure'
down_revision: Union[str, Sequence[str], None] = '0001_initial_ace_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Learners table
    op.create_table(
        'learners',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('target_career_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['target_career_id'], ['careers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. Learner skill mastery states
    op.create_table(
        'learner_skill_states',
        sa.Column('learner_id', sa.String(length=100), nullable=False),
        sa.Column('skill_id', sa.String(length=100), nullable=False),
        sa.Column('estimated_mastery', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.30'),
        sa.Column('evidence_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('predicted_performance', sa.Float(), nullable=True),
        sa.Column('last_evidence_id', sa.String(length=100), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('learner_id', 'skill_id'),
    )

    # 3. Canonical learner interaction event stream
    op.create_table(
        'learner_interactions',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column('learner_id', sa.String(length=100), nullable=False),
        sa.Column('skill_id', sa.String(length=100), nullable=False),
        sa.Column('evidence', sa.Float(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('evidence_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['learner_id'], ['learners.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('learner_id', 'evidence_id', name='uq_learner_evidence_id'),
    )
    op.create_index('ix_learner_interactions_learner_id', 'learner_interactions', ['learner_id'])
    op.create_index('ix_learner_interactions_skill_id', 'learner_interactions', ['skill_id'])
    op.create_index('ix_learner_interactions_created_at', 'learner_interactions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_learner_interactions_created_at', table_name='learner_interactions')
    op.drop_index('ix_learner_interactions_skill_id', table_name='learner_interactions')
    op.drop_index('ix_learner_interactions_learner_id', table_name='learner_interactions')
    op.drop_table('learner_interactions')
    op.drop_table('learner_skill_states')
    op.drop_table('learners')
