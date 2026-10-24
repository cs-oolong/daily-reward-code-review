# Daily reward PR — answer key and discussion guide

Use this guide to discuss the review of [PR #1: Add daily login reward claims](https://github.com/cs-oolong/daily-reward-code-review/pull/1).

The goal is not to find every minor issue. Strong reviews prioritize concrete production risks, explain how they happen, and suggest fixes that preserve the relevant business invariants.

## Expected findings at a glance

| Priority | Location | Finding |
|---|---|---|
| Blocker | `app/rewards.py:23, 47, 60` | The client controls the reward date and can claim arbitrary dates |
| Blocker | `app/rewards.py:44–54`; migration `:21–25` | Concurrent requests can claim the same daily reward twice |
| Blocker | `app/rewards.py:54` | The balance read-modify-write can lose concurrent updates |
| High | `app/rewards.py:66–76` | Analytics can fail after the reward has already been committed |
| Medium | `app/rewards.py:69` | Synchronous analytics I/O blocks the async endpoint |
| Medium | `app/rewards.py:78` | `player_id` creates unbounded metric cardinality |
| Medium | `tests/test_rewards.py` | Tests omit concurrency and failure-boundary scenarios |

## 1. Client-controlled reward date allows unlimited claims

**File:** [`app/rewards.py`, lines 23, 47 and 60](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L23)

**Suggested review comment:**

> The client chooses `reward_date`, and we use it directly as the deduplication key. A player can therefore submit different past or future dates and receive 100 coins for each one. The server should derive the eligible reward date from its own clock, with an explicitly defined timezone. If the client date is needed for another reason, it should be validated rather than trusted to determine eligibility.

**Discussion point:** Which timezone should define a “day”: UTC, the player's local timezone, or another product-defined timezone?

## 2. Concurrent requests can claim the same daily reward twice

**Files:**

- [`app/rewards.py`, lines 44–54](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L44)
- [`migrations/versions/20261025_daily_reward_claims.py`, lines 21–25](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/migrations/versions/20261025_daily_reward_claims.py#L21)

**Suggested review comment:**

> Two requests can execute the `SELECT` simultaneously, both observe no existing claim, and then both credit the player and insert a claim. The current index is non-unique, so the database does not protect the “one reward per player per day” invariant. Please add a unique constraint on `(player_id, reward_date)` and handle the resulting integrity conflict appropriately. The preliminary `SELECT` alone is not sufficient.

**What a strong answer includes:** A database uniqueness constraint, not only an application-level check or a process-local Python lock. The conflict also needs deliberate transaction handling.

## 3. Balance update can overwrite concurrent shop or reward transactions

**File:** [`app/rewards.py`, line 54](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L54)

**Suggested review comment:**

> This is a read-modify-write based on a potentially stale balance. If the shop updates `player.coins` after this request reads it but before this request commits, our assignment overwrites the shop's update. Two rewards for different dates can similarly both read the same initial balance and lose one increment. Use an atomic database update such as `coins = coins + 100`, a row lock, or optimistic concurrency control. The daily-claim uniqueness constraint does not protect updates made by other features.

**Concrete example:** Starting at 500 coins, a 100-coin purchase and a 100-coin reward should leave 500. This implementation can leave 600 by overwriting the purchase.

## 4. Analytics failure returns an error after the reward has been committed

**File:** [`app/rewards.py`, lines 66–76](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L66)

**Suggested review comment:**

> At this point the coin grant is already committed. If analytics fails, we return HTTP 500 even though the player received the reward. A client retry then receives 409, making the operation appear to have failed when it actually succeeded. Analytics should not determine the outcome of the committed reward. Return the successful reward response and handle analytics separately through best-effort delivery, a background job, or an outbox with its own retries.

**Additional consequence:** The metric on line 78 is skipped, so the reward is granted but not counted as a successful claim.

## 5. Synchronous analytics call blocks the async endpoint

**File:** [`app/rewards.py`, line 69](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L69)

**Suggested review comment:**

> `track_reward_claimed()` uses synchronous `requests.post()` inside an async endpoint. While waiting for the analytics service, this can block the worker's event loop and delay unrelated requests. Prefer an async client or, better for this use case, decouple analytics through a background job or queue. Moving it to a thread only addresses event-loop blocking; it does not address the post-commit response problem above.

The two-second timeout limits the wait but does not remove the blocking behavior.

## 6. Player ID creates unbounded metric cardinality

**File:** [`app/rewards.py`, line 78](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/app/rewards.py#L78)

**Suggested review comment:**

> `player_id` is an unbounded label. Every player creates another time series, which can become expensive and eventually overload the metrics backend. Remove the player ID from the metric labels; keep it in structured logs or traces. A bounded label such as `result=success|duplicate|error` would be more useful operationally.

## 7. Tests miss the risky behavior

**File:** [`tests/test_rewards.py`](https://github.com/cs-oolong/daily-reward-code-review/blob/feature/daily-login-reward/tests/test_rewards.py)

**Suggested review comment:**

> The duplicate test is sequential, so it does not exercise the concurrent double-claim race. Please add coverage for two simultaneous claims, a concurrent balance update, arbitrary past/future dates, and analytics failing after the reward commit. The concurrency tests should use separate real database sessions/transactions; mocks alone will not demonstrate the database guarantees.

## Optional observations

These can lead to useful discussion but should not dominate the review:

- **Retry semantics (`app/rewards.py:51–52`):** Returning 409 for an identical retry is not necessarily wrong, but returning the original successful result would make the API more retry-friendly. The critical bug is the possibility of duplicate grants.
- **Naive timestamps (`app/rewards.py:62`):** `datetime.utcnow()` produces a naive timestamp. Prefer timezone-aware UTC timestamps consistently.
- **Analytics metric placement:** Decide whether the claim metric describes the committed business operation or only requests that also completed analytics delivery. Its name and labels should make that explicit.

## Questions for the feedback discussion

1. Which issue would you fix first, and why?
2. Can you trace two concurrent requests claiming the same reward?
3. Why does the unique claim constraint not prevent lost balance updates from the shop?
4. What should the API return if analytics fails after the reward commit?
5. How would you test the concurrency cases using separate database sessions?
6. Would you return 409 or the original successful response for an identical retry? What trade-off does that involve?

## Positive review signals

- Prioritizes direct coin exploits and data corruption over style.
- Explains failure scenarios with concrete interleavings.
- Enforces business invariants in the database rather than relying only on application checks.
- Separates the critical reward operation from non-critical analytics delivery.
- Suggests tests that exercise the actual failure boundaries.
- Gives clear, actionable comments without prescribing unnecessary complexity.
