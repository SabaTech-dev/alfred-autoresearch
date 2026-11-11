"""Pluggable benchmark runners (S6).

The engine executes a "benchmark" through a Runner. The default is
SubprocessRunner (the historical bash -c behavior). CallableRunner runs an
in-process Python function; CommandRunner runs a fixed shell command with
enriched env/timeout. Any object with an execute() method matching the
Runner protocol works.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from autoresearch.core.engine import ExecutionResult


class Runner(Protocol):
    """A benchmark executor: returns an ExecutionResult for a command."""

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult: ...


@dataclass
class SubprocessRunner:
    """Run the command through bash (historical default)."""

    default_timeout: int | None = None

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        timeout = timeout or self.default_timeout
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(cwd) if cwd else None,
                env=cmd_env,
                check=False,  # exit code is captured as part of the run result
            )
            exit_code: int | None = proc.returncode
            timed_out = False
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            exit_code = None
            timed_out = True
            stdout, stderr = e.stdout or "", e.stderr or ""

        duration = time.monotonic() - started
        passed = exit_code == 0 and not timed_out
        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            duration_seconds=duration,
            passed=passed,
            crashed=not passed,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
        )


class CallableRunner:
    """Run an in-process Python callable as the benchmark."""

    def __init__(
        self,
        fn: Callable[[], str],
        default_timeout: int | None = None,
    ):
        self._fn = fn
        self.default_timeout = default_timeout

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        started = time.monotonic()
        try:
            output = self._fn()
            exit_code: int | None = 0
            timed_out = False
            stdout, stderr = output, ""
        except Exception as e:  # noqa: BLE001 - any failure is a crashed run
            exit_code = 1
            timed_out = False
            stdout, stderr = "", f"{type(e).__name__}: {e}"

        duration = time.monotonic() - started
        passed = exit_code == 0 and not timed_out
        return ExecutionResult(
            command=command,
            exit_code=exit_code,
            duration_seconds=duration,
            passed=passed,
            crashed=not passed,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
        )


@dataclass
class CommandRunner:
    """Run a fixed command with enriched env/timeout.

    The command given to execute() is ignored (the runner owns the command);
    useful when the benchmark is fully defined by the runner configuration.
    """

    command: str
    env: dict[str, str] | None = None
    timeout: int | None = None

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> ExecutionResult:
        cmd_env = os.environ.copy()
        if self.env:
            cmd_env.update(self.env)
        if env:
            cmd_env.update(env)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["bash", "-c", self.command],
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                cwd=str(cwd) if cwd else None,
                env=cmd_env,
                check=False,  # exit code is captured as part of the run result
            )
            exit_code: int | None = proc.returncode
            timed_out = False
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as e:
            exit_code = None
            timed_out = True
            stdout, stderr = e.stdout or "", e.stderr or ""

        duration = time.monotonic() - started
        passed = exit_code == 0 and not timed_out
        return ExecutionResult(
            command=self.command,
            exit_code=exit_code,
            duration_seconds=duration,
            passed=passed,
            crashed=not passed,
            timed_out=timed_out,
            stdout=stdout,
            stderr=stderr,
        )
