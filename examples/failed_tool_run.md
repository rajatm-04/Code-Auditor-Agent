# Sample Run 3: Graceful Failure Recovery Demonstrations

This document demonstrates the agent's resilience and self-correction across two distinct failure scenarios:
1. **Invalid / Non-Existent Repository URL**
2. **Missing External Static Analysis Binaries (`ruff` / `bandit`)**

---

## Scenario 1: Non-Existent Repository (Graceful 404 Recovery)

**Command:**
```bash
python main.py --repo https://github.com/nonexistent-user-12345/fake-repo-xyz
```

### Terminal Output:
```text
+-----------------------------------------------------------------+
| Autonomous GitHub Code-Quality Auditor                          |
| Target Repo: https://github.com/nonexistent-user-12345/fake-repo|
| Audit Focus: all                                                |
| LLM Model: gemini/gemini-3.5-flash-lite                         |
+-----------------------------------------------------------------+

Autonomous Audit Execution Plan
+------+-------------------------------------------------------------------+-----------+
| Step | Description                                                       |  Status   |
+------+-------------------------------------------------------------------+-----------+
|  1   | Validate repository URL and test connectivity                     | COMPLETED |
|  2   | Retrieve repository metadata and directory tree                   |  FAILED   |
|  3   | Filter and download key source code files                         |  PENDING  |
|  4   | Run deterministic file analysis & heuristic checks                |  PENDING  |
|  5   | Run external static analysis (with graceful degradation)          |  PENDING  |
|  6   | Synthesize evidence and invoke LLM code review                    |  PENDING  |
|  7   | Validate LLM findings against retrieved code (anti-hallucination) |  PENDING  |
|  8   | Generate final Markdown and JSON audit reports                    |  PENDING  |
+------+-------------------------------------------------------------------+-----------+

GitHub Access Error: Resource not found (404) at 'https://api.github.com/repos/nonexistent-user-12345/fake-repo-xyz'. Verify repository existence and access permissions.
```

### Self-Correction & Resilience Highlights:
- **No unhandled tracebacks:** Caught cleanly via `GitHubToolError`.
- **Recorded in ToolEvent:** Logged as `status="failed"` with recovery note: `"Halted execution; cannot access repository tree."`
- **Clean exit:** Exits with code 1 and an informative user guidance message.

---

## Scenario 2: Graceful Degradation on Missing Linters

When external tools like `ruff` or `bandit` are missing from the system environment, the agent does **not** crash with `FileNotFoundError`. It automatically catches the missing binary, logs graceful degradation, and proceeds with the audit:

```text
| Tool   | Status        | Duration (s) | Notes / Recovery Action                                                   |
| :----- | :------------ | :----------- | :------------------------------------------------------------------------ |
| ruff   | `unavailable` | 0.01         | Skipped ruff linting; continuing audit with heuristic analysis.           |
| bandit | `unavailable` | 0.01         | Skipped bandit security scan; falling back to pattern-based secret scan. |
```

The final report transparently discloses this under **Audit Limitations**:
- *"Static check 'ruff' was unavailable or failed: Skipped ruff linting; continuing audit with heuristic analysis."*
- *"Static check 'bandit' was unavailable or failed: Skipped bandit security scan; falling back to pattern-based secret scan."*
