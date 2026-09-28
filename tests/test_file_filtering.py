"""Tests for file extension and test naming classification."""

from src.tools.file_analyzer import FileAnalyzer


def test_is_supported_source():
    assert FileAnalyzer.is_supported_source("app.py") is True
    assert FileAnalyzer.is_supported_source("main.go") is True
    assert FileAnalyzer.is_supported_source("index.ts") is True
    assert FileAnalyzer.is_supported_source("Service.java") is True
    assert FileAnalyzer.is_supported_source("README.md") is False
    assert FileAnalyzer.is_supported_source("image.png") is False
    assert FileAnalyzer.is_supported_source("package-lock.json") is False


def test_is_test_file():
    assert FileAnalyzer.is_test_file("tests/test_api.py") is True
    assert FileAnalyzer.is_test_file("src/test_login.py") is True
    assert FileAnalyzer.is_test_file("src/utils_test.py") is True
    assert FileAnalyzer.is_test_file("components/Button.spec.tsx") is True
    assert FileAnalyzer.is_test_file("components/Button.test.js") is True
    assert FileAnalyzer.is_test_file("src/models/user.py") is False
    assert FileAnalyzer.is_test_file("server/routes.ts") is False