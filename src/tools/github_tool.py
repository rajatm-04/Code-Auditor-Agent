"""
GitHub API Tool for fetching repository metadata, directory trees, and file contents.
Supports unauthenticated requests (60 req/hr) and token-authenticated requests (5000 req/hr).
"""

import base64
import os
import re
from typing import Any, Optional
import requests


class GitHubToolError(Exception):
    """Custom exception raised when a GitHub API operation fails."""
    pass


class GitHubTool:
    """Tool for interacting with GitHub repositories via the GitHub REST API."""

    BASE_URL = "https://api.github.com"

    # Safety limits to avoid overflowing LLM context or memory
    MAX_FILES = 250
    MAX_FILE_SIZE = 250_000        # 250 KB per file (covers nearly all single code files)
    MAX_TOTAL_CHARS = 600_000

    # Paths and file types to exclude from code audits
    EXCLUDED_DIRS = {
        ".git", "node_modules", "venv", ".venv", "dist", "build",
        "__pycache__", ".pytest_cache", ".idea", ".vscode", "vendor",
        "egg-info", ".mypy_cache"
    }
    EXCLUDED_EXTENSIONS = {
        ".lock", ".min.js", ".min.css", ".map", ".png", ".jpg", ".jpeg",
        ".gif", ".ico", ".svg", ".pyc", ".exe", ".dll", ".so", ".dylib",
        ".zip", ".tar", ".gz", ".woff", ".woff2", ".ttf", ".pdf"
    }

    def __init__(self, token: Optional[str] = None):
        """Initialize with optional GitHub personal access token."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Autonomous-Code-Auditor/1.0"
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        """
        Extract (owner, repo) from a GitHub repository URL.
        Handles trailing slashes, .git suffix, and various URL structures.
        """
        if not url or not isinstance(url, str):
            raise GitHubToolError("Repository URL must be a non-empty string.")

        pattern = r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$"
        match = re.match(pattern, url.strip())
        if not match:
            raise GitHubToolError(
                f"Invalid GitHub repository URL: '{url}'. "
                "Expected format: https://github.com/owner/repository"
            )

        owner, repo = match.group(1), match.group(2)
        return owner, repo

    def _request(self, endpoint: str) -> dict[str, Any]:
        """Internal helper to execute GET requests with clean error propagation."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, timeout=15)
        except requests.RequestException as e:
            raise GitHubToolError(f"Network error connecting to GitHub: {str(e)}")

        if response.status_code == 404:
            raise GitHubToolError(f"Resource not found (404) at '{url}'. Verify repository existence and access permissions.")
        elif response.status_code == 403:
            msg = "GitHub API rate limit exceeded (403)."
            if not self.token:
                msg += " Provide GITHUB_TOKEN in .env for 5,000 requests/hour."
            raise GitHubToolError(msg)
        elif response.status_code != 200:
            raise GitHubToolError(f"GitHub API error {response.status_code}: {response.text}")

        return response.json()

    def get_repository(self, url: str) -> dict[str, Any]:
        """Fetch general repository information and default branch."""
        owner, repo = self.parse_url(url)
        data = self._request(f"/repos/{owner}/{repo}")
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description") or "",
            "default_branch": data.get("default_branch", "main"),
            "primary_language": data.get("language") or "Unknown",
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
        }

    def get_tree(self, url: str, branch: Optional[str] = None) -> list[str]:
        """
        Fetch complete list of repository file paths using recursive git tree.
        Filters out directories and excluded files.
        """
        owner, repo = self.parse_url(url)
        if not branch:
            repo_info = self.get_repository(url)
            branch = repo_info["default_branch"]

        data = self._request(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
        if data.get("truncated"):
            # Tree was truncated by GitHub (>100k entries)
            pass

        tree_items = data.get("tree", [])
        filtered_files: list[str] = []

        for item in tree_items:
            # We only want blobs (files), not trees (directories)
            if item.get("type") != "blob":
                continue

            path = item.get("path", "")
            parts = path.split("/")

            # Check if any parent folder is in EXCLUDED_DIRS
            if any(part in self.EXCLUDED_DIRS for part in parts[:-1]):
                continue

            # Check extension
            _, ext = os.path.splitext(path.lower())
            if ext in self.EXCLUDED_EXTENSIONS:
                continue

            filtered_files.append(path)

            if len(filtered_files) >= self.MAX_FILES:
                break

        return filtered_files

    def get_file(self, url: str, path: str, branch: Optional[str] = None) -> str:
        """
        Fetch and decode content of a specific file from the repository.
        """
        owner, repo = self.parse_url(url)
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        if branch:
            endpoint += f"?ref={branch}"

        data = self._request(endpoint)

        if data.get("size", 0) > self.MAX_FILE_SIZE:
            raise GitHubToolError(f"File '{path}' exceeds max allowed size ({self.MAX_FILE_SIZE} bytes).")

        content_encoded = data.get("content", "")
        encoding = data.get("encoding", "")

        if encoding == "base64":
            try:
                decoded_bytes = base64.b64decode(content_encoded)
                return decoded_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                raise GitHubToolError(f"Failed to decode file '{path}': {str(e)}")
        else:
            return content_encoded