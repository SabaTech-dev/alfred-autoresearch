"""Tests for the AutoResearch CLI."""

import json

import pytest
from click.testing import CliRunner

from autoresearch import AutoResearch
from autoresearch.cli import main


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def experiment(tmp_path):
    """Initialized experiment with one baseline run, via the Python API."""
    ar = AutoResearch(name="cli-exp", metric="score", direction="lower", unit="pts", cwd=tmp_path)
    ar.init()
    ar.run('echo "METRIC score=100"')
    ar.log("baseline")
    return ar


class TestInit:
    def test_init_creates_experiment(self, runner, tmp_path):
        result = runner.invoke(
            main,
            [
                "init",
                "--name",
                "e2e",
                "--metric",
                "score",
                "--direction",
                "lower",
                "--unit",
                "pts",
                "--cwd",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "autoresearch.results.jsonl").exists()

    def test_init_requires_name_and_metric(self, runner, tmp_path):
        result = runner.invoke(main, ["init", "--cwd", str(tmp_path)])
        assert result.exit_code != 0


class TestRunLogFlow:
    def test_run_before_init_fails(self, runner, tmp_path):
        result = runner.invoke(main, ["run", "-c", "true", "--cwd", str(tmp_path)])
        assert result.exit_code == 1

    def test_log_without_pending_fails(self, runner, tmp_path):
        runner.invoke(
            main,
            [
                "init",
                "-n",
                "e2e",
                "-m",
                "score",
                "--cwd",
                str(tmp_path),
            ],
        )
        result = runner.invoke(main, ["log", "--cwd", str(tmp_path)])
        assert result.exit_code == 1

    def test_run_then_log(self, runner, tmp_path):
        runner.invoke(
            main,
            [
                "init",
                "-n",
                "e2e",
                "-m",
                "score",
                "--cwd",
                str(tmp_path),
            ],
        )
        result = runner.invoke(
            main, ["run", "-c", 'echo "METRIC score=42"', "--cwd", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "METRIC score=42" in result.output or "score" in result.output

        result = runner.invoke(main, ["log", "-d", "cli baseline", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        assert "cli baseline" in result.output or "keep" in result.output

    def test_log_discard_with_idea(self, runner, tmp_path):
        runner.invoke(
            main,
            [
                "init",
                "-n",
                "e2e",
                "-m",
                "score",
                "--cwd",
                str(tmp_path),
            ],
        )
        runner.invoke(main, ["run", "-c", 'echo "METRIC score=1"', "--cwd", str(tmp_path)])
        result = runner.invoke(
            main,
            [
                "log",
                "-d",
                "bad",
                "-s",
                "discard",
                "-i",
                "try caching",
                "--cwd",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        ideas = (tmp_path / "autoresearch.ideas.md").read_text()
        assert "try caching" in ideas

    def test_run_crash_reported(self, runner, tmp_path):
        runner.invoke(
            main,
            [
                "init",
                "-n",
                "e2e",
                "-m",
                "score",
                "--cwd",
                str(tmp_path),
            ],
        )
        result = runner.invoke(main, ["run", "-c", "exit 3", "--cwd", str(tmp_path)])
        assert result.exit_code == 0  # crash is a recorded outcome, not a CLI error
        assert "rashed" in result.output


class TestStatusJson:
    def test_status_json_outputs_machine_readable_state(self, runner, tmp_path, experiment):
        result = runner.invoke(main, ["status", "--json", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        state = json.loads(result.output)
        assert state["name"] == "cli-exp"
        assert state["metric_name"] == "score"
        assert state["total_runs"] == 1
        assert state["baseline_metric"] == 100.0
        assert state["initialized"] is True

    def test_status_json_uninitialized(self, runner, tmp_path):
        result = runner.invoke(main, ["status", "--json", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        state = json.loads(result.output)
        assert state["initialized"] is False


class TestIdeas:
    def test_ideas_lists_backlog(self, runner, tmp_path, experiment):
        experiment.run('echo "METRIC score=120"')
        experiment.discard_with_idea("worse", "try async I/O")

        result = runner.invoke(main, ["ideas", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        assert "try async I/O" in result.output

    def test_ideas_empty_backlog(self, runner, tmp_path, experiment):
        result = runner.invoke(main, ["ideas", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        assert "ideas" in result.output.lower()


class TestReport:
    def test_report_writes_session_doc(self, runner, tmp_path, experiment):
        experiment.run('echo "METRIC score=80"')
        experiment.log("faster path")

        result = runner.invoke(main, ["report", "--cwd", str(tmp_path)])
        assert result.exit_code == 0

        doc = (tmp_path / "autoresearch.md").read_text()
        assert "cli-exp" in doc
        assert "score" in doc
        assert "baseline" in doc
        assert "faster path" in doc

    def test_report_uninitialized_fails(self, runner, tmp_path):
        result = runner.invoke(main, ["report", "--cwd", str(tmp_path)])
        assert result.exit_code == 1


class TestExportAndReset:
    def test_export_dumps_json(self, runner, tmp_path, experiment):
        result = runner.invoke(main, ["export", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
        state = json.loads(result.output)
        assert len(state["runs"]) == 1

    def test_reset_force(self, runner, tmp_path, experiment):
        result = runner.invoke(main, ["reset", "--force", "--cwd", str(tmp_path)])
        assert result.exit_code == 0
