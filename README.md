# Daily reward code review exercise

This repository contains a small fictional pull request for a code review interview in a gaming backend.

## Your task

Review the open pull request as you would review a teammate's changes. Leave inline comments for issues you would want addressed before merge, prioritize them, and explain the concrete impact. You do not need to implement fixes.

## Product behavior

A player can claim a daily login reward of **100 coins**. A player must not be able to claim the same day's reward more than once.

The service also sends an analytics event after a successful claim.

## Environment

- FastAPI and asynchronous SQLAlchemy.
- Multiple API workers can handle requests concurrently.
- Clients can retry after timeouts and HTTP `5xx` responses.
- A player's coin balance is also updated by other features, such as the in-game shop.
- The code and all entities in this exercise are fictional.

## Local setup

```bash
python -m pip install -e '.[test]'
pytest
```
