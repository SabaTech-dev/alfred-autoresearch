"""Tests for AutoResearch SDK."""

import pytest

from autoresearch import describe_confidence, parse_metric_lines
from autoresearch.core.confidence import compute_confidence as cc
from autoresearch.core.engine import AutoResearch as AR
from autoresearch.core.engine import Direction, RunStatus


class TestIdeasDedup:
    def test_duplicate_ideas_appended_once(self, tmp_path):
        ar = AR(name="dedup", metric="score", cwd=tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        ar.discard_with_idea("first", "try caching instead")
        ar.run('echo "METRIC score=110"')
        ar.discard_with_idea("second", "try caching instead")

        content = (tmp_path / ar.IDEAS_FILE).read_text()
        assert content.count("try caching instead") == 1

    def test_distinct_ideas_all_kept(self, tmp_path):
        ar = AR(name="dedup", metric="score", cwd=tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        ar.discard_with_idea("first", "try caching instead")
        ar.run('echo "METRIC score=110"')
        ar.discard_with_idea("second", "try connection pooling")

        content = (tmp_path / ar.IDEAS_FILE).read_text()
        assert "try caching instead" in content
        assert "try connection pooling" in content


class TestReport:
    def test_generate_report_markdown(self, tmp_path):
        ar = AR(name="report-exp", metric="score", direction="lower", unit="ms", cwd=tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        ar.log("baseline")
        ar.run('echo "METRIC score=60"')
        ar.log("after tuning")

        report = ar.generate_report()
        assert "# Autoresearch: report-exp" in report
        assert "**Primary**: score (ms, lower is better)" in report
        assert "baseline" in report
        assert "after tuning" in report
        assert "Best" in report

    def test_generate_report_uninitialized(self, tmp_path):
        ar = AR(name="x", metric="score", cwd=tmp_path)
        with pytest.raises(RuntimeError, match="Not initialized"):
            ar.generate_report()


class TestMetricParsing:
    def test_basic_metrics(self):
        output = "METRIC latency_ms=142.5\nMETRIC throughput_qps=1024"
        result = parse_metric_lines(output)
        assert result == {"latency_ms": 142.5, "throughput_qps": 1024.0}

    def test_scientific_notation(self):
        output = "METRIC time_ns=1.5e9"
        result = parse_metric_lines(output)
        assert result == {"time_ns": 1500000000.0}

    def test_negative_values(self):
        output = "METRIC delta=-3.2"
        result = parse_metric_lines(output)
        assert result == {"delta": -3.2}

    def test_unicode_mu(self):
        output = "METRIC latency_µs=142.5"
        result = parse_metric_lines(output)
        assert "latency_µs" in result

    def test_empty_output(self):
        assert parse_metric_lines("") == {}
        assert parse_metric_lines("no metrics here") == {}

    def test_mixed_output(self):
        output = "Running benchmark...\nSome noise\nMETRIC score=0.95\nDone!"
        result = parse_metric_lines(output)
        assert result == {"score": 0.95}


class TestConfidence:
    def test_needs_three_runs(self):
        runs = [{"metric": 100, "status": "keep"}]
        assert cc(runs) is None
        runs.append({"metric": 95, "status": "keep"})
        assert cc(runs) is None
        runs.append({"metric": 90, "status": "keep"})
        assert cc(runs) is not None

    def test_high_confidence(self):
        # Need some variance so MAD > 0
        runs = [
            {"metric": 100, "status": "keep"},
            {"metric": 98, "status": "keep"},
            {"metric": 102, "status": "keep"},
            {"metric": 50, "status": "keep"},
        ]
        conf = cc(runs)
        assert conf is not None
        assert conf >= 2.0

    def test_low_confidence(self):
        runs = [
            {"metric": 100, "status": "keep"},
            {"metric": 99, "status": "keep"},
            {"metric": 101, "status": "keep"},
            {"metric": 98, "status": "keep"},
        ]
        conf = cc(runs)
        assert conf is not None
        assert conf <= 2.0

    def test_higher_direction(self):
        runs = [
            {"metric": 10, "status": "keep"},
            {"metric": 11, "status": "keep"},
            {"metric": 9, "status": "keep"},
            {"metric": 100, "status": "keep"},
        ]
        conf = cc(runs, "higher")
        assert conf is not None
        assert conf >= 2.0

    def test_zero_mad_returns_none(self):
        # All identical values → MAD = 0 → can't compute confidence
        runs = [
            {"metric": 100, "status": "keep"},
            {"metric": 100, "status": "keep"},
            {"metric": 100, "status": "keep"},
            {"metric": 50, "status": "keep"},
        ]
        conf = cc(runs)
        assert conf is None  # MAD = 0 → indeterminate

    def test_describe_confidence(self):
        assert "n/a" in describe_confidence(None)
        assert "likely real" in describe_confidence(2.5)
        assert "marginal" in describe_confidence(1.5)
        assert "within noise" in describe_confidence(0.5)


class TestEngine:
    def _make_ar(self, tmpdir) -> AR:
        return AR(
            name="test-exp",
            metric="score",
            direction="lower",
            unit="ms",
            cwd=tmpdir,
        )

    def test_init(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        assert ar.is_initialized

    def test_init_twice_fails(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        with pytest.raises(ValueError, match="Already initialized"):
            ar.init()

    def test_init_reset(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.init(reset=True)
        assert ar.is_initialized

    def test_run_before_init_fails(self, tmp_path):
        ar = self._make_ar(tmp_path)
        with pytest.raises(RuntimeError, match="Not initialized"):
            ar.run("echo hello")

    def test_run_and_log(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        result = ar.run('echo "METRIC score=100"')
        assert result.passed
        assert ar.has_pending

        run = ar.log(description="baseline")
        assert run.metric == 100.0
        assert run.baseline
        assert not ar.has_pending

    def test_multiple_runs(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()

        # Baseline
        ar.run('echo "METRIC score=100"')
        ar.log("baseline")
        assert ar.baseline_metric == 100.0
        assert ar.best_metric == 100.0

        # Better
        ar.run('echo "METRIC score=50"')
        ar.log("optimization 1")
        assert ar.best_metric == 50.0

        # Worse
        ar.run('echo "METRIC score=75"')
        ar.log("optimization 2")
        assert ar.best_metric == 50.0  # unchanged

    def test_crash_handling(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        result = ar.run("exit 1")
        assert result.crashed
        assert ar.has_pending

        run = ar.log(description="crashed", status="crash")
        assert run.status == RunStatus.CRASH

    def test_discard_with_idea(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        run = ar.discard_with_idea("bad approach", "try caching instead")
        assert run.status == RunStatus.DISCARD

        # Idea should be written to file
        ideas_path = tmp_path / ar.IDEAS_FILE
        assert ideas_path.exists()
        content = ideas_path.read_text()
        assert "try caching instead" in content

    def test_state_persistence(self, tmp_path):
        # Create and run in one instance
        ar1 = self._make_ar(tmp_path)
        ar1.init()
        ar1.run('echo "METRIC score=100"')
        ar1.log("baseline")
        ar1.run('echo "METRIC score=50"')
        ar1.log("improvement")

        # Load in another instance
        ar2 = self._make_ar(tmp_path)
        assert ar2.is_initialized
        assert ar2.total_runs == 2
        assert ar2.baseline_metric == 100.0
        assert ar2.best_metric == 50.0

    def test_get_best_run(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        ar.log("baseline")
        ar.run('echo "METRIC score=80"')
        ar.log("try 1")
        ar.run('echo "METRIC score=50"')
        ar.log("try 2")
        ar.run('echo "METRIC score=60"')
        ar.log("try 3")

        best = ar.get_best_run()
        assert best is not None
        assert best.metric == 50.0

    def test_status_snapshot(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        ar.log("baseline")

        status = ar.get_status()
        assert status["initialized"]
        assert status["total_runs"] == 1
        assert status["baseline_metric"] == 100.0

    def test_higher_direction(self, tmp_path):
        ar = AR(name="test", metric="score", direction="higher", cwd=tmp_path)
        ar.init()
        ar.run('echo "METRIC score=10"')
        ar.log("baseline")
        ar.run('echo "METRIC score=100"')
        ar.log("improvement")
        assert ar.best_metric == 100.0

    def test_confidence_computed(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        # Need variance so MAD > 0
        for score in [100, 98, 102, 50]:
            ar.run(f'echo "METRIC score={score}"')
            ar.log(f"run {score}")

        assert ar.confidence is not None
        assert ar.confidence >= 1.0

    def test_log_honors_status_without_description(self, tmp_path):
        """Regression: log(status=...) without description ignored the status.

        A passing run logged with status="discard" and no description was
        recorded as "keep", polluting best_metric with a discarded result.
        """
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        run = ar.log(status="discard")

        assert run.status == RunStatus.DISCARD
        assert ar.best_metric is None  # discarded run must not become best

    def test_log_default_description_when_status_given(self, tmp_path):
        ar = self._make_ar(tmp_path)
        ar.init()
        ar.run('echo "METRIC score=100"')
        run = ar.log(status="keep")

        assert run.status == RunStatus.KEEP
        assert run.description  # non-empty default, not ""

    def test_unnamed_experiment_resumes_config_from_file(self, tmp_path):
        """Regression: config entries without a name skipped config restore.

        A config persisted as {"name": null} (unnamed experiment) did not
        restore metricName/bestDirection from the file, so constructor
        arguments silently won on resume — e.g. a wrong direction could
        flip the meaning of "best" without any error.
        """
        ar1 = AR(name="", metric="score", direction="lower", cwd=tmp_path)
        ar1.init()
        ar1.run('echo "METRIC score=100"')
        ar1.log("baseline")

        # Resume with WRONG constructor args: the file must win.
        ar2 = AR(name="", metric="wrong_metric", direction="higher", cwd=tmp_path)
        assert ar2.is_initialized
        assert ar2.total_runs == 1
        assert ar2.config.metric_name == "score"
        assert ar2.config.best_direction == Direction.LOWER
        ar2.run('echo "METRIC score=50"')
        ar2.log("improvement after resume")
        # direction=lower from file: 50 < 100 baseline is the improvement
        assert ar2.best_metric == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
