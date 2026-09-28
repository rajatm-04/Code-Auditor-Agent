"""Tests for post-LLM finding validation and hallucination rejection."""

from src.finding_validator import FindingValidator
from src.models import Finding


def test_finding_validator_keeps_real_files():
    retrieved_files = ["src/app.py", "src/auth.py", "tests/test_auth.py"]

    findings = [
        Finding(
            title="SQL Injection in auth",
            severity="critical",
            category="security",
            file="src/auth.py",
            evidence="query = f'SELECT * FROM users WHERE id={user_id}'",
            impact="Data breach",
            recommendation="Use parameterized queries",
            confidence=0.95,
        ),
        Finding(
            title="Hallucinated issue",
            severity="high",
            category="bug",
            file="src/non_existent_file.py",
            evidence="bad_function()",
            impact="Crash",
            recommendation="Remove it",
            confidence=0.8,
        ),
    ]

    valid, rejected = FindingValidator.validate_findings(findings, retrieved_files)

    assert len(valid) == 1
    assert valid[0].file == "src/auth.py"
    assert len(rejected) == 1
    assert rejected[0]["hallucinated_file"] == "src/non_existent_file.py"