"""T5/S4 + T6/S5: --agent plumbing and global --json with exit codes."""

import json

import pytest
from click.testing import CliRunner

from autoresearch.cli import main


@pytest.fixture()
def runner():
    return CliRunner()


def _init(runner, cwd, **kw):
    return runner.invoke(main, ["init", "-n", "cli-exp", "-m", "score", "-C", str(cwd), *kw])


class TestAgentCli:
    def test_run_and_log_accept_agent(self, runner, tmp_path):
        _init(runner, tmp_path)
        r = runner.invoke(
            main, ["run", "-c", 'echo "METRIC score=10"', "-C", str(tmp_path), "--agent", "qa"]
        )
        assert r.exit_code == 0, r.output
        r = runner.invoke(main, ["log", "-d", "by qa", "-C", str(tmp_path), "--agent", "qa"])
        assert r.exit_code == 0, r.output
        state = json.loads(runner.invoke(main, ["status", "--json", "-C", str(tmp_path)]).output)
        assert state["last_run"]["agent"] == "qa"

    def test_agent_isolated_pending(self, runner, tmp_path):
        _init(runner, tmp_path)
        runner.invoke(
            main, ["run", "-c", 'echo "METRIC score=10"', "-C", str(tmp_path), "--agent", "qa"]
        )
        # agentless log must NOT see qa's pending
        r = runner.invoke(main, ["log", "-d", "wrong", "-C", str(tmp_path)])
        assert r.exit_code == 1


class TestJsonFlag:
    def test_log_json_outputs_machine_readable(self, runner, tmp_path):
        _init(runner, tmp_path)
        runner.invoke(main, ["run", "-c", 'echo "METRIC score=10"', "-C", str(tmp_path)])
        r = runner.invoke(main, ["log", "-d", "x", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 0, r.output
        data = json.loads(r.output)
        assert data["status"] == "keep"
        assert data["metric"] == 10.0

    def test_run_json(self, runner, tmp_path):
        _init(runner, tmp_path)
        r = runner.invoke(
            main, ["run", "-c", 'echo "METRIC score=7"', "--json", "-C", str(tmp_path)]
        )
        assert r.exit_code == 0, r.output
        data = json.loads(r.output)
        assert data["passed"] is True
        assert data["metrics"] == {"score": 7.0}

    def test_ideas_json(self, runner, tmp_path):
        _init(runner, tmp_path)
        runner.invoke(main, ["run", "-c", 'echo "METRIC score=9"', "-C", str(tmp_path)])
        runner.invoke(
            main, ["log", "-d", "x", "-s", "discard", "-i", "try cache", "-C", str(tmp_path)]
        )
        r = runner.invoke(main, ["ideas", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 0, r.output
        data = json.loads(r.output)
        assert "try cache" in data["ideas"]

    def test_report_json(self, runner, tmp_path):
        _init(runner, tmp_path)
        r = runner.invoke(main, ["report", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 0, r.output
        data = json.loads(r.output)
        assert data["written"] is True

    def test_log_without_pending_exits_1(self, runner, tmp_path):
        _init(runner, tmp_path)
        r = runner.invoke(main, ["log", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 1
        data = json.loads(r.output)
        assert "error" in data

    def test_run_uninitialized_exits_1(self, runner, tmp_path):
        r = runner.invoke(main, ["run", "-c", "echo hi", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 1

    def test_invalid_usage_exits_2(self, runner, tmp_path):
        r = runner.invoke(main, ["init", "-C", str(tmp_path)])  # missing -n/-m
        assert r.exit_code == 2

    def test_ideas_json_empty(self, runner, tmp_path):
        _init(runner, tmp_path)
        r = runner.invoke(main, ["ideas", "--json", "-C", str(tmp_path)])
        assert r.exit_code == 0
        assert json.loads(r.output)["ideas"] == []
