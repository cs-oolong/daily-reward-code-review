from datetime import date

import pytest
from fastapi import HTTPException

from app.rewards import ClaimRequest, claim_daily_reward


@pytest.mark.asyncio
async def test_claim_daily_reward(db, player, analytics_mock):
    response = await claim_daily_reward(
        player.id,
        ClaimRequest(reward_date=date(2026, 10, 25)),
        db,
    )

    assert response.coins_awarded == 100
    assert response.new_balance == 150
    analytics_mock.assert_called_once()


@pytest.mark.asyncio
async def test_cannot_claim_same_date_twice(db, player, analytics_mock):
    request = ClaimRequest(reward_date=date(2026, 10, 25))

    await claim_daily_reward(player.id, request, db)

    with pytest.raises(HTTPException) as error:
        await claim_daily_reward(player.id, request, db)

    assert error.value.status_code == 409
    assert player.coins == 150
    analytics_mock.assert_called_once()
