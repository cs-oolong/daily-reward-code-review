from prometheus_client import Counter

DAILY_REWARD_CLAIMS = Counter(
    "daily_reward_claims_total",
    "Daily rewards claimed",
    ["player_id"],
)
