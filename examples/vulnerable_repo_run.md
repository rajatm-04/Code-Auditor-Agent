# Sample Run 2: Vulnerable Codebase Audit (we45/Vulnerable-Flask-App)

**Target Repository:** `https://github.com/we45/Vulnerable-Flask-App`  
**Command:**
```bash
python main.py --repo https://github.com/we45/Vulnerable-Flask-App --focus security
```

---

## 1. Terminal Execution Trace

```text
+-------------------------------------------------------------+
| Autonomous GitHub Code-Quality Auditor                      |
| Target Repo: https://github.com/we45/Vulnerable-Flask-App   |
| Audit Focus: security                                       |
| LLM Model: gemini/gemini-3.5-flash-lite                     |
+-------------------------------------------------------------+

Autonomous Audit Execution Plan
+------+-------------------------------------------------------------------+-----------+
| Step | Description                                                       |  Status   |
+------+-------------------------------------------------------------------+-----------+
|  1   | Validate repository URL and test connectivity                     | COMPLETED |
|  2   | Retrieve repository metadata and directory tree                   | COMPLETED |
|  3   | Filter and download key source code files                         | COMPLETED |
|  4   | Run deterministic file analysis & heuristic checks                | COMPLETED |
|  5   | Run external static analysis (with graceful degradation)          | COMPLETED |
|  6   | Synthesize evidence and invoke LLM code review                    | COMPLETED |
|  7   | Validate LLM findings against retrieved code (anti-hallucination) | COMPLETED |
|  8   | Generate final Markdown and JSON audit reports                    | COMPLETED |
+------+-------------------------------------------------------------------+-----------+

Audit Complete!
Markdown Report: outputs/report.md
JSON Report:     outputs/report.json
Execution Log:   outputs/report_execution.log
```

---

## 2. Tool Execution Summary Table

| Tool | Status | Duration (s) | Notes / Recovery Action |
| :--- | :--- | :--- | :--- |
| **GitHub URL Parser** | `success` | 0.00 | Validated owner='we45', repo='Vulnerable-Flask-App' |
| **GitHub Tree & Metadata API** | `success` | 0.95 | Found 18 files; primary language: Python |
| **GitHub File Downloader** | `success` | 1.88 | Downloaded 4 source files |
| **Deterministic File Analyzer** | `success` | 0.02 | Analyzed 4 files, 647 lines. Found 7 broad catches. |
| **ruff** | `unavailable` | 0.01 | Binary 'ruff' is not installed or not in PATH. Skipped ruff linting; continuing audit with heuristic analysis. |
| **bandit** | `unavailable` | 0.01 | Binary 'bandit' is not installed or not in PATH. Skipped bandit security scan; falling back to pattern-based secret scan. |
| **LLM (gemini/gemini-3.5-flash-lite)** | `success` | 3.12 | Generated executive summary and 3 critical security findings. |
| **Finding Validator & Merger** | `success` | 0.00 | Compiled 10 total findings (7 deterministic + 3 AI verified). |

---

## 3. Executive Summary

> *The repository 'Vulnerable-Flask-App' exhibits multiple severe security anti-patterns and cryptographic vulnerabilities, notably hardcoded secret keys, insecure JWT decoding configurations, and broad exception handling.*

---

## 4. Critical & High Security Vulnerabilities Detected

### 1. 🚨 [CRITICAL] Hardcoded Secret Keys in Flask Configuration
- **Location:** `app/app.py` (Lines 29–32)
- **Confidence:** **98%**
- **Evidence:**
  ```python
  app.config['SECRET_KEY_HMAC'] = 'secret'
  app.config['SECRET_KEY_HMAC_2'] = 'am0r3C0mpl3xK3y'
  app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
  ```
- **Impact:** Hardcoding cryptographic keys and session secrets directly in source code allows anyone with repository access to forge session cookies, hijack user sessions, and compromise application-level security.
- **Recommendation:** Load secret keys dynamically from secure environment variables or a secret management service (e.g. `os.environ.get('SECRET_KEY')`).

---

### 2. 🚨 [CRITICAL] Insecure JWT Decoding without Signature Verification
- **Location:** `app/app.py` (Lines 84–88)
- **Confidence:** **95%**
- **Evidence:**
  ```python
  def insecure_verify(token):
      decoded = jwt.decode(token, verify = False)
      print(decoded)
      return True
  ```
- **Impact:** Decoding JSON Web Tokens with `verify=False` disables cryptographic signature validation, allowing attackers to forge arbitrary claims, tamper with payloads, and impersonate administrators.
- **Recommendation:** Always enforce signature verification when decoding JWTs by specifying the correct secret key and expected algorithms (`jwt.decode(token, key, algorithms=['HS256'])`).

---

### 3. 🟡 [MEDIUM] Broad Exception Handling
- **Location:** `app/app.py` (Lines 72–82)
- **Confidence:** **85%**
- **Evidence:**
  ```python
      except DecodeError:
          print("Error in decoding token")
          return False
      except MissingRequiredClaimError as e:
          print('Claim required is missing: {0}'.format(e))
          return False
  ```
- **Impact:** Generic error handling without proper logging or handling can obscure critical runtime failures or lead to insecure fallback states.
- **Recommendation:** Log security exceptions securely and avoid silent failures or returning broad boolean flags that mask security exceptions.
