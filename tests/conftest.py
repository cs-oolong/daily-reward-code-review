from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base, Player

PLAYER_ID = UUID("22222222-2222-2222-2222-222222222222")


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def player(db):
    player = Player(id=PLAYER_ID, coins=50)
    db.add(player)
    await db.commit()
    return player


@pytest.fixture
def analytics_mock(monkeypatch):
    from unittest.mock import Mock

    mock = Mock()
    monkeypatch.setattr("app.rewards.track_reward_claimed", mock)
    return mock
