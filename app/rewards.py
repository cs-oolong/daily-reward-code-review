import logging
from datetime import date, datetime
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import track_reward_claimed
from app.database import get_db
from app.metrics import DAILY_REWARD_CLAIMS
from app.models import DailyRewardClaim, Player

router = APIRouter()
logger = logging.getLogger(__name__)

DAILY_REWARD_COINS = 100


class ClaimRequest(BaseModel):
    reward_date: date


class ClaimResponse(BaseModel):
    player_id: UUID
    reward_date: date
    coins_awarded: int
    new_balance: int


@router.post("/players/{player_id}/daily-reward")
async def claim_daily_reward(
    player_id: UUID,
    payload: ClaimRequest,
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    player = await db.get(Player, player_id)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    existing_claim = await db.scalar(
        select(DailyRewardClaim).where(
            DailyRewardClaim.player_id == player_id,
            DailyRewardClaim.reward_date == payload.reward_date,
        )
    )

    if existing_claim is not None:
        raise HTTPException(status_code=409, detail="Reward already claimed")

    player.coins = player.coins + DAILY_REWARD_COINS

    db.add(
        DailyRewardClaim(
            id=uuid4(),
            player_id=player_id,
            reward_date=payload.reward_date,
            coins=DAILY_REWARD_COINS,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()

    try:
        track_reward_claimed(
            player_id=str(player_id),
            reward_date=payload.reward_date.isoformat(),
            coins=DAILY_REWARD_COINS,
        )
    except requests.RequestException:
        logger.exception("Could not send daily reward analytics")
        raise HTTPException(status_code=500, detail="Analytics unavailable")

    DAILY_REWARD_CLAIMS.labels(player_id=str(player_id)).inc()

    return ClaimResponse(
        player_id=player_id,
        reward_date=payload.reward_date,
        coins_awarded=DAILY_REWARD_COINS,
        new_balance=player.coins,
    )
