"""refactor Table Contacts

Revision ID: 7755e31d57c6
Revises: 1701d678ff5f
Create Date: 2026-03-05 15:55:47.270710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7755e31d57c6'
down_revision: Union[str, Sequence[str], None] = '1701d678ff5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(op.f('contacts_followed_user_id_fkey'), 'contacts', type_='foreignkey')
    op.drop_constraint(op.f('contacts_user_id_fkey'), 'contacts', type_='foreignkey')
    op.drop_constraint('uq_contacts_pair', 'contacts', type_='unique')
    op.drop_constraint('ck_contacts_not_self', 'contacts', type_='check')

    op.add_column('contacts', sa.Column('user_id_new', sa.Integer(), nullable=True))
    op.add_column('contacts', sa.Column('followed_user_id_new', sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE contacts c
            SET user_id_new = u.reks_id
            FROM users u
            WHERE c.user_id = u.id
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE contacts c
            SET followed_user_id_new = u.reks_id
            FROM users u
            WHERE c.followed_user_id = u.id
            """
        )
    )

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM contacts
                    WHERE user_id_new IS NULL OR followed_user_id_new IS NULL
                ) THEN
                    RAISE EXCEPTION 'contacts has rows that cannot map UUID user refs to users.reks_id';
                END IF;
            END
            $$;
            """
        )
    )

    op.drop_column('contacts', 'user_id')
    op.drop_column('contacts', 'followed_user_id')

    op.alter_column(
        'contacts',
        'user_id_new',
        new_column_name='user_id',
        existing_type=sa.Integer(),
        nullable=False,
        comment='关注者通用ID(reks_id)',
    )
    op.alter_column(
        'contacts',
        'followed_user_id_new',
        new_column_name='followed_user_id',
        existing_type=sa.Integer(),
        nullable=False,
        comment='被关注者通用ID(reks_id)',
    )

    op.create_index(op.f('ix_contacts_user_id'), 'contacts', ['user_id'], unique=False)
    op.create_index(op.f('ix_contacts_followed_user_id'), 'contacts', ['followed_user_id'], unique=False)
    op.create_unique_constraint('uq_contacts_pair', 'contacts', ['user_id', 'followed_user_id'])
    op.create_check_constraint('ck_contacts_not_self', 'contacts', 'user_id <> followed_user_id')
    op.create_foreign_key(op.f('contacts_user_id_fkey'), 'contacts', 'users', ['user_id'], ['reks_id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('contacts_followed_user_id_fkey'), 'contacts', 'users', ['followed_user_id'], ['reks_id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('contacts_followed_user_id_fkey'), 'contacts', type_='foreignkey')
    op.drop_constraint(op.f('contacts_user_id_fkey'), 'contacts', type_='foreignkey')
    op.drop_constraint('uq_contacts_pair', 'contacts', type_='unique')
    op.drop_constraint('ck_contacts_not_self', 'contacts', type_='check')
    op.drop_index(op.f('ix_contacts_followed_user_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_user_id'), table_name='contacts')

    op.add_column('contacts', sa.Column('user_id_old', sa.UUID(), nullable=True))
    op.add_column('contacts', sa.Column('followed_user_id_old', sa.UUID(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE contacts c
            SET user_id_old = u.id
            FROM users u
            WHERE c.user_id = u.reks_id
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE contacts c
            SET followed_user_id_old = u.id
            FROM users u
            WHERE c.followed_user_id = u.reks_id
            """
        )
    )

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM contacts
                    WHERE user_id_old IS NULL OR followed_user_id_old IS NULL
                ) THEN
                    RAISE EXCEPTION 'contacts has rows that cannot map reks_id refs back to users.id';
                END IF;
            END
            $$;
            """
        )
    )

    op.drop_column('contacts', 'user_id')
    op.drop_column('contacts', 'followed_user_id')

    op.alter_column(
        'contacts',
        'user_id_old',
        new_column_name='user_id',
        existing_type=sa.UUID(),
        nullable=False,
        comment='关注 UUID',
    )
    op.alter_column(
        'contacts',
        'followed_user_id_old',
        new_column_name='followed_user_id',
        existing_type=sa.UUID(),
        nullable=False,
        comment='被关注 UUID',
    )

    op.create_index(op.f('ix_contacts_user_id'), 'contacts', ['user_id'], unique=False)
    op.create_index(op.f('ix_contacts_followed_user_id'), 'contacts', ['followed_user_id'], unique=False)
    op.create_unique_constraint('uq_contacts_pair', 'contacts', ['user_id', 'followed_user_id'])
    op.create_check_constraint('ck_contacts_not_self', 'contacts', 'user_id <> followed_user_id')
    op.create_foreign_key(op.f('contacts_user_id_fkey'), 'contacts', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('contacts_followed_user_id_fkey'), 'contacts', 'users', ['followed_user_id'], ['id'], ondelete='CASCADE')
