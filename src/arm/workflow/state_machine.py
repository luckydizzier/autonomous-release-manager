from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class StateMachineError(RuntimeError):
    pass


class ReleaseState(str, Enum):
    NEW = "NEW"
    DIFF_COLLECTED = "DIFF_COLLECTED"
    COMMITS_VALIDATED = "COMMITS_VALIDATED"
    VERSION_BUMPED = "VERSION_BUMPED"
    CHANGELOG_WRITTEN = "CHANGELOG_WRITTEN"
    PACKAGED = "PACKAGED"
    COMPLETED = "COMPLETED"


_ALLOWED: dict[ReleaseState, set[ReleaseState]] = {
    ReleaseState.NEW: {ReleaseState.DIFF_COLLECTED},
    ReleaseState.DIFF_COLLECTED: {ReleaseState.COMMITS_VALIDATED},
    ReleaseState.COMMITS_VALIDATED: {ReleaseState.VERSION_BUMPED},
    ReleaseState.VERSION_BUMPED: {ReleaseState.CHANGELOG_WRITTEN},
    ReleaseState.CHANGELOG_WRITTEN: {ReleaseState.PACKAGED},
    ReleaseState.PACKAGED: {ReleaseState.COMPLETED},
    ReleaseState.COMPLETED: set(),
}


@dataclass(frozen=True, slots=True)
class ReleaseEvent:
    from_state: ReleaseState
    to_state: ReleaseState
    timestamp_utc: str
    reason: str
    artifacts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ReleaseContext:
    state: ReleaseState = ReleaseState.NEW
    events: list[ReleaseEvent] = field(default_factory=list)

    def transition(self, to_state: ReleaseState, *, reason: str, artifacts: list[str] | None = None) -> None:
        allowed = _ALLOWED.get(self.state, set())
        if to_state not in allowed:
            raise StateMachineError(f"Invalid transition: {self.state} -> {to_state}")
        ts = datetime.now(timezone.utc).isoformat()
        self.events.append(
            ReleaseEvent(
                from_state=self.state,
                to_state=to_state,
                timestamp_utc=ts,
                reason=reason,
                artifacts=list(artifacts or []),
            )
        )
        self.state = to_state
