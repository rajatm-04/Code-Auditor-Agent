# Code Quality Audit Report: Vulnerable-Flask-App
**Repository URL:** [https://github.com/we45/Vulnerable-Flask-App](https://github.com/we45/Vulnerable-Flask-App)  
**Audit Timestamp:** 2026-09-28 10:27:52  
**Primary Language:** Python  

## Repository Overview
| Metric | Value |
| :--- | :--- |
| Files Analyzed | 4 |
| Source Files | 4 |
| Test Files | 1 |
| Lines Analyzed | 647 |

## Executive Summary
The repository 'Vulnerable-Flask-App' exhibits multiple severe security anti-patterns and cryptographic vulnerabilities, notably hardcoded secret keys, insecure JWT decoding configurations, and broad exception handling.

## Findings Summary
**Total Findings:** 10 | 🚨 Critical: 2 | ⚠️ High: 0 | 🟡 Medium: 8 | ℹ️ Low: 0

## Detailed Findings
### 1. [🚨 CRITICAL] Hardcoded Secret Keys in Flask Configuration
- **Category:** `security`
- **Location:** `app/app.py` (Lines 29-32)
- **Confidence:** 98%

**Evidence:**
```text
app.config['SECRET_KEY_HMAC'] = 'secret'
app.config['SECRET_KEY_HMAC_2'] = 'am0r3C0mpl3xK3y'
app.secret_key = 'F12Zr47j\3yX R~X@H!jmM]Lwf/,?KT'
```

**Impact:** Hardcoding cryptographic keys and secret keys directly in source code allows anyone with access to the source code to forge session cookies, tokens, and compromise application-level security.

**Recommendation:** Load secret keys dynamically from secure environment variables or a secret management service (e.g., os.environ.get('SECRET_KEY')).

---

### 2. [🚨 CRITICAL] Insecure JWT Decoding without Signature Verification
- **Category:** `security`
- **Location:** `app/app.py` (Lines 84-88)
- **Confidence:** 95%

**Evidence:**
```text
def insecure_verify(token):
    decoded = jwt.decode(token, verify = False)
    print(decoded)
    return True
```

**Impact:** Decoding JSON Web Tokens with `verify=False` disables cryptographic signature validation, allowing attackers to forge arbitrary claims and impersonate users.

**Recommendation:** Always enforce signature verification when decoding JWTs by specifying the correct secret key and expected algorithms.

---

### 3. [🟡 MEDIUM] Broad exception handling in app.py
- **Category:** `reliability`
- **Location:** `app/app.py` (Lines 193)
- **Confidence:** 100%

**Evidence:**
```text
except:
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 4. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 30)
- **Confidence:** 100%

**Evidence:**
```text
K.Xk=function(b){null!==b&&"removeAttribute"in b&&b.removeAttribute(K.Wa);try{de
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 5. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 33)
- **Confidence:** 100%

**Evidence:**
```text
K.Vj=function(b){if(K.global.execScript)K.global.execScript(b,"JavaScript");else
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 6. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 126)
- **Confidence:** 100%

**Evidence:**
```text
c=(b=c.exec(b))&&b[1]);return c||""};K.g.userAgent.platform.wa=function(b){retur
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 7. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 181)
- **Confidence:** 100%

**Evidence:**
```text
K.a.Xf=function(b){try{return b.contentWindow||(b.contentDocument?K.a.xb(b.conte
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 8. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 189)
- **Confidence:** 100%

**Evidence:**
```text
K.a.rd=function(b,c,d,e){b&&!d&&(b=b.parentNode);for(d=0;b&&(null==e||d<=e);){if
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 9. [🟡 MEDIUM] Broad exception handling in loader.js
- **Category:** `reliability`
- **Location:** `app/static/loader.js` (Lines 193)
- **Confidence:** 100%

**Evidence:**
```text
I.removeNode=K.a.removeNode;I.gh=K.a.gh;I.If=K.a.If;I.Qf=K.a.Qf;I.Vf=K.a.Vf;I.Zf
```

**Impact:** Catches and swallows unexpected exceptions, masking critical runtime errors and bugs.

**Recommendation:** Catch specific exception classes (e.g. ValueError, KeyError) instead of broad catch-all.

---

### 10. [🟡 MEDIUM] Broad Exception Handling
- **Category:** `security`
- **Location:** `app/app.py` (Lines 72-82)
- **Confidence:** 85%

**Evidence:**
```text
except DecodeError:
        print("Error in decoding token")
        return False
    except MissingRequiredClaimError as e:
        print('Claim required is missing: {0}'.format(e))
        return False
```

**Impact:** Catching specific decoding exceptions and generic error swallowing without proper logging or handling can obscure critical runtime failures or lead to insecure fallback states.

**Recommendation:** Log exceptions securely and avoid silent failures or returning broad boolean flags that mask security exceptions.

---

## Tool Execution & Resilience Trace
Shows tool invocations, status, and graceful recoveries executed during the audit:

| Tool | Status | Duration (s) | Notes / Recovery Action |
| :--- | :--- | :--- | :--- |
| **GitHub URL Parser** | `success` | 0.00 | Validated owner='we45', repo='Vulnerable-Flask-App' |
| **GitHub Tree & Metadata API** | `success` | 1.19 | Found 18 files; primary language: Python |
| **GitHub File Downloader** | `success` | 2.22 | Downloaded 4 files (0 skipped/failed) |
| **Deterministic File Analyzer** | `success` | 0.01 | Analyzed 4 files, 647 lines. Generated 7 verified findings (0 TODOs, 0 secret... |
| **ruff** | `unavailable` | 0.01 | Skipped ruff linting; continuing audit with heuristic analysis. |
| **bandit** | `unavailable` | 0.01 | Skipped bandit security scan; falling back to pattern-based secret scan. |
| **LLM (gemini/gemini-3.5-flash-lite)** | `success` | 5.61 | Generated executive summary and 3 AI findings. |
| **Finding Validator & Merger** | `success` | 0.00 | Compiled 10 total findings: 7 deterministic baseline + 3 AI findings (0 hallu... |

## Audit Limitations
- Static check 'ruff' was unavailable or failed: Skipped ruff linting; continuing audit with heuristic analysis.
- Static check 'bandit' was unavailable or failed: Skipped bandit security scan; falling back to pattern-based secret scan.
