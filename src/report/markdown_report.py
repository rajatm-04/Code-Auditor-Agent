"""
Markdown report generator.
Produces human-readable, beautifully formatted audit reports with execution traces.
"""

import os
from src.models import AuditReport, Finding


class MarkdownReportGenerator:
    """Renders AuditReport models into structured Markdown documents."""

    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    SEVERITY_BADGES = {
        "critical": "🚨 CRITICAL",
        "high": "⚠️ HIGH",
        "medium": "🟡 MEDIUM",
        "low": "ℹ️ LOW",
    }

    @classmethod
    def render(cls, report: AuditReport) -> str:
        """Converts an AuditReport model into a Markdown string."""
        lines: list[str] = []

        # 1. Header & Repository Metadata
        repo = report.repository
        lines.append(f"# Code Quality Audit Report: {repo.name}")
        lines.append(f"**Repository URL:** [{repo.url}]({repo.url})  ")
        lines.append(f"**Audit Timestamp:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**Primary Language:** {repo.primary_language or 'Not specified'}  ")
        lines.append("")

        lines.append("## Repository Overview")
        lines.append("| Metric | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Files Analyzed | {repo.files_analyzed} |")
        lines.append(f"| Source Files | {repo.source_files} |")
        lines.append(f"| Test Files | {repo.test_files} |")
        lines.append(f"| Lines Analyzed | {repo.lines_analyzed:,} |")
        lines.append("")

        # 2. Executive Summary
        lines.append("## Executive Summary")
        lines.append(report.executive_summary.strip())
        lines.append("")

        # 3. Findings Breakdown Summary
        sorted_findings = sorted(
            report.findings,
            key=lambda f: cls.SEVERITY_ORDER.get(f.severity, 99)
        )
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in sorted_findings:
            if f.severity in counts:
                counts[f.severity] += 1

        lines.append("## Findings Summary")
        lines.append(
            f"**Total Findings:** {len(sorted_findings)} | "
            f"🚨 Critical: {counts['critical']} | "
            f"⚠️ High: {counts['high']} | "
            f"🟡 Medium: {counts['medium']} | "
            f"ℹ️ Low: {counts['low']}"
        )
        lines.append("")

        # 4. Detailed Findings
        lines.append("## Detailed Findings")
        if not sorted_findings:
            lines.append("_No major issues flagged by audit tools or reviewer._")
            lines.append("")
        else:
            for i, f in enumerate(sorted_findings, start=1):
                badge = cls.SEVERITY_BADGES.get(f.severity, f.severity.upper())
                file_location = f"`{f.file}`" if f.file else "_Global/Architecture_"
                if f.line_start:
                    file_location += f" (Lines {f.line_start}"
                    if f.line_end and f.line_end != f.line_start:
                        file_location += f"-{f.line_end}"
                    file_location += ")"

                lines.append(f"### {i}. [{badge}] {f.title}")
                lines.append(f"- **Category:** `{f.category}`")
                lines.append(f"- **Location:** {file_location}")
                lines.append(f"- **Confidence:** {int(f.confidence * 100)}%")
                lines.append("")
                lines.append(f"**Evidence:**")
                lines.append("```text")
                lines.append(f.evidence.strip())
                lines.append("```")
                lines.append("")
                lines.append(f"**Impact:** {f.impact}")
                lines.append("")
                lines.append(f"**Recommendation:** {f.recommendation}")
                lines.append("")
                lines.append("---")
                lines.append("")

        # 5. Tool Execution & Recovery Trace
        lines.append("## Tool Execution & Resilience Trace")
        lines.append("Shows tool invocations, status, and graceful recoveries executed during the audit:")
        lines.append("")
        lines.append("| Tool | Status | Duration (s) | Notes / Recovery Action |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for ev in report.tool_events:
            notes = ev.recovery or ev.error or ev.result or "Completed successfully."
            # Truncate notes for markdown table
            notes_clean = notes.replace("\n", " ").replace("|", "\\|")
            if len(notes_clean) > 80:
                notes_clean = notes_clean[:77] + "..."
            dur = f"{ev.duration_seconds:.2f}" if ev.duration_seconds is not None else "-"
            lines.append(f"| **{ev.tool}** | `{ev.status}` | {dur} | {notes_clean} |")
        lines.append("")

        # 6. Audit Limitations
        lines.append("## Audit Limitations")
        if repo.limitations:
            for lim in repo.limitations:
                lines.append(f"- {lim}")
        else:
            lines.append("- Analysis limited to top repository files within character and rate limits.")
        lines.append("")

        return "\n".join(lines)

    @classmethod
    def save(cls, report: AuditReport, output_path: str) -> str:
        """Render and save report to disk."""
        target_file = output_path if output_path.endswith(".md") else f"{output_path}.md"
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        content = cls.render(report)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return target_file