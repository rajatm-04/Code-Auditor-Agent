"""
Deterministic file and repository analyzer.
Extracts code metrics, smell heuristics, and structural stats without an LLM.
"""

import os
import re
from typing import Any


class FileAnalyzer:
    """Analyzes source files and repositories using deterministic rules and heuristics."""

    SOURCE_EXTENSIONS = {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java",
        ".rs", ".c", ".cpp", ".cc", ".h", ".hpp", ".cs",
        ".rb", ".php", ".swift", ".kt", ".scala", ".sh"
    }

    TEST_PATTERNS = [
        r"(?:^|[\\/])test_.*\.py$",
        r".*_test\.py$",
        r"(?:^|[\\/])tests?[\\/].*",
        r".*\.(?:spec|test)\.[jt]sx?$",
        r"(?:^|[\\/])__tests__[\\/].*",
    ]

    # Secret and credential regexes
    SECRET_PATTERNS = [
        (r"""(?i)(?:api_key|apikey|secret|password|passwd|token|auth_token)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]""", "Hardcoded API Key / Secret"),
        (r"""ghp_[a-zA-Z0-9]{36}""", "GitHub Personal Access Token"),
        (r"""AIza[0-9A-Za-z\\-_]{35}""", "Google API Key"),
        (r"""sk-[a-zA-Z0-9]{32,}""", "OpenAI Secret Key"),
    ]

    # Broad exception patterns across languages
    BROAD_EXCEPTION_PATTERNS = [
        (r"except\s*:", "Bare except clause (Python)"),
        (r"except\s+Exception\s*:", "Catch-all Exception without specificity (Python)"),
        (r"catch\s*\(\s*Exception\s+\w+\s*\)", "Broad Exception catch (Java/C#)"),
        (r"catch\s*\(\s*\w+\s*\)\s*\{\s*\}", "Empty catch block"),
    ]

    @classmethod
    def is_supported_source(cls, path: str) -> bool:
        """Check if the file is a recognized source code file."""
        _, ext = os.path.splitext(path.lower())
        return ext in cls.SOURCE_EXTENSIONS

    @classmethod
    def is_test_file(cls, path: str) -> bool:
        """Determine if a file is a test/spec file by naming conventions and path."""
        norm_path = path.replace("\\", "/")
        return any(re.search(pat, norm_path, re.IGNORECASE) for pat in cls.TEST_PATTERNS)

    @classmethod
    def analyze_file(cls, path: str, content: str) -> dict[str, Any]:
        """
        Analyze an individual file and return quantitative metrics and smell indicators.
        """
        lines = content.splitlines()
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        code_lines = total_lines - blank_lines

        long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 120]
        
        # Search for TODO / FIXME annotations
        todos: list[dict[str, Any]] = []
        for i, line in enumerate(lines, start=1):
            match = re.search(r"\b(TODO|FIXME|HACK|XXX)\b(?::?\s*(.*))?", line, re.IGNORECASE)
            if match:
                todos.append({
                    "line": i,
                    "tag": match.group(1).upper(),
                    "comment": match.group(2).strip() if match.group(2) else ""
                })

        # Search for potential secrets
        secrets_found: list[dict[str, Any]] = []
        for i, line in enumerate(lines, start=1):
            for pat, desc in cls.SECRET_PATTERNS:
                if re.search(pat, line):
                    secrets_found.append({
                        "line": i,
                        "description": desc
                    })

        # Search for broad exceptions
        broad_exceptions: list[dict[str, Any]] = []
        for i, line in enumerate(lines, start=1):
            for pat, desc in cls.BROAD_EXCEPTION_PATTERNS:
                if re.search(pat, line):
                    broad_exceptions.append({
                        "line": i,
                        "description": desc
                    })

        return {
            "path": path,
            "is_source": cls.is_supported_source(path),
            "is_test": cls.is_test_file(path),
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "long_lines_count": len(long_lines),
            "todos": todos,
            "secrets": secrets_found,
            "broad_exceptions": broad_exceptions,
        }

    @classmethod
    def analyze_repository(cls, files: dict[str, str]) -> dict[str, Any]:
        """
        Aggregate file analysis into a repository-wide statistics bundle.
        files: dict mapping path -> file_content
        """
        file_metrics = []
        source_count = 0
        test_count = 0
        total_lines = 0

        files_with_secrets = []
        files_with_broad_exceptions = []
        all_todos_count = 0

        for path, content in files.items():
            metrics = cls.analyze_file(path, content)
            file_metrics.append(metrics)

            if metrics["is_source"]:
                source_count += 1
            if metrics["is_test"]:
                test_count += 1

            total_lines += metrics["total_lines"]
            all_todos_count += len(metrics["todos"])

            if metrics["secrets"]:
                files_with_secrets.append(path)
            if metrics["broad_exceptions"]:
                files_with_broad_exceptions.append(path)

        test_ratio = round(test_count / max(source_count, 1), 2)
        avg_lines_per_file = round(total_lines / max(len(files), 1), 1)

        return {
            "total_files_analyzed": len(files),
            "source_files_count": source_count,
            "test_files_count": test_count,
            "test_to_source_ratio": test_ratio,
            "total_lines": total_lines,
            "avg_lines_per_file": avg_lines_per_file,
            "total_todos": all_todos_count,
            "files_with_secrets": files_with_secrets,
            "files_with_broad_exceptions": files_with_broad_exceptions,
            "details": file_metrics,
        }