import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    coins: Mapped[int] = mapped_column(default=0)


class DailyRewardClaim(Base):
    __tablename__ = "daily_reward_claims"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"))
    reward_date: Mapped[date] = mapped_column(Date())
    coins: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime())
