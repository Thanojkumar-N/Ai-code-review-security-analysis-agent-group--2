import re
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any
from backend.app.agents.state import AgentState

# ==========================================
# Abstract Base and Registry for expansion
# ==========================================

class BaseLanguageScanner(ABC):
    """Abstract base class that all language scanners must implement."""
    @abstractmethod
    def scan_code(self, code: str) -> List[Dict[str, Any]]:
        """Scan source code text and return a list of structured vulnerability dictionaries."""
        pass


class ScannerRegistry:
    """Registry class to manage and instantiate language-specific security scanners."""
    _registry: Dict[str, Type[BaseLanguageScanner]] = {}

    @classmethod
    def register(cls, language: str, scanner_cls: Type[BaseLanguageScanner]) -> None:
        """Register a scanner class under a specific language key."""
        cls._registry[language.lower()] = scanner_cls

    @classmethod
    def get_scanner(cls, language: str) -> BaseLanguageScanner:
        """Get an instance of a registered scanner. Returns None if not supported."""
        scanner_cls = cls._registry.get(language.lower())
        if scanner_cls:
            return scanner_cls()
        return None

# ==========================================
# Python Scanner Implementation
# ==========================================

class PythonScanner(BaseLanguageScanner):
    """Static security rules engine for auditing Python scripts."""
    
    SQLI = re.compile(r"execute\(\s*(f['\"].*SELECT.*\{.*\}['\"]|['\"].*SELECT.*['\"]\s*%\s*\w+|['\"].*SELECT.*['\"]\.format\()", re.IGNORECASE)
    XSS = re.compile(r"HTMLResponse\(\s*content\s*=\s*f?['\"].*\{.*\}.*['\"]|render_template_string\(\s*f?['\"].*\{.*\}.*['\"]", re.IGNORECASE)
    CSRF_DISABLE = re.compile(r"WTF_CSRF_ENABLED\s*=\s*False|csrf_protect\s*=\s*False", re.IGNORECASE)
    AUTH_NONE = re.compile(r"algorithm\s*=\s*['\"]none['\"]|jwt\.encode\(.*algorithm\s*=\s*['\"]none['\"]", re.IGNORECASE)
    TRAVERSAL = re.compile(r"open\(\s*(f['\"].*\{.*?path.*?|.*?file_name.*?\}['\"]|['\"].*?['\"]\s*\+\s*\w+)\)", re.IGNORECASE)
    SECRETS = re.compile(r"(password|passwd|secret|api_key|apikey|token|private_key|aws_key)\s*=\s*['\"][a-zA-Z0-9_\-\+\/]{8,}['\"]", re.IGNORECASE)
    CMD = re.compile(r"os\.(system|popen)\(|subprocess\.(Popen|run|call)\(.*shell\s*=\s*True", re.IGNORECASE)
    CRYPTO = re.compile(r"hashlib\.(md5|sha1)\(|Cipher\.getInstance\(['\"]DES['\"]\)|DES\.new\(", re.IGNORECASE)
    DESERIAL = re.compile(r"pickle\.loads\(|yaml\.unsafe_load\(|shelve\.open\(", re.IGNORECASE)
    SSRF = re.compile(r"requests\.(get|post|put|delete)\(\s*(url|target_url|user_url|\w+)\)", re.IGNORECASE)

    def scan_code(self, code: str) -> List[Dict[str, Any]]:
        vulnerabilities = []
        lines = code.split("\n")
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()
            
            if stripped.startswith("#") or not stripped:
                continue

            # Hardcoded Secrets check
            if self.SECRETS.search(stripped) and not "mock" in stripped.lower() and not "test" in stripped.lower():
                vulnerabilities.append({
                    "id": "SEC-001",
                    "line": line_num,
                    "title": "Hardcoded Cryptographic Secrets or Token Keys",
                    "severity": "High",
                    "classification": "OWASP A02:2021-Cryptographic Failures",
                    "cwe": "CWE-798",
                    "confidence": "High",
                    "description": "Plaintext secret token keys or credentials variables are declared directly in source code.",
                    "recommendation": "Extract credentials secrets to environment configuration files (e.g. .env) that are git-ignored.",
                    "snippet": stripped
                })

            # SQL Injection check
            if self.SQLI.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-002",
                    "line": line_num,
                    "title": "SQL Injection via Query Formatter Concatenation",
                    "severity": "Critical",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-89",
                    "confidence": "High",
                    "description": "Constructing SQL statements dynamically using formatting (f-strings or .format) executes parameters as database command blocks.",
                    "recommendation": "Use SQLAlchemy parameterized query parameters bindings.",
                    "snippet": stripped
                })

            # XSS check
            if self.XSS.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-003",
                    "line": line_num,
                    "title": "Cross-Site Scripting (XSS) via Unescaped HTML responses",
                    "severity": "High",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-79",
                    "confidence": "High",
                    "description": "Returning raw, unescaped HTML content parameter strings allows client browsers to execute malicious javascript code.",
                    "recommendation": "Sanitize output strings using HTML template layouts or escape packages.",
                    "snippet": stripped
                })

            # CSRF disabled check
            if self.CSRF_DISABLE.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-004",
                    "line": line_num,
                    "title": "CSRF Safety Controls Disabled",
                    "severity": "High",
                    "classification": "OWASP A05:2021-Security Misconfiguration",
                    "cwe": "CWE-352",
                    "confidence": "High",
                    "description": "WTF_CSRF_ENABLED has been set to False or CSRF validation checks are explicitly skipped, opening user state change leaks.",
                    "recommendation": "Enable CSRF protection globally in configuration settings for all POST/PUT requests.",
                    "snippet": stripped
                })

            # Broken Auth check
            if self.AUTH_NONE.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-005",
                    "line": line_num,
                    "title": "Broken Authentication via JWT 'none' Algorithm",
                    "severity": "Critical",
                    "classification": "OWASP A07:2021-Identification and Authentication Failures",
                    "cwe": "CWE-287",
                    "confidence": "High",
                    "description": "JWT tokens are created with the alg claim set to none. This allows clients to forge signatures and bypass auth.",
                    "recommendation": "Enforce strong signing algorithms (e.g. HS256, RS256) and reject none algorithms explicitly during decodes.",
                    "snippet": stripped
                })

            # Path Traversal check
            if self.TRAVERSAL.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-006",
                    "line": line_num,
                    "title": "Path Traversal File Read Vulnerability",
                    "severity": "High",
                    "classification": "OWASP A01:2021-Broken Access Control",
                    "cwe": "CWE-22",
                    "confidence": "Medium",
                    "description": "Using dynamic strings directly in open() functions allows attackers to read files outside restricted directories using double dots (../).",
                    "recommendation": "Sanitize filenames using `os.path.basename()` or verify paths reside within an authorized root directory.",
                    "snippet": stripped
                })

            # Command Injection check
            if self.CMD.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-007",
                    "line": line_num,
                    "title": "OS Command Shell Injection",
                    "severity": "Critical",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-78",
                    "confidence": "High",
                    "description": "Invoking system shells (shell=True) via os.system or subprocess runs unvalidated strings as direct terminal inputs.",
                    "recommendation": "Set shell=False and pass arguments as lists: `subprocess.run(['command', 'arg1'])`.",
                    "snippet": stripped
                })

            # Weak Crypto check
            if self.CRYPTO.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-008",
                    "line": line_num,
                    "title": "Weak Cryptographic Hashing Algorithm",
                    "severity": "Medium",
                    "classification": "OWASP A02:2021-Cryptographic Failures",
                    "cwe": "CWE-327",
                    "confidence": "High",
                    "description": "MD5 or SHA-1 hashes are weak, prone to collision exploits, and insecure for password hashing.",
                    "recommendation": "Upgrade to secure hashing structures (e.g., bcrypt, Argon2, or SHA-256).",
                    "snippet": stripped
                })

            # Insecure Deserialization check
            if self.DESERIAL.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-009",
                    "line": line_num,
                    "title": "Insecure Deserialization via pickle/yaml loading",
                    "severity": "Critical",
                    "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                    "cwe": "CWE-502",
                    "confidence": "High",
                    "description": "Using pickle.loads or yaml.unsafe_load on untrusted inputs allows arbitrary code execution during object load.",
                    "recommendation": "Use safe JSON serialization or safe YAML parsers (`yaml.safe_load`).",
                    "snippet": stripped
                })

            # SSRF check
            if self.SSRF.search(stripped) and not "http" in stripped.lower():
                vulnerabilities.append({
                    "id": "SEC-010",
                    "line": line_num,
                    "title": "Server-Side Request Forgery (SSRF)",
                    "severity": "High",
                    "classification": "OWASP A10:2021-Server-Side Request Forgery",
                    "cwe": "CWE-918",
                    "confidence": "Medium",
                    "description": "Sending HTTP requests using dynamic input parameters allows attackers to trigger internal request scans.",
                    "recommendation": "Use a whitelist of allowed domains and block requests directed to local loops (localhost/127.0.0.1).",
                    "snippet": stripped
                })

        return vulnerabilities


# ==========================================
# Java Scanner Implementation
# ==========================================

class JavaScanner(BaseLanguageScanner):
    """Static security rules engine for auditing Java source files."""
    
    SQLI = re.compile(r"\"SELECT\s+.*\s+WHERE\s+.*\s*=\s*'\s*\"\s*\+\s*\w+|executeQuery\(\s*.*?\s*\+\s*.*?\)", re.IGNORECASE)
    XSS = re.compile(r"response\.getWriter\(\)\.write\(\s*\w+\)|out\.(print|println)\(\s*request\.getParameter", re.IGNORECASE)
    CSRF_DISABLE = re.compile(r"\.csrf\(\)\.disable\(\)|csrf\s*->\s*csrf\.disable\(\)", re.IGNORECASE)
    AUTH = re.compile(r"InMemoryUserDetailsManager|NoOpPasswordEncoder", re.IGNORECASE)
    TRAVERSAL = re.compile(r"new\s+(FileInputStream|File|FileReader)\(\s*(\w+\s*\+\s*\w+|request\.getParameter)", re.IGNORECASE)
    SECRETS = re.compile(r"(password|passwd|secret|api_key|apikey|token|private_key|aws_key)\s*=\s*['\"][a-zA-Z0-9_\-\+\/]{8,}['\"]", re.IGNORECASE)
    CMD = re.compile(r"Runtime\.getRuntime\(\)\.exec\(|new\s+ProcessBuilder\(", re.IGNORECASE)
    CRYPTO = re.compile(r"MessageDigest\.getInstance\(['\"](MD5|SHA-1)['\"]\)|Cipher\.getInstance\(['\"]DES['\"]", re.IGNORECASE)
    DESERIAL = re.compile(r"ObjectInputStream\.readObject\(", re.IGNORECASE)
    SSRF = re.compile(r"new\s+URL\(\s*(url|target_url|\w+)\)\.openStream\(|new\s+URL\(\s*(url|target_url|\w+)\)\.openConnection\(", re.IGNORECASE)

    def scan_code(self, code: str) -> List[Dict[str, Any]]:
        vulnerabilities = []
        lines = code.split("\n")
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()
            
            if stripped.startswith("//") or not stripped:
                continue

            # Hardcoded Secrets check
            if self.SECRETS.search(stripped) and not "mock" in stripped.lower() and not "test" in stripped.lower():
                vulnerabilities.append({
                    "id": "SEC-001",
                    "line": line_num,
                    "title": "Hardcoded Cryptographic Secrets or Token Keys",
                    "severity": "High",
                    "classification": "OWASP A02:2021-Cryptographic Failures",
                    "cwe": "CWE-798",
                    "confidence": "High",
                    "description": "Plaintext secret token keys or credentials variables are declared directly in source code.",
                    "recommendation": "Extract credentials secrets to environment configuration files (e.g. .env) that are git-ignored.",
                    "snippet": stripped
                })

            # SQL Injection check
            if self.SQLI.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-002",
                    "line": line_num,
                    "title": "SQL Injection via Java String Concatenation",
                    "severity": "Critical",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-89",
                    "confidence": "High",
                    "description": "Concatenating variables into SQL queries bypasses syntax separation, allowing query logic modifications.",
                    "recommendation": "Replace Statement string concats with PreparedStatement parameterized query parameters.",
                    "snippet": stripped
                })

            # XSS check
            if self.XSS.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-003",
                    "line": line_num,
                    "title": "Cross-Site Scripting (XSS) in Java Servlet Output",
                    "severity": "High",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-79",
                    "confidence": "High",
                    "description": "Printing unescaped request parameters to servlet response streams allows malicious script code executions.",
                    "recommendation": "Escape inputs using HTML wrapper utils (e.g. Apache StringEscapeUtils).",
                    "snippet": stripped
                })

            # CSRF disabled check
            if self.CSRF_DISABLE.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-004",
                    "line": line_num,
                    "title": "Java Spring CSRF Security Controls Disabled",
                    "severity": "High",
                    "classification": "OWASP A05:2021-Security Misconfiguration",
                    "cwe": "CWE-352",
                    "confidence": "High",
                    "description": "Spring Security CSRF checks are explicitly disabled in config setups, facilitating state forgery bugs.",
                    "recommendation": "Enable CSRF controls and include anti-CSRF tokens in AJAX headers.",
                    "snippet": stripped
                })

            # Broken Auth check
            if self.AUTH.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-005",
                    "line": line_num,
                    "title": "Broken Authentication via Insecure Password Encoder",
                    "severity": "Critical",
                    "classification": "OWASP A07:2021-Identification and Authentication Failures",
                    "cwe": "CWE-287",
                    "confidence": "High",
                    "description": "Using NoOpPasswordEncoder or hardcoded in-memory user lists stores credentials in plaintext formats.",
                    "recommendation": "Configure BCryptPasswordEncoder or Argon2 for secure database credentials checks.",
                    "snippet": stripped
                })

            # Path Traversal check
            if self.TRAVERSAL.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-006",
                    "line": line_num,
                    "title": "Java Path Traversal File Stream Access",
                    "severity": "High",
                    "classification": "OWASP A01:2021-Broken Access Control",
                    "cwe": "CWE-22",
                    "confidence": "Medium",
                    "description": "Initializing file inputs using concatenated parameter requests allows attackers to retrieve root file paths.",
                    "recommendation": "Use path normalization and restrict access to specific base directories.",
                    "snippet": stripped
                })

            # Command Injection check
            if self.CMD.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-007",
                    "line": line_num,
                    "title": "Java OS Command Execution Injection",
                    "severity": "Critical",
                    "classification": "OWASP A03:2021-Injection",
                    "cwe": "CWE-78",
                    "confidence": "High",
                    "description": "Executing system prompts using Runtime.exec with raw strings runs parameters as terminal commands.",
                    "recommendation": "Avoid using Runtime.exec with raw strings; run commands via ProcessBuilder array blocks.",
                    "snippet": stripped
                })

            # Weak Crypto check
            if self.CRYPTO.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-008",
                    "line": line_num,
                    "title": "Weak Hashing MessageDigest Algorithm",
                    "severity": "Medium",
                    "classification": "OWASP A02:2021-Cryptographic Failures",
                    "cwe": "CWE-327",
                    "confidence": "High",
                    "description": "Java MessageDigest is configured to use insecure hash algorithms (MD5, SHA-1).",
                    "recommendation": "Upgrade cryptographic hashing classes to SHA-256 or SHA-512 instances.",
                    "snippet": stripped
                })

            # Insecure Deserialization check
            if self.DESERIAL.search(stripped):
                vulnerabilities.append({
                    "id": "SEC-009",
                    "line": line_num,
                    "title": "Java Insecure ObjectInputStream Deserialization",
                    "severity": "Critical",
                    "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                    "cwe": "CWE-502",
                    "confidence": "High",
                    "description": "Invoking readObject() on ObjectInputStream parses bytes directly, enabling arbitrary object instances instantiations.",
                    "recommendation": "Implement class-validation filters or use JSON parsing libraries.",
                    "snippet": stripped
                })

            # SSRF check
            if self.SSRF.search(stripped) and not "http" in stripped.lower():
                vulnerabilities.append({
                    "id": "SEC-010",
                    "line": line_num,
                    "title": "Java Server-Side Request Forgery (SSRF)",
                    "severity": "High",
                    "classification": "OWASP A10:2021-Server-Side Request Forgery",
                    "cwe": "CWE-918",
                    "confidence": "Medium",
                    "description": "Initiating network requests from dynamic inputs allows server-level network scans.",
                    "recommendation": "Validate requested URL patterns against strict domain whitelist configurations.",
                    "snippet": stripped
                })

        return vulnerabilities


# Register core scanners in the registry
ScannerRegistry.register("python", PythonScanner)
ScannerRegistry.register("java", JavaScanner)

# ==========================================
# Orchestrator Node Function
# ==========================================

def security_agent_node(state: AgentState) -> dict:
    """Agent node that audits source code scripts using registered language scanners."""
    code = state.get("code", "")
    language = state.get("language", "python").lower()
    
    # 1. Fetch scanner class from register
    scanner = ScannerRegistry.get_scanner(language)
    if not scanner:
        # Fallback to python if language registry is empty
        scanner = ScannerRegistry.get_scanner("python")

    # 2. Execute scanning filters
    vulnerabilities = []
    if scanner:
        vulnerabilities = scanner.scan_code(code)

    # 3. Compile severity summaries
    severities = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for vuln in vulnerabilities:
        sev = vuln["severity"]
        if sev in severities:
            severities[sev] += 1

    return {
        "security_analysis": {
            "vulnerabilities": vulnerabilities,
            "severity_summary": severities
        }
    }
