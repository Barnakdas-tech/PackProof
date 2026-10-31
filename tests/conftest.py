"""Shared pytest configuration.

Applies the `unit` / `integration` marker from the directory a test file lives in, so
`pytest -m unit` works without repeating a decorator on every test function. Adding a
test to `tests/unit/` or `tests/integration/` is the whole declaration of its tier.
"""

from collections.abc import Sequence

import pytest

TIERS = frozenset({"unit", "integration"})


def pytest_collection_modifyitems(items: Sequence[pytest.Item]) -> None:
    for item in items:
        tier = item.path.parent.name
        if tier in TIERS:
            item.add_marker(tier)
