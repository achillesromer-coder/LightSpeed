from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Any, DefaultDict
from collections import defaultdict

@dataclass
class Event:
    topic: str
    payload: dict

class EventBus:
    def __init__(self):
        self._subs: DefaultDict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, topic: str, fn: Callable[[Event], None]) -> None:
        self._subs[topic].append(fn)

    def publish(self, topic: str, **payload: Any) -> None:
        evt = Event(topic=topic, payload=payload)
        for fn in list(self._subs.get(topic, [])):
            try:
                fn(evt)
            except Exception as e:
                # TODO: route to audit/error log
                pass

# Global singleton (import in N.py and pass into layers via app.bus)
BUS = EventBus()
