import requests

from app.settings import settings


def track_reward_claimed(player_id: str, reward_date: str, coins: int) -> None:
    response = requests.post(
        settings.ANALYTICS_URL,
        json={
            "event": "daily_reward_claimed",
            "player_id": player_id,
            "reward_date": reward_date,
            "coins": coins,
        },
        timeout=2,
    )
    response.raise_for_status()
