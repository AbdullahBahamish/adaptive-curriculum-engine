"""Initial ACE schema for skills, careers, prerequisites, and career_skills.

Revision ID: 0001_initial_ace_schema
Revises: 
Create Date: 2026-09-07 15:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial_ace_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.String(length=100), nullable=False, comment='Stable slug identifier'),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('estimated_hours', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # 2. Careers table
    op.create_table(
        'careers',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # 3. Prerequisites table (DAG edges: requires_skill_id -> skill_id)
    op.create_table(
        'prerequisites',
        sa.Column('skill_id', sa.String(length=100), nullable=False),
        sa.Column('requires_skill_id', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requires_skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('skill_id', 'requires_skill_id'),
    )

    # 4. Career-Skill requirements table
    op.create_table(
        'career_skills',
        sa.Column('career_id', sa.String(length=100), nullable=False),
        sa.Column('skill_id', sa.String(length=100), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('importance', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['career_id'], ['careers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('career_id', 'skill_id'),
    )


def downgrade() -> None:
    op.drop_table('career_skills')
    op.drop_table('prerequisites')
    op.drop_table('careers')
    op.drop_table('skills')
