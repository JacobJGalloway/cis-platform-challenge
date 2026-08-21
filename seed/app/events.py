"""Append-only event stream helper.

State changes publish a single event; email and history are sinks on that one write (one-write
fan-out). Events are never mutated or deleted — only appended.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Event:
    event_type: str
    aggregate_id: str
    payload: dict
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AppendOnlyStream:
    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def for_aggregate(self, aggregate_id: str) -> list[Event]:
        return [e for e in self._events if e.aggregate_id == aggregate_id]
