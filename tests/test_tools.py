from pathlib import Path

import pytest

from ci_triage.preprocess import MAX_CHARS
from ci_triage.store import FixtureStore
from ci_triage.tools import (
    get_commit_files,
    get_failed_job_log,
    get_junit_summary,
    get_workflow_run,
)

RUNS = Path(__file__).parent / "fixtures" / "runs"


@pytest.fixture
def store() -> FixtureStore:
    return FixtureStore(RUNS)


def test_get_workflow_run(store: FixtureStore) -> None:
    run = get_workflow_run(store, "12345")
    assert run.name == "CI"
    assert run.sha == "abc123def456"
    assert run.branch == "main"
    assert run.conclusion == "failure"
    assert run.jobs[0].name == "test"


def test_get_failed_job_log_is_preprocessed(store: FixtureStore) -> None:
    excerpt = get_failed_job_log(store, "12345")
    assert "socket hang up" in excerpt
    assert "Set up job" not in excerpt
    assert len(excerpt) <= MAX_CHARS


def test_get_junit_summary_lists_failures(store: FixtureStore) -> None:
    summary = get_junit_summary(store, "12345")
    assert summary.reason is None
    assert len(summary.failed) == 1
    assert summary.failed[0].name == "waits for overlay"
    assert summary.failed[0].file == "src/flaky.test.js"
    assert "socket hang up" in summary.failed[0].message
    assert all(t.name != "passes" for t in summary.failed)


def test_get_commit_files_paths_only(store: FixtureStore) -> None:
    paths = get_commit_files(store, "12345")
    assert paths == ["src/flaky.test.js", "package.json"]
    assert all(isinstance(p, str) for p in paths)


def test_get_junit_summary_missing_artifact(store: FixtureStore) -> None:
    summary = get_junit_summary(store, "99999")
    assert summary.failed == []
    assert summary.reason == "no JUnit artifact"


def test_unknown_run_id(store: FixtureStore) -> None:
    with pytest.raises(FileNotFoundError):
        get_workflow_run(store, "00000")


def test_rejects_unsafe_run_id(store: FixtureStore) -> None:
    with pytest.raises(ValueError):
        get_workflow_run(store, "../secret")
