"""T7/S6: pluggable Runners (Protocol Runner, Subprocess, Callable, Command)."""

from autoresearch.core.engine import AutoResearch as AR
from autoresearch.runners import CallableRunner, CommandRunner, SubprocessRunner


def _callable_runner(**kw):
    return CallableRunner(lambda: "METRIC score=42\n", **kw)


class TestRunners:
    def test_subprocess_runner_is_default(self, tmp_path):
        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=None)
        ar.init()
        result = ar.run('echo "METRIC score=1"')
        assert result.passed

    def test_callable_runner_in_process(self, tmp_path):
        """AC: benchmark callable in-process without bash."""
        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=_callable_runner())
        ar.init()
        result = ar.run("n/a — callable")
        assert result.passed
        assert result.exit_code == 0
        run = ar.log("callable benchmark")
        assert run.metric == 42.0

    def test_callable_runner_crash(self, tmp_path):
        def boom():
            raise RuntimeError("boom")

        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=CallableRunner(boom))
        ar.init()
        result = ar.run("n/a")
        assert result.crashed
        assert "boom" in result.stderr

    def test_command_runner_env_and_timeout(self, tmp_path):
        runner = CommandRunner(
            'echo "METRIC score=$MY_VAL"',
            env={"MY_VAL": "33"},
            timeout=5,
        )
        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=runner)
        ar.init()
        result = ar.run("n/a — command fixed")
        assert result.passed
        run = ar.log("env command")
        assert run.metric == 33.0

    def test_command_runner_timeout(self, tmp_path):
        runner = CommandRunner("sleep 5")
        # Engine-level timeout governs execution.
        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=runner, timeout=1)
        ar.init()
        result = ar.run("n/a")
        assert result.timed_out

    def test_subprocess_runner_direct(self):
        r = SubprocessRunner()
        result = r.execute('echo "METRIC score=5"', timeout=10, cwd=None)
        assert result.passed

    def test_engine_accepts_any_runner(self, tmp_path):
        """Runner protocol: duck-typed object with execute()."""

        class Fake:
            def execute(self, command, timeout=None, cwd=None, env=None):
                from autoresearch.core.engine import ExecutionResult

                return ExecutionResult(
                    command=command,
                    exit_code=0,
                    duration_seconds=0.0,
                    passed=True,
                    crashed=False,
                    timed_out=False,
                    stdout="METRIC score=99",
                    stderr="",
                )

        ar = AR(name="runners", metric="score", cwd=tmp_path, runner=Fake())
        ar.init()
        ar.run("anything")
        run = ar.log("fake runner")
        assert run.metric == 99.0
