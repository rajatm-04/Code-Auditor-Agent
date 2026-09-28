"""Tests for Markdown and JSON report generation."""

import json
from src.models import AuditReport, Finding, RepositorySummary, ToolEvent
from src.report.json_report import JsonReportGenerator
from src.report.markdown_report import MarkdownReportGenerator


def test_report_generation_roundtrip(tmp_path):
    report = AuditReport(
        repository=RepositorySummary(
            url="https://github.com/psf/requests",
            name="requests",
            primary_language="Python",
            files_analyzed=10,
            source_files=8,
            test_files=2,
            lines_analyzed=1200,
        ),
        executive_summary="Codebase is well maintained.",
        findings=[
            Finding(
                title="Broad exception",
                severity="medium",
                category="reliability",
                file="requests/api.py",
                line_start=15,
                evidence="except Exception:",
                impact="May swallow errors",
                recommendation="Catch specific exceptions",
                confidence=0.9,
            )
        ],
        tool_events=[
            ToolEvent(tool="GitHub API", status="success", result="Fetched 10 files")
        ],
    )

    out_prefix = str(tmp_path / "test_report")
    md_file = MarkdownReportGenerator.save(report, out_prefix)
    json_file = JsonReportGenerator.save(report, out_prefix)

    # Check Markdown
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "# Code Quality Audit Report: requests" in md_text
    assert "Broad exception" in md_text

    # Check JSON
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    assert json_data["repository"]["name"] == "requests"
    assert len(json_data["findings"]) == 1
    assert json_data["findings"][0]["severity"] == "medium"