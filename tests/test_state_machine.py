from arm.workflow.state_machine import ReleaseContext, ReleaseState, StateMachineError


def test_valid_transitions_reach_completed():
    ctx = ReleaseContext()
    ctx.transition(ReleaseState.DIFF_COLLECTED, reason="collected")
    ctx.transition(ReleaseState.COMMITS_VALIDATED, reason="validated")
    ctx.transition(ReleaseState.VERSION_BUMPED, reason="bumped")
    ctx.transition(ReleaseState.CHANGELOG_WRITTEN, reason="changelog")
    ctx.transition(ReleaseState.PACKAGED, reason="packaged")
    ctx.transition(ReleaseState.COMPLETED, reason="done")
    assert ctx.state == ReleaseState.COMPLETED
    assert len(ctx.events) == 6


def test_invalid_transition_raises():
    ctx = ReleaseContext()
    try:
        ctx.transition(ReleaseState.VERSION_BUMPED, reason="skip")
    except StateMachineError:
        pass
    else:
        raise AssertionError("Expected StateMachineError")
