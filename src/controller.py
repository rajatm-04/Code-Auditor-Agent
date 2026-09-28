"""
Central Execution Controller for the Autonomous GitHub Code-Quality Auditor.
Orchestrates an 8-step execution plan, collects tool events, handles failures gracefully,
and produces comprehensive audit reports.
"""

import time
from typing import Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.finding_validator import FindingValidator
from src.llm_reviewer import LLMReviewer
from src.logging_config import setup_logging
from src.models import AuditReport, PlanStep, RepositorySummary, ToolEvent
from src.report.json_report import JsonReportGenerator
from src.report.markdown_report import MarkdownReportGenerator
from src.tools.file_analyzer import FileAnalyzer
from src.tools.github_tool import GitHubTool, GitHubToolError
from src.tools.static_analysis import StaticAnalysisTool


class AuditController:
    """Orchestrates the entire repository audit workflow."""

    PLAN_STEPS = [
        "Validate repository URL and test connectivity",
        "Retrieve repository metadata and directory tree",
        "Filter and download key source code files",
        "Run deterministic file analysis & heuristic checks",
        "Run external static analysis (with graceful degradation)",
        "Synthesize evidence and invoke LLM code review",
        "Validate LLM findings against retrieved code (anti-hallucination)",
        "Generate final Markdown and JSON audit reports",
    ]

    def __init__(
        self,
        repo_url: str,
        focus: str = "all",
        model: Optional[str] = None,
        output_prefix: str = "outputs/report",
        github_token: Optional[str] = None,
        verbose: bool = False,
    ):
        self.repo_url = repo_url.strip()
        self.focus = focus
        self.model = model
        self.output_prefix = output_prefix
        self.console = Console()
        self.logger = setup_logging(f"{output_prefix}_execution.log", verbose=verbose)

        # Initialize tools
        self.github_tool = GitHubTool(token=github_token)
        self.file_analyzer = FileAnalyzer()
        self.llm_reviewer = LLMReviewer(model=model)

        # Execution tracking
        self.tool_events: list[ToolEvent] = []
        self.steps: list[PlanStep] = [
            PlanStep(step=i + 1, description=desc, status="pending")
            for i, desc in enumerate(self.PLAN_STEPS)
        ]

    def _render_plan(self):
        """Displays the execution plan table with real-time status badges in terminal."""
        table = Table(title="📋 Autonomous Audit Execution Plan", border_style="cyan")
        table.add_column("Step", justify="center", style="bold")
        table.add_column("Description", style="white")
        table.add_column("Status", justify="center")

        status_styles = {
            "pending": "[grey50]⏳ PENDING[/grey50]",
            "running": "[yellow]🔄 RUNNING[/yellow]",
            "done": "[green]✅ COMPLETED[/green]",
            "failed": "[red]❌ FAILED[/red]",
            "skipped": "[blue]⏭️ SKIPPED[/blue]",
        }

        for s in self.steps:
            table.add_row(str(s.step), s.description, status_styles.get(s.status, s.status))

        self.console.print(table)
        self.console.print("")

    def _set_step_status(self, step_num: int, status: str):
        """Updates the status of a specific plan step."""
        self.steps[step_num - 1].status = status

    def run(self) -> Optional[AuditReport]:
        """
        Executes the 8-step audit workflow.
        Returns the finalized AuditReport or None if fatal initialization failed.
        """
        self.console.print(
            Panel.fit(
                f"[bold cyan]Autonomous GitHub Code-Quality Auditor[/bold cyan]\n"
                f"[white]Target Repo:[/white] [green]{self.repo_url}[/green]\n"
                f"[white]Audit Focus:[/white] [yellow]{self.focus}[/yellow]\n"
                f"[white]LLM Model:[/white] [magenta]{self.llm_reviewer.model}[/magenta]",
                border_style="bright_blue",
            )
        )
        self._render_plan()

        limitations: list[str] = []
        repo_metadata: dict[str, Any] = {}
        all_tree_files: list[str] = []
        downloaded_files: dict[str, str] = {}
        repo_stats: dict[str, Any] = {}
        static_events: list[ToolEvent] = []

        # =========================================================================
        # Step 1: Validate URL & connectivity
        # =========================================================================
        self._set_step_status(1, "running")
        start_t = time.time()
        try:
            owner, repo_name = self.github_tool.parse_url(self.repo_url)
            self.logger.info(f"Validated URL: owner='{owner}', repo='{repo_name}'")
            self.tool_events.append(
                ToolEvent(
                    tool="GitHub URL Parser",
                    status="success",
                    result=f"Validated owner='{owner}', repo='{repo_name}'",
                    duration_seconds=round(time.time() - start_t, 2),
                )
            )
            self._set_step_status(1, "done")
        except GitHubToolError as e:
            self._set_step_status(1, "failed")
            self.tool_events.append(
                ToolEvent(
                    tool="GitHub URL Parser",
                    status="failed",
                    error=str(e),
                    recovery="Halted execution; please check repository URL format.",
                    duration_seconds=round(time.time() - start_t, 2),
                )
            )
            self.console.print(f"[bold red]❌ Error:[/bold red] {str(e)}")
            return None

        # =========================================================================
        # Step 2: Retrieve metadata & directory tree
        # =========================================================================
        self._set_step_status(2, "running")
        start_t = time.time()
        try:
            repo_metadata = self.github_tool.get_repository(self.repo_url)
            all_tree_files = self.github_tool.get_tree(
                self.repo_url, branch=repo_metadata.get("default_branch")
            )
            self.tool_events.append(
                ToolEvent(
                    tool="GitHub Tree & Metadata API",
                    status="success",
                    result=f"Found {len(all_tree_files)} files; primary language: {repo_metadata.get('primary_language')}",
                    duration_seconds=round(time.time() - start_t, 2),
                )
            )
            self._set_step_status(2, "done")
        except GitHubToolError as e:
            self._set_step_status(2, "failed")
            self.tool_events.append(
                ToolEvent(
                    tool="GitHub Tree & Metadata API",
                    status="failed",
                    error=str(e),
                    recovery="Halted execution; cannot access repository tree.",
                    duration_seconds=round(time.time() - start_t, 2),
                )
            )
            self.console.print(f"[bold red]❌ GitHub Access Error:[/bold red] {str(e)}")
            return None

        # =========================================================================
        # Step 3: Filter & download key source files
        # =========================================================================
        self._set_step_status(3, "running")
        start_t = time.time()
        # Filter for source files, prioritize smaller files first
        target_files = [
            f for f in all_tree_files if self.file_analyzer.is_supported_source(f)
        ][: self.github_tool.MAX_FILES]

        download_errors = 0
        for f_path in target_files:
            try:
                content = self.github_tool.get_file(
                    self.repo_url, f_path, branch=repo_metadata.get("default_branch")
                )
                downloaded_files[f_path] = content
            except GitHubToolError as e:
                download_errors += 1
                self.logger.warning(f"Failed to download {f_path}: {e}")

        if download_errors > 0:
            limitations.append(f"Failed to retrieve {download_errors} files due to size or encoding limits.")

        self.tool_events.append(
            ToolEvent(
                tool="GitHub File Downloader",
                status="success" if downloaded_files else "failed",
                result=f"Downloaded {len(downloaded_files)} files ({download_errors} skipped/failed)",
                duration_seconds=round(time.time() - start_t, 2),
            )
        )
        self._set_step_status(3, "done")

        # =========================================================================
        # Step 4: Run deterministic file & heuristic analysis
        # =========================================================================
        self._set_step_status(4, "running")
        start_t = time.time()
        repo_stats = self.file_analyzer.analyze_repository(downloaded_files)
        self.tool_events.append(
            ToolEvent(
                tool="Deterministic File Analyzer",
                status="success",
                result=(
                    f"Analyzed {repo_stats['total_files_analyzed']} files, "
                    f"{repo_stats['total_lines']} lines. Found {repo_stats['total_todos']} TODOs, "
                    f"{len(repo_stats['files_with_secrets'])} potential secrets, "
                    f"{len(repo_stats['files_with_broad_exceptions'])} broad catches."
                ),
                duration_seconds=round(time.time() - start_t, 2),
            )
        )
        self._set_step_status(4, "done")

        # =========================================================================
        # Step 5: External static analysis with graceful degradation
        # =========================================================================
        self._set_step_status(5, "running")
        # Run ruff and bandit (against local dir or gracefully degrade)
        static_events = StaticAnalysisTool.run_all(".")
        self.tool_events.extend(static_events)
        for ev in static_events:
            if ev.status != "success":
                limitations.append(f"Static check '{ev.tool}' was unavailable or failed: {ev.recovery}")
        self._set_step_status(5, "done")

        # =========================================================================
        # Step 6: LLM evidence synthesis and review
        # =========================================================================
        self._set_step_status(6, "running")
        llm_resp, llm_event = self.llm_reviewer.review(
            repo_name=repo_metadata.get("name", "Unknown"),
            focus=self.focus,
            repo_stats=repo_stats,
            static_events=static_events,
            sample_files=downloaded_files,
        )
        self.tool_events.append(llm_event)
        if llm_event.status != "success":
            limitations.append(f"LLM Review degraded: {llm_event.error}")
            self._set_step_status(6, "failed")
        else:
            self._set_step_status(6, "done")

        # =========================================================================
        # Step 7: Anti-hallucination finding validation
        # =========================================================================
        self._set_step_status(7, "running")
        start_t = time.time()
        valid_findings, rejected_findings = FindingValidator.validate_findings(
            findings=llm_resp.findings,
            retrieved_files=list(downloaded_files.keys()),
        )
        for rej in rejected_findings:
            self.logger.warning(f"Filtered hallucinated finding: {rej['title']} -> {rej['reason']}")
            limitations.append(f"Discarded unverified finding '{rej['title']}' referencing non-existent file.")

        self.tool_events.append(
            ToolEvent(
                tool="Finding Validator",
                status="success",
                result=f"Validated {len(valid_findings)} findings ({len(rejected_findings)} hallucinated findings rejected).",
                duration_seconds=round(time.time() - start_t, 2),
            )
        )
        self._set_step_status(7, "done")

        # =========================================================================
        # Step 8: Build models and export reports
        # =========================================================================
        self._set_step_status(8, "running")
        summary_model = RepositorySummary(
            url=self.repo_url,
            name=repo_metadata.get("name", "Unknown Repo"),
            primary_language=repo_metadata.get("primary_language"),
            files_analyzed=repo_stats.get("total_files_analyzed", 0),
            source_files=repo_stats.get("source_files_count", 0),
            test_files=repo_stats.get("test_files_count", 0),
            lines_analyzed=repo_stats.get("total_lines", 0),
            limitations=limitations,
        )

        audit_report = AuditReport(
            repository=summary_model,
            executive_summary=llm_resp.executive_summary,
            findings=valid_findings,
            tool_events=self.tool_events,
        )

        md_path = MarkdownReportGenerator.save(audit_report, self.output_prefix)
        json_path = JsonReportGenerator.save(audit_report, self.output_prefix)
        self._set_step_status(8, "done")

        # Final terminal summary
        self.console.print("")
        self._render_plan()
        self.console.print(
            Panel.fit(
                f"[bold green] Audit Complete![/bold green]\n"
                f"[white]Markdown Report:[/white] [cyan]{md_path}[/cyan]\n"
                f"[white]JSON Report:[/white]     [cyan]{json_path}[/cyan]\n"
                f"[white]Execution Log:[/white]   [cyan]{self.output_prefix}_execution.log[/cyan]",
                border_style="green",
            )
        )

        return audit_report