# Code Quality Audit Report: bottle
**Repository URL:** [https://github.com/bottlepy/bottle](https://github.com/bottlepy/bottle)  
**Audit Timestamp:** 2026-09-28 09:24:07  
**Primary Language:** Python  

## Repository Overview
| Metric | Value |
| :--- | :--- |
| Files Analyzed | 31 |
| Source Files | 31 |
| Test Files | 29 |
| Lines Analyzed | 9,278 |

## Executive Summary
LLM review could not be completed. Deterministic metrics are retained.

## Findings Summary
**Total Findings:** 0 | 🚨 Critical: 0 | ⚠️ High: 0 | 🟡 Medium: 0 | ℹ️ Low: 0

## Detailed Findings
_No major issues flagged by audit tools or reviewer._

## Tool Execution & Resilience Trace
Shows tool invocations, status, and graceful recoveries executed during the audit:

| Tool | Status | Duration (s) | Notes / Recovery Action |
| :--- | :--- | :--- | :--- |
| **GitHub URL Parser** | `success` | 0.00 | Validated owner='bottlepy', repo='bottle' |
| **GitHub Tree & Metadata API** | `success` | 1.12 | Found 219 files; primary language: Python |
| **GitHub File Downloader** | `success` | 10.30 | Downloaded 31 files (0 skipped/failed) |
| **Deterministic File Analyzer** | `success` | 0.07 | Analyzed 31 files, 9278 lines. Found 17 TODOs, 0 potential secrets, 3 broad c... |
| **ruff** | `unavailable` | 0.01 | Skipped ruff linting; continuing audit with heuristic analysis. |
| **bandit** | `unavailable` | 0.01 | Skipped bandit security scan; falling back to pattern-based secret scan. |
| **LLM (Gemini: gemini-3.5-flash)** | `failed` | 43.09 | Falling back to deterministic heuristic summary. |
| **Finding Validator** | `success` | 0.00 | Validated 0 findings (0 hallucinated findings rejected). |

## Audit Limitations
- Static check 'ruff' was unavailable or failed: Skipped ruff linting; continuing audit with heuristic analysis.
- Static check 'bandit' was unavailable or failed: Skipped bandit security scan; falling back to pattern-based secret scan.
- LLM Review degraded: Gemini API returned HTTP 503: {
  "error": {
    "code": 503,
    "message": "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.",
    "status": "UNAVAILABLE"
  }
}

