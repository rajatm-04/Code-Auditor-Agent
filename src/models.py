"""
Data models for the Autonomous GitHub Code-Quality Auditor.
Uses Pydantic v2 for robust validation and automated JSON serialization.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ToolEvent(BaseModel):
    """Tracks each tool invocation during the audit (demonstrates tool usage & recovery)."""
    tool: str
    status: Literal["success", "failed", "unavailable", "timeout"]
    result: Optional[str] = None
    error: Optional[str] = None
    recovery: Optional[str] = None
    duration_seconds: Optional[float] = None


class Finding(BaseModel):
    """A single code-quality finding detected in the repository."""
    title: str
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal[
        "bug", "security", "testing", "maintainability", "performance", "reliability"
    ]
    file: Optional[str] = None
    line_start: Optional[int] = Field(default=None, ge=1)
    line_end: Optional[int] = Field(default=None, ge=1)
    evidence: str
    impact: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)


class RepositorySummary(BaseModel):
    """Metadata and high-level statistics about the inspected repository."""
    url: str
    name: str
    primary_language: Optional[str] = None
    files_analyzed: int = 0
    source_files: int = 0
    test_files: int = 0
    lines_analyzed: int = 0
    limitations: list[str] = []


class LLMResponse(BaseModel):
    """Schema sent to LiteLLM for structured output enforcement."""
    executive_summary: str
    findings: list[Finding]


class AuditReport(BaseModel):
    """Final comprehensive audit report containing summaries, findings, and tool traces."""
    repository: RepositorySummary
    executive_summary: str
    findings: list[Finding]
    tool_events: list[ToolEvent]
    timestamp: datetime = Field(default_factory=datetime.now)


class PlanStep(BaseModel):
    """Represents a single step in the agent's visible execution plan."""
    step: int
    description: str
    status: Literal["pending", "running", "done", "failed", "skipped"] = "pending"