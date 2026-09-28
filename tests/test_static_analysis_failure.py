"""Tests verifying static analysis fails gracefully without crashing."""

from src.tools.static_analysis import StaticAnalysisTool


def test_unavailable_tool_degrades_gracefully():
    # Attempting to run a non-existent tool should never raise FileNotFoundError
    status, stdout, err, dur = StaticAnalysisTool.run_command(["nonexistent_linter_tool_xyz"])
    assert status == "unavailable"
    assert "not installed" in err


def test_ruff_handles_missing_binary():
    # If ruff is not installed, it returns ToolEvent with status='unavailable'
    if not StaticAnalysisTool.is_tool_available("ruff"):
        event = StaticAnalysisTool.run_ruff(".")
        assert event.status == "unavailable"
        assert event.recovery is not None