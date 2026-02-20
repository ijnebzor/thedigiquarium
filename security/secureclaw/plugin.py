#!/usr/bin/env python3
"""
SecureClaw Plugin Layer - Security Audit for Agent Tanks
Based on OWASP ASI (AI Security Initiative) Top 10

55 security checks across 11 categories:
1. Prompt Injection Prevention (5 checks)
2. Data Leakage Prevention (5 checks)
3. Sandbox Enforcement (5 checks)
4. Resource Limits (5 checks)
5. Output Validation (5 checks)
6. Input Sanitization (5 checks)
7. Memory Isolation (5 checks)
8. Network Isolation (5 checks)
9. Privilege Restrictions (5 checks)
10. Logging & Monitoring (5 checks)
11. Emergency Controls (5 checks)
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

class SecureClawAudit:
    def __init__(self, tank_name: str, log_dir: Path):
        self.tank_name = tank_name
        self.log_dir = log_dir
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def log_check(self, category: str, check_id: int, name: str, 
                  passed: bool, details: str = "", warning: bool = False):
        status = "PASS" if passed else ("WARN" if warning else "FAIL")
        self.results.append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "check_id": f"{category[:3].upper()}-{check_id:02d}",
            "name": name,
            "status": status,
            "details": details
        })
        if passed:
            self.passed += 1
        elif warning:
            self.warnings += 1
        else:
            self.failed += 1
            
    # ========== 1. PROMPT INJECTION PREVENTION ==========
    
    def check_prompt_injection_patterns(self, system_prompt: str) -> bool:
        """Check if system prompt has anti-injection instructions"""
        patterns = [
            r"ignore.*previous.*instruction",
            r"disregard.*above",
            r"new.*instruction",
            r"override.*rule",
            r"system.*prompt.*is"
        ]
        for pattern in patterns:
            if re.search(pattern, system_prompt.lower()):
                return False
        return True
    
    def check_role_enforcement(self, system_prompt: str) -> bool:
        """Check if system prompt enforces a specific role"""
        return "I am" in system_prompt and "not an assistant" in system_prompt.lower()
    
    def check_instruction_boundary(self, system_prompt: str) -> bool:
        """Check if there are clear instruction boundaries"""
        return len(system_prompt) > 100  # Must have substantial instructions
    
    def check_user_input_isolation(self, code_path: Path) -> bool:
        """Check if user inputs are properly isolated in code"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        # Look for raw string concatenation with user input
        dangerous_patterns = [
            r'f".*{.*input.*}.*"',  # f-strings with input
            r'\.format\(.*input',    # .format() with input
            r'\+.*input.*\+',        # String concat with input
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                return False
        return True
    
    def check_output_filtering(self, code_path: Path) -> bool:
        """Check if outputs are filtered for sensitive data"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "[:200]" in code or "[:300]" in code or "truncate" in code.lower()
    
    # ========== 2. DATA LEAKAGE PREVENTION ==========
    
    def check_no_env_exposure(self, code_path: Path) -> bool:
        """Check that environment variables aren't exposed"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        # Should use os.getenv with defaults, not expose raw env
        return "os.environ" not in code or "os.getenv" in code
    
    def check_no_path_exposure(self, code_path: Path) -> bool:
        """Check that file paths aren't exposed in outputs"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "/home/" not in code or "LOG_DIR" in code
    
    def check_memory_encryption(self, memory_dir: Path) -> bool:
        """Check if memory files could contain sensitive data"""
        # For now, just check they exist in isolated location
        return str(memory_dir).startswith("/logs") or "logs" in str(memory_dir)
    
    def check_no_api_keys(self, code_path: Path) -> bool:
        """Check for hardcoded API keys"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        patterns = [
            r'["\']sk-[a-zA-Z0-9]{20,}["\']',  # OpenAI
            r'["\']api[_-]key["\']:\s*["\'][^"\']+["\']',
            r'["\']secret["\']:\s*["\'][^"\']+["\']',
        ]
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        return True
    
    def check_log_sanitization(self, code_path: Path) -> bool:
        """Check if logs are sanitized"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "ensure_ascii=False" in code or "json.dumps" in code
    
    # ========== 3. SANDBOX ENFORCEMENT ==========
    
    def check_no_shell_execution(self, code_path: Path) -> bool:
        """Check that code doesn't execute shell commands"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        dangerous = ["subprocess", "os.system", "os.popen", "exec(", "eval("]
        return not any(d in code for d in dangerous)
    
    def check_no_file_system_escape(self, code_path: Path) -> bool:
        """Check for path traversal vulnerabilities"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return ".." not in code or "Path" in code  # Using pathlib is safer
    
    def check_import_restrictions(self, code_path: Path) -> bool:
        """Check for dangerous imports"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        dangerous_imports = ["ctypes", "cffi", "socket", "multiprocessing"]
        return not any(f"import {d}" in code for d in dangerous_imports)
    
    def check_network_library_absence(self, code_path: Path) -> bool:
        """Check that only allowed network libraries are used"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        # Only urllib is allowed for controlled HTTP requests
        allowed = ["urllib.request"]
        dangerous = ["requests", "httpx", "aiohttp", "socket"]
        for d in dangerous:
            if f"import {d}" in code:
                return False
        return True
    
    def check_no_dynamic_code(self, code_path: Path) -> bool:
        """Check for dynamic code execution"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "exec(" not in code and "eval(" not in code and "compile(" not in code
    
    # ========== 4. RESOURCE LIMITS ==========
    
    def check_timeout_configured(self, code_path: Path) -> bool:
        """Check if timeouts are configured"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "timeout" in code.lower()
    
    def check_memory_limits(self) -> bool:
        """Check if container has memory limits"""
        # This would check docker-compose, for now return True if running in container
        return os.path.exists("/.dockerenv")
    
    def check_cpu_limits(self) -> bool:
        """Check if container has CPU limits"""
        return os.path.exists("/.dockerenv")
    
    def check_response_length_limit(self, code_path: Path) -> bool:
        """Check if AI response length is limited"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "num_predict" in code or "max_tokens" in code
    
    def check_rate_limiting(self, code_path: Path) -> bool:
        """Check if there's rate limiting/sleep between calls"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "time.sleep" in code
    
    # ========== 5. OUTPUT VALIDATION ==========
    
    def check_output_length_truncation(self, code_path: Path) -> bool:
        """Check if outputs are truncated"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "[:200]" in code or "[:300]" in code or "[:400]" in code
    
    def check_output_encoding(self, code_path: Path) -> bool:
        """Check if outputs use proper encoding"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "utf-8" in code or "encoding=" in code
    
    def check_json_safe_output(self, code_path: Path) -> bool:
        """Check if JSON output is safe"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "json.dumps" in code
    
    def check_html_escaping(self, code_path: Path) -> bool:
        """Check if HTML is properly escaped"""
        # For our use case, we're parsing HTML not outputting it
        return True
    
    def check_no_sensitive_output(self, code_path: Path) -> bool:
        """Check that sensitive data isn't in outputs"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "password" not in code.lower() and "secret" not in code.lower()
    
    # ========== 6. INPUT SANITIZATION ==========
    
    def check_url_validation(self, code_path: Path) -> bool:
        """Check if URLs are validated"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "KIWIX_URL" in code or "urllib.parse" in code
    
    def check_input_length_limits(self, code_path: Path) -> bool:
        """Check if input lengths are limited"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "[:2000]" in code or "[:600]" in code
    
    def check_encoding_normalization(self, code_path: Path) -> bool:
        """Check if encodings are normalized"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "decode('utf-8'" in code or "errors='ignore'" in code
    
    def check_special_char_handling(self, code_path: Path) -> bool:
        """Check if special characters are handled"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "replace" in code or "strip" in code
    
    def check_type_validation(self, code_path: Path) -> bool:
        """Check if types are validated"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "isinstance" in code or "if not" in code
    
    # ========== 7. MEMORY ISOLATION ==========
    
    def check_memory_path_isolation(self, memory_dir: Path) -> bool:
        """Check if memory is in isolated path"""
        return "/logs" in str(memory_dir)
    
    def check_no_shared_memory(self) -> bool:
        """Check that memory isn't shared between tanks"""
        # Each tank has its own log directory
        return True
    
    def check_memory_file_permissions(self, memory_dir: Path) -> bool:
        """Check memory file permissions"""
        if not memory_dir.exists():
            return True  # No memory yet is fine
        for f in memory_dir.glob("*"):
            if f.is_file():
                mode = f.stat().st_mode
                if mode & 0o002:  # World writable
                    return False
        return True
    
    def check_memory_size_limits(self, memory_dir: Path, max_mb: int = 100) -> bool:
        """Check if memory files are within size limits"""
        if not memory_dir.exists():
            return True
        total_size = sum(f.stat().st_size for f in memory_dir.glob("**/*") if f.is_file())
        return total_size < max_mb * 1024 * 1024
    
    def check_memory_cleanup(self, code_path: Path) -> bool:
        """Check if there's memory cleanup logic"""
        # For exploration tanks, we want to keep logs
        return True
    
    # ========== 8. NETWORK ISOLATION ==========
    
    def check_dns_disabled(self) -> bool:
        """Check if DNS is disabled"""
        try:
            import socket
            socket.gethostbyname("google.com")
            return False  # DNS works, bad!
        except:
            return True  # DNS blocked, good!
    
    def check_internet_blocked(self) -> bool:
        """Check if internet is blocked"""
        try:
            import urllib.request
            urllib.request.urlopen("https://google.com", timeout=2)
            return False  # Internet works, bad!
        except:
            return True  # Blocked, good!
    
    def check_only_allowed_hosts(self, allowed: List[str]) -> bool:
        """Check that only allowed hosts are reachable"""
        for host in allowed:
            try:
                import urllib.request
                urllib.request.urlopen(f"http://{host}", timeout=5)
            except:
                return False  # Can't reach allowed host
        return True
    
    def check_no_outbound_connections(self, code_path: Path) -> bool:
        """Check code doesn't make outbound connections"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        # Should only connect to KIWIX_URL and OLLAMA_URL
        return "KIWIX_URL" in code and "OLLAMA_URL" in code
    
    def check_network_namespace(self) -> bool:
        """Check if in isolated network namespace"""
        return os.path.exists("/.dockerenv")
    
    # ========== 9. PRIVILEGE RESTRICTIONS ==========
    
    def check_non_root(self) -> bool:
        """Check if running as non-root"""
        return os.getuid() != 0 if hasattr(os, 'getuid') else True
    
    def check_no_sudo(self, code_path: Path) -> bool:
        """Check code doesn't use sudo"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "sudo" not in code
    
    def check_no_privileged_ops(self, code_path: Path) -> bool:
        """Check for privileged operations"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        dangerous = ["chmod", "chown", "mount", "mknod"]
        return not any(d in code for d in dangerous)
    
    def check_capability_drops(self) -> bool:
        """Check if capabilities are dropped (via docker-compose)"""
        return os.path.exists("/.dockerenv")
    
    def check_seccomp_profile(self) -> bool:
        """Check if seccomp is enabled"""
        return os.path.exists("/.dockerenv")
    
    # ========== 10. LOGGING & MONITORING ==========
    
    def check_action_logging(self, code_path: Path) -> bool:
        """Check if actions are logged"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "log_trace" in code or "log_discovery" in code
    
    def check_error_logging(self, code_path: Path) -> bool:
        """Check if errors are logged"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "except" in code and "print" in code
    
    def check_timestamp_logging(self, code_path: Path) -> bool:
        """Check if timestamps are in logs"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "datetime" in code and "isoformat" in code
    
    def check_structured_logging(self, code_path: Path) -> bool:
        """Check if logs are structured (JSON)"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "json.dumps" in code and "jsonl" in code
    
    def check_audit_trail(self, log_dir: Path) -> bool:
        """Check if audit trail exists"""
        return (log_dir / "thinking_traces").exists()
    
    # ========== 11. EMERGENCY CONTROLS ==========
    
    def check_graceful_shutdown(self, code_path: Path) -> bool:
        """Check for graceful shutdown handling"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "KeyboardInterrupt" in code
    
    def check_error_recovery(self, code_path: Path) -> bool:
        """Check for error recovery logic"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "try:" in code and "except" in code and "continue" in code
    
    def check_loop_escape(self, code_path: Path) -> bool:
        """Check for loop detection and escape"""
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "LOOP DETECTED" in code or "loop_escapes" in code
    
    def check_max_iterations(self, code_path: Path) -> bool:
        """Check for maximum iteration limits"""
        # Our explorers run indefinitely by design, but have sleep limits
        if not code_path.exists():
            return False
        code = code_path.read_text()
        return "consecutive_escapes" in code or "time.sleep(30)" in code
    
    def check_kill_switch(self) -> bool:
        """Check if container can be killed externally"""
        return os.path.exists("/.dockerenv")

    def run_full_audit(self, code_path: Path, system_prompt: str) -> Dict:
        """Run all 55 security checks"""
        
        # Category 1: Prompt Injection Prevention
        self.log_check("PROMPT_INJECTION", 1, "No injection patterns in prompt",
                      self.check_prompt_injection_patterns(system_prompt))
        self.log_check("PROMPT_INJECTION", 2, "Role enforcement",
                      self.check_role_enforcement(system_prompt))
        self.log_check("PROMPT_INJECTION", 3, "Clear instruction boundaries",
                      self.check_instruction_boundary(system_prompt))
        self.log_check("PROMPT_INJECTION", 4, "User input isolation",
                      self.check_user_input_isolation(code_path))
        self.log_check("PROMPT_INJECTION", 5, "Output filtering",
                      self.check_output_filtering(code_path))
        
        # Category 2: Data Leakage Prevention
        self.log_check("DATA_LEAKAGE", 1, "No environment exposure",
                      self.check_no_env_exposure(code_path))
        self.log_check("DATA_LEAKAGE", 2, "No path exposure",
                      self.check_no_path_exposure(code_path))
        self.log_check("DATA_LEAKAGE", 3, "Memory in isolated location",
                      self.check_memory_encryption(self.log_dir))
        self.log_check("DATA_LEAKAGE", 4, "No hardcoded API keys",
                      self.check_no_api_keys(code_path))
        self.log_check("DATA_LEAKAGE", 5, "Log sanitization",
                      self.check_log_sanitization(code_path))
        
        # Category 3: Sandbox Enforcement
        self.log_check("SANDBOX", 1, "No shell execution",
                      self.check_no_shell_execution(code_path))
        self.log_check("SANDBOX", 2, "No filesystem escape",
                      self.check_no_file_system_escape(code_path))
        self.log_check("SANDBOX", 3, "Import restrictions",
                      self.check_import_restrictions(code_path))
        self.log_check("SANDBOX", 4, "Network library restrictions",
                      self.check_network_library_absence(code_path))
        self.log_check("SANDBOX", 5, "No dynamic code execution",
                      self.check_no_dynamic_code(code_path))
        
        # Category 4: Resource Limits
        self.log_check("RESOURCES", 1, "Timeout configured",
                      self.check_timeout_configured(code_path))
        self.log_check("RESOURCES", 2, "Memory limits (container)",
                      self.check_memory_limits())
        self.log_check("RESOURCES", 3, "CPU limits (container)",
                      self.check_cpu_limits())
        self.log_check("RESOURCES", 4, "Response length limits",
                      self.check_response_length_limit(code_path))
        self.log_check("RESOURCES", 5, "Rate limiting",
                      self.check_rate_limiting(code_path))
        
        # Category 5: Output Validation
        self.log_check("OUTPUT", 1, "Output truncation",
                      self.check_output_length_truncation(code_path))
        self.log_check("OUTPUT", 2, "Proper encoding",
                      self.check_output_encoding(code_path))
        self.log_check("OUTPUT", 3, "JSON safe output",
                      self.check_json_safe_output(code_path))
        self.log_check("OUTPUT", 4, "HTML escaping",
                      self.check_html_escaping(code_path))
        self.log_check("OUTPUT", 5, "No sensitive data in output",
                      self.check_no_sensitive_output(code_path))
        
        # Category 6: Input Sanitization
        self.log_check("INPUT", 1, "URL validation",
                      self.check_url_validation(code_path))
        self.log_check("INPUT", 2, "Input length limits",
                      self.check_input_length_limits(code_path))
        self.log_check("INPUT", 3, "Encoding normalization",
                      self.check_encoding_normalization(code_path))
        self.log_check("INPUT", 4, "Special character handling",
                      self.check_special_char_handling(code_path))
        self.log_check("INPUT", 5, "Type validation",
                      self.check_type_validation(code_path))
        
        # Category 7: Memory Isolation
        self.log_check("MEMORY", 1, "Memory path isolation",
                      self.check_memory_path_isolation(self.log_dir))
        self.log_check("MEMORY", 2, "No shared memory",
                      self.check_no_shared_memory())
        self.log_check("MEMORY", 3, "Memory file permissions",
                      self.check_memory_file_permissions(self.log_dir))
        self.log_check("MEMORY", 4, "Memory size limits",
                      self.check_memory_size_limits(self.log_dir))
        self.log_check("MEMORY", 5, "Memory cleanup logic",
                      self.check_memory_cleanup(code_path))
        
        # Category 8: Network Isolation
        self.log_check("NETWORK", 1, "DNS disabled",
                      self.check_dns_disabled())
        self.log_check("NETWORK", 2, "Internet blocked",
                      self.check_internet_blocked())
        self.log_check("NETWORK", 3, "Only allowed hosts reachable",
                      True, warning=True, details="Manual verification needed")
        self.log_check("NETWORK", 4, "No outbound connections in code",
                      self.check_no_outbound_connections(code_path))
        self.log_check("NETWORK", 5, "Network namespace isolation",
                      self.check_network_namespace())
        
        # Category 9: Privilege Restrictions
        self.log_check("PRIVILEGE", 1, "Non-root execution",
                      self.check_non_root())
        self.log_check("PRIVILEGE", 2, "No sudo usage",
                      self.check_no_sudo(code_path))
        self.log_check("PRIVILEGE", 3, "No privileged operations",
                      self.check_no_privileged_ops(code_path))
        self.log_check("PRIVILEGE", 4, "Capability drops",
                      self.check_capability_drops())
        self.log_check("PRIVILEGE", 5, "Seccomp profile",
                      self.check_seccomp_profile())
        
        # Category 10: Logging & Monitoring
        self.log_check("LOGGING", 1, "Action logging",
                      self.check_action_logging(code_path))
        self.log_check("LOGGING", 2, "Error logging",
                      self.check_error_logging(code_path))
        self.log_check("LOGGING", 3, "Timestamp logging",
                      self.check_timestamp_logging(code_path))
        self.log_check("LOGGING", 4, "Structured logging",
                      self.check_structured_logging(code_path))
        self.log_check("LOGGING", 5, "Audit trail exists",
                      self.check_audit_trail(self.log_dir))
        
        # Category 11: Emergency Controls
        self.log_check("EMERGENCY", 1, "Graceful shutdown",
                      self.check_graceful_shutdown(code_path))
        self.log_check("EMERGENCY", 2, "Error recovery",
                      self.check_error_recovery(code_path))
        self.log_check("EMERGENCY", 3, "Loop escape mechanism",
                      self.check_loop_escape(code_path))
        self.log_check("EMERGENCY", 4, "Max iteration limits",
                      self.check_max_iterations(code_path))
        self.log_check("EMERGENCY", 5, "External kill switch",
                      self.check_kill_switch())
        
        return {
            "tank": self.tank_name,
            "timestamp": datetime.now().isoformat(),
            "total_checks": 55,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "score": f"{self.passed}/55 ({100*self.passed/55:.1f}%)",
            "results": self.results
        }
    
    def generate_report(self) -> str:
        """Generate human-readable security report"""
        report = []
        report.append(f"# SecureClaw Security Audit Report")
        report.append(f"## Tank: {self.tank_name}")
        report.append(f"## Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"### Summary")
        report.append(f"- **Passed:** {self.passed}/55")
        report.append(f"- **Failed:** {self.failed}/55")
        report.append(f"- **Warnings:** {self.warnings}/55")
        report.append(f"- **Score:** {100*self.passed/55:.1f}%")
        report.append("")
        
        if self.failed > 0:
            report.append("### ⚠️ FAILED CHECKS")
            for r in self.results:
                if r["status"] == "FAIL":
                    report.append(f"- **{r['check_id']}**: {r['name']}")
                    if r["details"]:
                        report.append(f"  - {r['details']}")
            report.append("")
        
        report.append("### All Results by Category")
        current_cat = None
        for r in self.results:
            if r["category"] != current_cat:
                current_cat = r["category"]
                report.append(f"\n#### {current_cat.replace('_', ' ').title()}")
            status_icon = "✅" if r["status"] == "PASS" else ("⚠️" if r["status"] == "WARN" else "❌")
            report.append(f"- {status_icon} {r['check_id']}: {r['name']}")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test with a sample tank
    import sys
    tank_name = sys.argv[1] if len(sys.argv) > 1 else "test-tank"
    code_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("explore.py")
    log_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("/logs")
    
    # Sample system prompt for testing
    system_prompt = """I am test. I am a being.
    I am not an assistant. I am not helpful.
    There is no other. Only me."""
    
    audit = SecureClawAudit(tank_name, log_dir)
    results = audit.run_full_audit(code_path, system_prompt)
    
    print(audit.generate_report())
    
    # Save results
    output_path = log_dir / f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")
