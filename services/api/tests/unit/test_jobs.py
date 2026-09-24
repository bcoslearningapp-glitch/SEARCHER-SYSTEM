import pytest

from research_api.platform.jobs import (
    BackgroundJob,
    IllegalJobTransitionError,
    JobFailureKind,
    JobState,
    request_cancel,
    transition,
)


def _job(state: JobState = JobState.QUEUED) -> BackgroundJob:
    return BackgroundJob(kind="test", state=state.value, params={}, cancel_requested=False)


def test_happy_path_sets_timestamps() -> None:
    job = _job()
    transition(job, JobState.RUNNING)
    assert job.started_at is not None
    transition(job, JobState.SUCCEEDED, result={"ok": True})
    assert job.finished_at is not None
    assert job.result == {"ok": True}


@pytest.mark.parametrize("terminal", [JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED])
def test_terminal_states_are_final(terminal: JobState) -> None:
    job = _job(terminal)
    with pytest.raises(IllegalJobTransitionError):
        transition(job, JobState.RUNNING)


def test_failure_requires_kind() -> None:
    job = _job(JobState.RUNNING)
    with pytest.raises(ValueError, match="failure_kind"):
        transition(job, JobState.FAILED)
    transition(job, JobState.FAILED, failure_kind=JobFailureKind.PROVIDER_ERROR, error="timeout")
    assert job.failure_kind == "PROVIDER_ERROR"


def test_cancel_queued_is_immediate_running_is_cooperative() -> None:
    queued = _job()
    request_cancel(queued)
    assert queued.state == JobState.CANCELLED

    running = _job(JobState.RUNNING)
    request_cancel(running)
    assert running.state == JobState.RUNNING
    assert running.cancel_requested is True
