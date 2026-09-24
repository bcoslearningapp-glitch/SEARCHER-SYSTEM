"""Compare API JSON with canonical contracts: the contract omits optional fields rather than using null."""

from typing import Any


def as_contract(value: Any, *, drop: frozenset[str] = frozenset()) -> Any:
    if isinstance(value, dict):
        return {k: as_contract(v) for k, v in value.items() if v is not None and k not in drop}
    if isinstance(value, list):
        return [as_contract(v) for v in value]
    return value
