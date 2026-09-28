"""Tests for GitHub URL validation and extraction."""

import pytest
from src.tools.github_tool import GitHubTool, GitHubToolError


def test_valid_github_urls():
    assert GitHubTool.parse_url("https://github.com/psf/requests") == ("psf", "requests")
    assert GitHubTool.parse_url("https://github.com/psf/requests.git") == ("psf", "requests")
    assert GitHubTool.parse_url("https://github.com/psf/requests/") == ("psf", "requests")
    assert GitHubTool.parse_url("http://github.com/pallets/flask") == ("pallets", "flask")
    assert GitHubTool.parse_url("https://www.github.com/torvalds/linux") == ("torvalds", "linux")


def test_invalid_github_urls():
    invalid_cases = [
        "",
        "not-a-url",
        "https://gitlab.com/owner/repo",
        "https://bitbucket.org/owner/repo",
        "https://github.com/",
        "https://github.com/incomplete",
    ]
    for url in invalid_cases:
        with pytest.raises(GitHubToolError):
            GitHubTool.parse_url(url)