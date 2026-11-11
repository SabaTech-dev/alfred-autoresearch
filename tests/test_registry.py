"""T4/S3: optional experiment registry (AUTORESEARCH_HOME)."""

import json

from autoresearch.core.engine import AutoResearch as AR
from autoresearch.registry import list_experiments, registry_path


class TestRegistry:
    def test_registry_path_respects_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AUTORESEARCH_HOME", str(tmp_path))
        assert registry_path() == tmp_path / "registry.json"

    def test_init_registers_experiment(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        monkeypatch.setenv("AUTORESEARCH_HOME", str(home))
        exp = tmp_path / "exp1"
        exp.mkdir()
        ar = AR(name="reg-exp", metric="score", cwd=exp)
        ar.init()
        data = json.loads((home / "registry.json").read_text())
        assert str(exp) in data["experiments"]
        assert data["experiments"][str(exp)]["name"] == "reg-exp"

    def test_experiments_lists_known(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AUTORESEARCH_HOME", str(tmp_path))
        exp1 = tmp_path / "exp1"
        exp1.mkdir()
        AR(name="first", metric="score", cwd=exp1).init()
        exp2 = tmp_path / "exp2"
        exp2.mkdir()
        AR(name="second", metric="lat", cwd=exp2).init()
        entries = list_experiments()
        assert len(entries) == 2
        assert {e["name"] for e in entries} == {"first", "second"}

    def test_cwd_only_mode_works_without_registry(self, tmp_path, monkeypatch):
        # No AUTORESEARCH_HOME, unwritable default home must not break init.
        monkeypatch.setenv("AUTORESEARCH_HOME", "")
        monkeypatch.delenv("AUTORESEARCH_HOME", raising=False)
        ar = AR(name="solo", metric="score", cwd=tmp_path)
        ar.init()
        assert ar.is_initialized

    def test_corrupt_registry_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AUTORESEARCH_HOME", str(tmp_path))
        (tmp_path / "registry.json").write_text("not json{")
        assert list_experiments() == []
