import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table(
        "daily_reward_claims",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "player_id",
            sa.UUID(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column("reward_date", sa.Date(), nullable=False),
        sa.Column("coins", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_daily_reward_player_date",
        "daily_reward_claims",
        ["player_id", "reward_date"],
    )


def downgrade():
    op.drop_index("ix_daily_reward_player_date")
    op.drop_table("daily_reward_claims")
