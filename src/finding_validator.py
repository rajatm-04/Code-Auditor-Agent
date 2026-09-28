"""
Post-LLM finding validator.
Ensures every finding references a real file that was actually retrieved (anti-hallucination).
"""

from typing import Any
from src.models import Finding


class FindingValidator:
    """Validates findings produced by LLMs against retrieved ground-truth repository files."""

    @classmethod
    def validate_findings(
        cls,
        findings: list[Finding],
        retrieved_files: list[str],
    ) -> tuple[list[Finding], list[dict[str, Any]]]:
        """
        Filters out hallucinated findings.
        Returns:
            valid_findings: List of verified Finding objects.
            rejected: List of rejected finding records with rationale.
        """
        valid: list[Finding] = []
        rejected: list[dict[str, Any]] = []

        retrieved_set = set(retrieved_files)

        for finding in findings:
            # If no file is specified (e.g. general repo architecture note), allow it
            if not finding.file:
                valid.append(finding)
                continue

            # Check if file exists in the retrieved files
            norm_file = finding.file.replace("\\", "/").strip()
            
            # Direct match or suffix match (e.g. 'src/app.py' matching 'app.py' or vice versa)
            matched = norm_file in retrieved_set or any(
                f.endswith(norm_file) or norm_file.endswith(f) for f in retrieved_set
            )

            if matched:
                valid.append(finding)
            else:
                rejected.append({
                    "title": finding.title,
                    "hallucinated_file": finding.file,
                    "reason": f"Referenced file '{finding.file}' was not found in retrieved repository files.",
                })

        return valid, rejected