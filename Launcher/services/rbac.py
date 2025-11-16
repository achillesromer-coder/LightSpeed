from __future__ import annotations
from functools import wraps
from typing import Callable, Iterable

def require_role(allowed: Iterable[str]):
    allowed = set(allowed)
    def deco(fn: Callable):
        @wraps(fn)
        def wrapper(app, *a, **kw):
            role = getattr(app.session, "role", "viewer") or "viewer"
            if role not in allowed:
                app.log(f"Denied: role '{role}' cannot run {fn.__name__}")
                return None
            return fn(app, *a, **kw)
        return wrapper
    return deco

# Example usage in a layer:
# @require_role(["admin","founder","it"])
# def publish_to_live(app, item_id: str): ...
