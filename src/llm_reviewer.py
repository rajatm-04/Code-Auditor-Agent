"""
LLM Reviewer module leveraging LiteLLM for universal multi-provider support.
Feeds deterministic tool evidence to the model to produce evidence-backed findings.
"""

import json
import os
import re
import time
from typing import Any, Optional

import litellm
from src.models import Finding, LLMResponse, ToolEvent

# Suppress noisy litellm debug logs
litellm.suppress_debug_info = True


class LLMReviewer:
    """Manages prompting and structured response parsing from LLMs via LiteLLM."""

    DEFAULT_MODEL = "gemini/gemini-3.5-flash"

    SYSTEM_PROMPT = """You are an elite autonomous code-quality auditor.
Your job is to perform a rigorous, evidence-based code review on a software repository.

CRITICAL RULES:
1. Only report real issues with concrete evidence from the provided code and metrics.
2. DO NOT hallucinate files, functions, or lines that do not exist in the provided source files.
3. Every finding MUST cite:
   - exact file path
   - approximate line start/end if identifiable
   - literal evidence snippet from the code
   - clear explanation of the impact
   - actionable recommendation
4. Assign an honest confidence score between 0.0 and 1.0.
5. If the repository is clean or lacks evidence for high-severity issues, do not invent issues.

OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object matching this schema:
{
  "executive_summary": "Concise high-level quality evaluation",
  "findings": [
    {
      "title": "Clear description of the issue",
      "severity": "critical", 
      "category": "security",
      "file": "path/to/file.py",
      "line_start": 10,
      "line_end": 12,
      "evidence": "code snippet",
      "impact": "why this is dangerous",
      "recommendation": "how to resolve",
      "confidence": 0.95
    }
  ]
}
Allowed severity values: "critical", "high", "medium", "low"
Allowed category values: "bug", "security", "testing", "maintainability", "performance", "reliability"
"""

    def __init__(self, model: Optional[str] = None):
        """Initialize reviewer with a specific litellm model string."""
        self.model = model or os.getenv("LLM_MODEL") or self.DEFAULT_MODEL
        if not self.model.startswith("gemini/") and "gpt" not in self.model and "claude" not in self.model:
            self.model = f"gemini/{self.model}"

    def _build_user_prompt(
        self,
        repo_name: str,
        focus: str,
        repo_stats: dict[str, Any],
        static_events: list[ToolEvent],
        sample_files: dict[str, str],
    ) -> str:
        """Constructs an evidence bundle prompt for the LLM."""
        static_summary_lines = []
        for ev in static_events:
            status_desc = ev.status
            if ev.result:
                status_desc += f": {ev.result[:150]}..."
            elif ev.error:
                status_desc += f": {ev.error}"
            static_summary_lines.append(f"- {ev.tool} ({status_desc})")
        static_summary = "\n".join(static_summary_lines) if static_summary_lines else "No static tools executed."

        # Prioritize files with detected smells first
        smell_files = set(
            repo_stats.get("files_with_broad_exceptions", [])
            + repo_stats.get("files_with_secrets", [])
        )
        sorted_files = sorted(sample_files.keys(), key=lambda p: 0 if p in smell_files else 1)

        file_excerpts = []
        char_count = 0
        MAX_CHAR_BUDGET = 10_000

        for path in sorted_files:
            if char_count >= MAX_CHAR_BUDGET:
                break
            content = sample_files[path]
            lines = content.splitlines()[:100]
            snippet = "\n".join(lines)
            char_count += len(snippet)
            file_excerpts.append(f"--- FILE: {path} ---\n{snippet}\n")

        files_text = "\n".join(file_excerpts)

        return f"""AUDIT REQUEST FOR REPOSITORY: {repo_name}
AUDIT FOCUS: {focus}

=== 1. DETERMINISTIC REPO METRICS ===
- Total files analyzed: {repo_stats.get('total_files_analyzed', 0)}
- Source code files: {repo_stats.get('source_files_count', 0)}
- Test files: {repo_stats.get('test_files_count', 0)}
- Test-to-source ratio: {repo_stats.get('test_to_source_ratio', 0.0)}
- Total lines analyzed: {repo_stats.get('total_lines', 0)}
- Total TODO/FIXME tags: {repo_stats.get('total_todos', 0)}
- Files with potential secret patterns: {repo_stats.get('files_with_secrets', [])}
- Files with broad exception catches: {repo_stats.get('files_with_broad_exceptions', [])}

=== 2. STATIC ANALYSIS TOOL RESULTS ===
{static_summary}

=== 3. SOURCE CODE EXCERPTS (PRIORITIZED) ===
{files_text}

Analyze the above evidence and output a single JSON object with your executive_summary and deeper architectural findings.
Prioritize issues matching the audit focus: '{focus}'.
"""

    def review(
        self,
        repo_name: str,
        focus: str,
        repo_stats: dict[str, Any],
        static_events: list[ToolEvent],
        sample_files: dict[str, str],
    ) -> tuple[LLMResponse, ToolEvent]:
        """Executes LLM review via LiteLLM and returns (LLMResponse, ToolEvent)."""
        start_time = time.time()
        user_prompt = self._build_user_prompt(
            repo_name=repo_name,
            focus=focus,
            repo_stats=repo_stats,
            static_events=static_events,
            sample_files=sample_files,
        )

        for attempt in range(3):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    timeout=60,
                )

                raw_content = response.choices[0].message.content or "{}"
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_content.strip())
                cleaned = re.sub(r"\s*```$", "", cleaned)

                llm_response = LLMResponse.model_validate_json(cleaned)
                duration = round(time.time() - start_time, 2)

                event = ToolEvent(
                    tool=f"LLM ({self.model})",
                    status="success",
                    result=f"Generated executive summary and {len(llm_response.findings)} AI findings.",
                    duration_seconds=duration,
                )
                return llm_response, event

            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "429" in err_str) and attempt < 2:
                    time.sleep(3)
                    continue

                duration = round(time.time() - start_time, 2)
                event = ToolEvent(
                    tool=f"LLM ({self.model})",
                    status="failed",
                    error=err_str,
                    recovery="Retaining deterministic heuristic findings as baseline audit.",
                    duration_seconds=duration,
                )
                fallback_response = LLMResponse(
                    executive_summary=(
                        f"Audit completed using deterministic analysis of {repo_stats.get('total_files_analyzed', 0)} files "
                        f"({repo_stats.get('total_lines', 0):,} lines). Heuristic smells and structural metrics were verified."
                    ),
                    findings=[],
                )
                return fallback_response, event