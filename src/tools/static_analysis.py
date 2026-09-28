"""
Static analysis tool running linters and security scanners via subprocess.
Emphasizes graceful degradation: missing tools or timeouts never crash the audit.
"""

import shutil
import subprocess
import time
from typing import Optional

from src.models import ToolEvent


class StaticAnalysisTool:
    """Runs external linters/scanners with strict timeout and fallback handling."""

    DEFAULT_TIMEOUT_SECONDS = 30

    @classmethod
    def is_tool_available(cls, tool_name: str) -> bool:
        """Check if an executable is in the system PATH."""
        return shutil.which(tool_name) is not None

    @classmethod
    def run_command(
        cls, cmd: list[str], cwd: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS
    ) -> tuple[str, Optional[str], Optional[str], float]:
        """
        Executes an external command safely.
        Returns: (status, stdout_result, error_message, duration_seconds)
        status can be: "success", "failed", "unavailable", "timeout"
        """
        start_time = time.time()
        tool_name = cmd[0]

        if not cls.is_tool_available(tool_name):
            duration = round(time.time() - start_time, 2)
            return (
                "unavailable",
                None,
                f"Binary '{tool_name}' is not installed or not in PATH.",
                duration,
            )

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            duration = round(time.time() - start_time, 2)

            # Note: Linters often return exit code 1 when issues are found, which is a successful run
            output = (result.stdout + "\n" + result.stderr).strip()
            if result.returncode in (0, 1):
                return "success", output, None, duration
            else:
                return "failed", None, f"Exited with error code {result.returncode}: {output}", duration

        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 2)
            return (
                "timeout",
                None,
                f"Command timed out after {timeout} seconds.",
                duration,
            )
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return "failed", None, f"Execution error: {str(e)}", duration

    @classmethod
    def run_ruff(cls, target_dir: str) -> ToolEvent:
        """
        Run ruff linter on target directory if available.
        """
        cmd = ["ruff", "check", target_dir, "--output-format=text"]
        status, output, error, duration = cls.run_command(cmd)

        if status == "success":
            return ToolEvent(
                tool="ruff",
                status="success",
                result=output or "No lint issues found.",
                duration_seconds=duration,
            )
        elif status == "unavailable":
            return ToolEvent(
                tool="ruff",
                status="unavailable",
                error=error,
                recovery="Skipped ruff linting; continuing audit with heuristic analysis.",
                duration_seconds=duration,
            )
        elif status == "timeout":
            return ToolEvent(
                tool="ruff",
                status="timeout",
                error=error,
                recovery="Terminated ruff process; continuing without static linting.",
                duration_seconds=duration,
            )
        else:
            return ToolEvent(
                tool="ruff",
                status="failed",
                error=error,
                recovery="Ignored linter failure; proceeding with remaining audit steps.",
                duration_seconds=duration,
            )

    @classmethod
    def run_bandit(cls, target_dir: str) -> ToolEvent:
        """
        Run bandit security analyzer on target directory if available.
        """
        cmd = ["bandit", "-r", target_dir, "-f", "screen"]
        status, output, error, duration = cls.run_command(cmd)

        if status == "success":
            return ToolEvent(
                tool="bandit",
                status="success",
                result=output or "No security issues flagged.",
                duration_seconds=duration,
            )
        elif status == "unavailable":
            return ToolEvent(
                tool="bandit",
                status="unavailable",
                error=error,
                recovery="Skipped bandit security scan; falling back to pattern-based secret scan.",
                duration_seconds=duration,
            )
        elif status == "timeout":
            return ToolEvent(
                tool="bandit",
                status="timeout",
                error=error,
                recovery="Terminated bandit process; continuing without external security scan.",
                duration_seconds=duration,
            )
        else:
            return ToolEvent(
                tool="bandit",
                status="failed",
                error=error,
                recovery="Proceeding with audit despite security scanner execution failure.",
                duration_seconds=duration,
            )

    @classmethod
    def run_all(cls, target_dir: str) -> list[ToolEvent]:
        """Convenience method to run all static checks against a directory."""
        return [
            cls.run_ruff(target_dir),
            cls.run_bandit(target_dir),
        ]