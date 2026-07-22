import re
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any, Optional
from backend.app.agents.state import AgentState

# ==========================================
# Abstract Base and Registry for expansion
# ==========================================

class BaseLanguageScanner(ABC):
    """Abstract base class that all language scanners must implement."""
    @abstractmethod
    def scan_code(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def __init__(self):
        # Define the 19 OWASP vulnerability checks with detailed metadata
        self.rules = [
            {
                "id": "SEC-001",
                "pattern": re.compile(r"(api_key|apikey|secret|secret_key|jwt_key|private_key|aws_key|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-\+\/]{8,}['\"]", re.IGNORECASE),
                "title": "Hardcoded Cryptographic Secrets or Token Keys",
                "severity": "High",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-798",
                "confidence": "High",
                "description": "Plaintext secret token keys or credentials variables are declared directly in source code.",
                "risk_explanation": "Storing credentials, passwords, or token keys as string literals inside variable definitions leaves keys readable in public code repos, which can lead to unauthorized service access.",
                "recommendation": "Extract credentials secrets to environment configuration files (e.g. .env) that are git-ignored.",
                "corrected_code": "import os\napi_secret = os.getenv('API_SECRET_KEY')"
            },
            {
                "id": "SEC-002",
                "pattern": re.compile(r"\bexecute\(\s*(f['\"].*SELECT.*\{.*\}['\"]|['\"].*SELECT.*['\"]\s*%\s*\w+|['\"].*SELECT.*['\"]\.format\()", re.IGNORECASE),
                "title": "SQL Injection via Query Formatter Concatenation",
                "severity": "Critical",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-89",
                "confidence": "High",
                "description": "Constructing SQL statements dynamically using formatting (f-strings or .format) executes parameters as database command blocks.",
                "risk_explanation": "Dynamic string concatenations or formatting inside SQL queries executes parameter strings as active database commands, allowing unauthorized access or data deletion.",
                "recommendation": "Use SQLAlchemy parameterized query parameters bindings.",
                "corrected_code": "db.execute(text('SELECT * FROM users WHERE name = :name'), {'name': user_input})"
            },
            {
                "id": "SEC-003",
                "pattern": re.compile(r"\bHTMLResponse\(\s*content\s*=\s*f?['\"].*\{.*\}.*['\"]|\brender_template_string\(\s*f?['\"].*\{.*\}.*['\"]", re.IGNORECASE),
                "title": "Cross-Site Scripting (XSS) via Unescaped HTML responses",
                "severity": "High",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-79",
                "confidence": "High",
                "description": "Returning raw, unescaped HTML content parameter strings allows client browsers to execute malicious javascript code.",
                "risk_explanation": "Outputting raw request parameters directly to HTML responses lets client browsers parse and execute malicious javascript snippets in the context of the user's session.",
                "recommendation": "Sanitize output strings using HTML template layouts or escape packages.",
                "corrected_code": "import html\nreturn HTMLResponse(content=f'<h1>{html.escape(user_input)}</h1>')"
            },
            {
                "id": "SEC-004",
                "pattern": re.compile(r"WTF_CSRF_ENABLED\s*=\s*False|csrf_protect\s*=\s*False|@csrf_exempt", re.IGNORECASE),
                "title": "CSRF Safety Controls Disabled",
                "severity": "High",
                "classification": "OWASP A05:2021-Security Misconfiguration",
                "cwe": "CWE-352",
                "confidence": "High",
                "description": "WTF_CSRF_ENABLED has been set to False or CSRF validation checks are explicitly skipped, opening user state change leaks.",
                "risk_explanation": "Disabling Cross-Site Request Forgery controls allows malicious web scripts to submit post/delete requests on behalf of logged-in sessions.",
                "recommendation": "Enable CSRF protection globally in configuration settings for all POST/PUT requests.",
                "corrected_code": "WTF_CSRF_ENABLED = True"
            },
            {
                "id": "SEC-005",
                "pattern": re.compile(r"algorithm\s*=\s*['\"]none['\"]|jwt\.encode\(.*algorithm\s*=\s*['\"]none['\"]|jwt\.decode\(.*verify\s*=\s*False", re.IGNORECASE),
                "title": "Broken Authentication via JWT 'none' Algorithm",
                "severity": "Critical",
                "classification": "OWASP A07:2021-Identification and Authentication Failures",
                "cwe": "CWE-287",
                "confidence": "High",
                "description": "JWT tokens are created with the alg claim set to none. This allows clients to forge signatures and bypass auth.",
                "risk_explanation": "Enabling JWT signature creation using algorithm 'none' or implementing plaintext encoders allows token forging and credential compromises.",
                "recommendation": "Enforce strong signing algorithms (e.g. HS256, RS256) and reject none algorithms explicitly during decodes.",
                "corrected_code": "jwt.encode(payload, key, algorithm='HS256')"
            },
            {
                "id": "SEC-006",
                "pattern": re.compile(r"\bopen\(\s*(f['\"].*\{.*?path.*?|.*?file_name.*?\}['\"]|['\"].*?['\"]\s*\+\s*\w+)\)", re.IGNORECASE),
                "title": "Path Traversal File Read Vulnerability",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-22",
                "confidence": "Medium",
                "description": "Using dynamic strings directly in open() functions allows attackers to read files outside restricted directories using double dots (../).",
                "risk_explanation": "Constructing file system paths directly using input variables lets attackers fetch unauthorized server directories using double-dots (../).",
                "recommendation": "Sanitize filenames using `os.path.basename()` or verify paths reside within an authorized root directory.",
                "corrected_code": "import os\nsafe_path = os.path.abspath(os.path.join('/tmp/', os.path.basename(user_input)))"
            },
            {
                "id": "SEC-007",
                "pattern": re.compile(r"os\.(system|popen)\(|subprocess\.(Popen|run|call)\(.*shell\s*=\s*True", re.IGNORECASE),
                "title": "OS Command Shell Injection",
                "severity": "Critical",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-78",
                "confidence": "High",
                "description": "Invoking system shells (shell=True) via os.system or subprocess runs unvalidated strings as direct terminal inputs.",
                "risk_explanation": "Running raw terminal subshells executes user inputs directly as OS shell commands, leading to full Remote Code Execution (RCE).",
                "recommendation": "Set shell=False and pass arguments as lists: `subprocess.run(['command', 'arg1'])`.",
                "corrected_code": "import subprocess\nsubprocess.run(['echo', user_input], shell=False)"
            },
            {
                "id": "SEC-008",
                "pattern": re.compile(r"hashlib\.(md5|sha1)\(|Cipher\.getInstance\(['\"]DES['\"]\)|DES\.new\(", re.IGNORECASE),
                "title": "Weak Cryptographic Hashing Algorithm",
                "severity": "Medium",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-327",
                "confidence": "High",
                "description": "MD5 or SHA-1 hashes are weak, prone to collision exploits, and insecure for password hashing.",
                "risk_explanation": "MD5 and SHA-1 hashing algorithms are cryptographically broken, prone to collision attacks, and insecure for password hashing.",
                "recommendation": "Upgrade to secure hashing structures (e.g., bcrypt, Argon2, or SHA-256).",
                "corrected_code": "import bcrypt\nhash_val = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
            },
            {
                "id": "SEC-009",
                "pattern": re.compile(r"pickle\.loads\(|yaml\.unsafe_load\(|shelve\.open\(", re.IGNORECASE),
                "title": "Insecure Deserialization via pickle/yaml loading",
                "severity": "Critical",
                "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                "cwe": "CWE-502",
                "confidence": "High",
                "description": "Using pickle.loads or yaml.unsafe_load on untrusted inputs allows arbitrary code execution during object load.",
                "risk_explanation": "Restoring serialized byte blocks from untrusted inputs lets custom objects call classes inside constructors, enabling arbitrary code injection.",
                "recommendation": "Use safe JSON serialization or safe YAML parsers (`yaml.safe_load`).",
                "corrected_code": "import json\ndata = json.loads(user_json)"
            },
            {
                "id": "SEC-010",
                "pattern": re.compile(r"requests\.(get|post|put|delete)\(\s*(url|target_url|user_url|\w+)\)|urllib\.request\.urlopen\(", re.IGNORECASE),
                "title": "Server-Side Request Forgery (SSRF)",
                "severity": "High",
                "classification": "OWASP A10:2021-Server-Side Request Forgery",
                "cwe": "CWE-918",
                "confidence": "Medium",
                "description": "Sending HTTP requests using dynamic input parameters allows attackers to trigger internal request scans.",
                "risk_explanation": "Opening HTTP connections to variable input domains lets attackers scan local virtual interfaces or cloud metadata nodes.",
                "recommendation": "Use a whitelist of allowed domains and block requests directed to local loops (localhost/127.0.0.1).",
                "corrected_code": "if target_host in ALLOWED_DOMAINS:\n    requests.get(target_url)"
            },
            {
                "id": "SEC-011",
                "pattern": re.compile(r"(password|passwd|pwd)\s*=\s*['\"][a-zA-Z0-9_\-\+\/@#$%^&*()!]{8,}['\"]", re.IGNORECASE),
                "title": "Hardcoded Passwords",
                "severity": "High",
                "classification": "OWASP A07:2021-Identification and Authentication Failures",
                "cwe": "CWE-259",
                "confidence": "High",
                "description": "Plaintext passwords or database credentials are declared directly as variables in the source code.",
                "risk_explanation": "Hardcoding sensitive credentials in source code exposes them to anyone with read access to the repository, potentially leading to unauthorized system access.",
                "recommendation": "Move password credentials to configuration files or load them via environment variables.",
                "corrected_code": "db_password = os.getenv('DB_PASSWORD')"
            },
            {
                "id": "SEC-012",
                "pattern": re.compile(r"\ballow_all\s*=\s*True|\badmin_bypass\s*=\s*True|role\s*==\s*['\"]anonymous['\"]|auth\s*=\s*None\b", re.IGNORECASE),
                "title": "Broken Access Control",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-284",
                "confidence": "High",
                "description": "Access control variables or permissions flags are configured to bypass authentication, allowing anonymous users to access administrative features.",
                "risk_explanation": "Failing to check user authentication state or permissions when performing actions exposes private endpoints to unauthorized manipulation.",
                "recommendation": "Enforce robust, role-based authorization checks at the handler or middleware layer.",
                "corrected_code": "if current_user.role == 'Admin':\n    proceed()"
            },
            {
                "id": "SEC-013",
                "pattern": re.compile(r"\bprint\((.*password.*|.*secret.*|.*token.*|.*api_key.*)\)|\blogging\.(info|debug|warning|error)\((.*password.*|.*secret.*|.*token.*|.*api_key.*)\)", re.IGNORECASE),
                "title": "Sensitive Data Exposure",
                "severity": "High",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-312",
                "confidence": "High",
                "description": "Writing sensitive credentials, tokens, or personal identifiers directly to logger outputs or standard streams.",
                "risk_explanation": "Exposing sensitive variables through stdout or logger outputs writes credentials into persistent files, which can be read by administrators or monitoring tools.",
                "recommendation": "Redact or mask sensitive parameters before writing them to console streams or logger blocks.",
                "corrected_code": "logging.info(f'User logged in: {username}')"
            },
            {
                "id": "SEC-014",
                "pattern": re.compile(r"\.save\(\s*(upload|file)\.filename\)|upload_file\s*=\s*open\(\s*\w+\.filename", re.IGNORECASE),
                "title": "Unsafe File Upload",
                "severity": "High",
                "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                "cwe": "CWE-434",
                "confidence": "High",
                "description": "Accepting uploads using raw user-supplied file names allows attackers to overwrite system configurations or run arbitrary scripts.",
                "risk_explanation": "Uploading files directly under the client's file name can result in path traversal writes, script execution, or arbitrary system overrides.",
                "recommendation": "Use secure filename functions like `werkzeug.utils.secure_filename` and validate file extensions before writing files.",
                "corrected_code": "safe_name = secure_filename(file.filename)"
            },
            {
                "id": "SEC-015",
                "pattern": re.compile(r"\bimport\s+random|\brandom\.randint\(|\brandom\.random\(|\brandom\.choice\(", re.IGNORECASE),
                "title": "Insecure Random Number Generation",
                "severity": "Medium",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-338",
                "confidence": "High",
                "description": "Using python's built-in pseudo-random numbers module (random) for security tokens, salts, or passwords.",
                "risk_explanation": "Pseudo-random generators generate numbers in a predictable sequence, making generated security tokens/hashes vulnerable to brute-force prediction.",
                "recommendation": "Use the `secrets` module for security-sensitive random number requirements.",
                "corrected_code": "import secrets\ntoken = secrets.token_hex(16)"
            },
            {
                "id": "SEC-016",
                "pattern": re.compile(r"os\.path\.join\(.*,\s*(user_input|path|filename)\)|os\.listdir\(\s*(user_input|path|filename)\)", re.IGNORECASE),
                "title": "Directory Traversal",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-22",
                "confidence": "High",
                "description": "Concatenating user-supplied input strings directly to directory path variables allows directory listing leaks.",
                "risk_explanation": "Allowing users to control parameters used in file paths can expose directories or delete contents if parameters contain double-dots.",
                "recommendation": "Normalize the path using `os.path.realpath` and assert that it begins with the authorized base path.",
                "corrected_code": "if os.path.realpath(target).startswith(base_dir):\n    list_files()"
            },
            {
                "id": "SEC-017",
                "pattern": re.compile(r"RedirectResponse\(\s*(url|target|user_url|redirect_url|next)\s*\)|redirect\(\s*(url|target|user_url|redirect_url|next)\s*\)", re.IGNORECASE),
                "title": "Open Redirect",
                "severity": "Medium",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-601",
                "confidence": "Medium",
                "description": "Redirecting users dynamically based on parameters without checking their target domains.",
                "risk_explanation": "Redirecting users to dynamic URL parameters lets attackers orchestrate phishing campaigns by redirecting authentic users to malicious sites.",
                "recommendation": "Enforce redirection whitelists or check that target URLs reside in internal hosts.",
                "corrected_code": "if is_safe_url(redirect_url):\n    return RedirectResponse(redirect_url)"
            },
            {
                "id": "SEC-018",
                "pattern": re.compile(r"xml\.etree\.ElementTree\.parse\(|lxml\.etree\.parse\(|XMLParser\(.*resolve_entities\s*=\s*True", re.IGNORECASE),
                "title": "XXE",
                "severity": "High",
                "classification": "OWASP A05:2021-Security Misconfiguration",
                "cwe": "CWE-611",
                "confidence": "High",
                "description": "Parsing XML data using default libraries without disabling DTD schemas or external entity parsing.",
                "risk_explanation": "Vulnerable XML parsers read references to external entities, enabling attackers to read local files, trigger SSRF requests, or execute denial of service attacks.",
                "recommendation": "Disable external entity resolution or use `defusedxml` to parse untrusted XML structures.",
                "corrected_code": "from defusedxml.ElementTree import parse\nparse(xml_file)"
            },
            {
                "id": "SEC-019",
                "pattern": re.compile(r"request\.(args|json|form)\.get\(['\"][a-zA-Z0-9_]+['\"]\)(?!\.isdigit\(\))(?!\.isalpha\(\))(?!\.replace\(\))", re.IGNORECASE),
                "title": "Missing Input Validation",
                "severity": "Medium",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-20",
                "confidence": "Medium",
                "description": "Processing parameters read directly from query/body streams without bounds checking or format validation.",
                "risk_explanation": "Accepting unvalidated inputs makes applications vulnerable to overflow, type coercion failures, or general logic exploitation.",
                "recommendation": "Use Pydantic schemas or type-cast and parse values to restrict parameters to predefined boundaries.",
                "corrected_code": "user_id = int(request.args.get('id'))"
            }
        ]

    def scan_code(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        vulnerabilities = []
        lines = code.split("\n")
        affected_file = filename if filename else "main.py"
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()
            
            if stripped.startswith("#") or not stripped:
                continue

            for rule in self.rules:
                # Avoid false positives for mock secrets in tests
                if rule["id"] in ["SEC-001", "SEC-011"]:
                    if "mock" in stripped.lower() or "test" in stripped.lower():
                        continue
                # Avoid false positives for requests/SSRF checks containing clear internal mock urls
                if rule["id"] == "SEC-010" and "http" in stripped.lower() and not ("requests" in stripped.lower() and ("url" in stripped.lower() or "target" in stripped.lower() or "user" in stripped.lower())):
                    # if it hardcodes an exact HTTP path instead of taking a parameter variable
                    if re.search(r"['\"]https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}", stripped):
                        continue

                if rule["pattern"].search(stripped):
                    vulnerabilities.append({
                        "id": rule["id"],
                        "line": line_num,
                        "line_number": line_num,
                        "title": rule["title"],
                        "Issue Name": rule["title"],
                        "issue_name": rule["title"],
                        "severity": rule["severity"],
                        "Severity": rule["severity"],
                        "classification": rule["classification"],
                        "OWASP Category": rule["classification"],
                        "owasp_category": rule["classification"],
                        "cwe": rule["cwe"],
                        "confidence": "High" if rule["id"] not in ["SEC-006", "SEC-010", "SEC-017", "SEC-019"] else "Medium",
                        "description": rule["description"],
                        "Description": rule["description"],
                        "Affected File": affected_file,
                        "affected_file": affected_file,
                        "Line Number": line_num,
                        "Code Snippet": stripped,
                        "code_snippet": stripped,
                        "snippet": stripped,
                        "Risk Explanation": rule["risk_explanation"],
                        "risk_explanation": rule["risk_explanation"],
                        "recommendation": rule["recommendation"],
                        "Recommended Fix": rule["recommendation"],
                        "recommended_fix": rule["recommendation"],
                        "Corrected Code Example": rule["corrected_code"],
                        "corrected_code_example": rule["corrected_code"]
                    })
        return vulnerabilities


# ==========================================
# Java Scanner Implementation
# ==========================================

class JavaScanner(BaseLanguageScanner):
    """Static security rules engine for auditing Java source files."""

    def __init__(self):
        self.rules = [
            {
                "id": "SEC-001",
                "pattern": re.compile(r"String\s+(api_key|apikey|secret|token)\s*=\s*\"[a-zA-Z0-9_\-\+\/]{8,}\";", re.IGNORECASE),
                "title": "Hardcoded Cryptographic Secrets or Token Keys",
                "severity": "High",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-798",
                "confidence": "High",
                "description": "Plaintext secret token keys or credentials variables are declared directly in source code.",
                "risk_explanation": "Storing credentials, passwords, or token keys as string literals inside variable definitions leaves keys readable in public code repos.",
                "recommendation": "Extract credentials secrets to environment configuration files (e.g. .env) that are git-ignored.",
                "corrected_code": "String apiSecret = System.getenv(\"API_SECRET_KEY\");"
            },
            {
                "id": "SEC-002",
                "pattern": re.compile(r"\"SELECT\s+.*\s+WHERE\s+.*\s*=\s*'\s*\"\s*\+\s*\w+|executeQuery\(\s*.*?\s*\+\s*.*?\)", re.IGNORECASE),
                "title": "SQL Injection via Java String Concatenation",
                "severity": "Critical",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-89",
                "confidence": "High",
                "description": "Concatenating variables into SQL queries bypasses syntax separation, allowing query logic modifications.",
                "risk_explanation": "Concatenating variables into SQL queries bypasses syntax separation, allowing query logic modifications.",
                "recommendation": "Replace Statement string concats with PreparedStatement parameterized query parameters.",
                "corrected_code": "PreparedStatement stmt = conn.prepareStatement(\"SELECT * FROM users WHERE name = ?\");\nstmt.setString(1, user_input);"
            },
            {
                "id": "SEC-003",
                "pattern": re.compile(r"response\.getWriter\(\)\.write\(\s*\w+\)|out\.(print|println)\(\s*request\.getParameter", re.IGNORECASE),
                "title": "Cross-Site Scripting (XSS) in Java Servlet Output",
                "severity": "High",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-79",
                "confidence": "High",
                "description": "Printing unescaped request parameters to servlet response streams allows malicious script code executions.",
                "risk_explanation": "Printing unescaped request parameters to servlet response streams allows malicious script code executions.",
                "recommendation": "Escape inputs using HTML wrapper utils (e.g. Apache StringEscapeUtils).",
                "corrected_code": "response.getWriter().write(StringEscapeUtils.escapeHtml4(user_input));"
            },
            {
                "id": "SEC-004",
                "pattern": re.compile(r"\.csrf\(\)\.disable\(\)|csrf\s*->\s*csrf\.disable\(\)", re.IGNORECASE),
                "title": "Java Spring CSRF Security Controls Disabled",
                "severity": "High",
                "classification": "OWASP A05:2021-Security Misconfiguration",
                "cwe": "CWE-352",
                "confidence": "High",
                "description": "Spring Security CSRF checks are explicitly disabled in config setups, facilitating state forgery bugs.",
                "risk_explanation": "Spring Security CSRF checks are explicitly disabled in config setups, facilitating state forgery bugs.",
                "recommendation": "Enable CSRF controls and include anti-CSRF tokens in AJAX headers.",
                "corrected_code": "// CSRF protection enabled automatically in modern Spring configurations"
            },
            {
                "id": "SEC-005",
                "pattern": re.compile(r"InMemoryUserDetailsManager|NoOpPasswordEncoder", re.IGNORECASE),
                "title": "Broken Authentication via Insecure Password Encoder",
                "severity": "Critical",
                "classification": "OWASP A07:2021-Identification and Authentication Failures",
                "cwe": "CWE-287",
                "confidence": "High",
                "description": "Using NoOpPasswordEncoder or hardcoded in-memory user lists stores credentials in plaintext formats.",
                "risk_explanation": "Using NoOpPasswordEncoder or hardcoded in-memory user lists stores credentials in plaintext formats.",
                "recommendation": "Configure BCryptPasswordEncoder or Argon2 for secure database credentials checks.",
                "corrected_code": "PasswordEncoder encoder = new BCryptPasswordEncoder();"
            },
            {
                "id": "SEC-006",
                "pattern": re.compile(r"new\s+(FileInputStream|File|FileReader)\(\s*(\w+|[^)]*?\+[^)]*?|request\.getParameter)", re.IGNORECASE),
                "title": "Java Path Traversal File Stream Access",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-22",
                "confidence": "Medium",
                "description": "Initializing file inputs using concatenated parameter requests allows attackers to retrieve root file paths.",
                "risk_explanation": "Initializing file inputs using concatenated parameter requests allows attackers to retrieve root file paths.",
                "recommendation": "Use path normalization and restrict access to specific base directories.",
                "corrected_code": "File safeFile = new File(\"/tmp/\", new File(user_input).getName());"
            },
            {
                "id": "SEC-007",
                "pattern": re.compile(r"Runtime\.getRuntime\(\)\.exec\(|new\s+ProcessBuilder\(", re.IGNORECASE),
                "title": "Java OS Command Execution Injection",
                "severity": "Critical",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-78",
                "confidence": "High",
                "description": "Executing system prompts using Runtime.exec with raw strings runs parameters as terminal commands.",
                "risk_explanation": "Executing system prompts using Runtime.exec with raw strings runs parameters as terminal commands.",
                "recommendation": "Avoid using Runtime.exec with raw strings; run commands via ProcessBuilder array blocks.",
                "corrected_code": "new ProcessBuilder(\"echo\", user_input).start();"
            },
            {
                "id": "SEC-008",
                "pattern": re.compile(r"MessageDigest\.getInstance\(['\"](MD5|SHA-1)['\"]\)|Cipher\.getInstance\(['\"]DES|Blowfish|RC4['\"]", re.IGNORECASE),
                "title": "Weak Hashing MessageDigest Algorithm",
                "severity": "Medium",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-327",
                "confidence": "High",
                "description": "Java MessageDigest is configured to use insecure hash algorithms (MD5, SHA-1).",
                "risk_explanation": "Java MessageDigest is configured to use insecure hash algorithms (MD5, SHA-1).",
                "recommendation": "Upgrade cryptographic hashing classes to SHA-256 or SHA-512 instances.",
                "corrected_code": "PasswordEncoder encoder = new BCryptPasswordEncoder();"
            },
            {
                "id": "SEC-009",
                "pattern": re.compile(r"ObjectInputStream\.readObject\(|XMLDecoder\.readObject\(", re.IGNORECASE),
                "title": "Java Insecure ObjectInputStream Deserialization",
                "severity": "Critical",
                "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                "cwe": "CWE-502",
                "confidence": "High",
                "description": "Invoking readObject() on ObjectInputStream parses bytes directly, enabling arbitrary object instances instantiations.",
                "risk_explanation": "Invoking readObject() on ObjectInputStream parses bytes directly, enabling arbitrary object instances instantiations.",
                "recommendation": "Implement class-validation filters or use JSON parsing libraries.",
                "corrected_code": "// Configure safer ObjectInputStream filters or parse inputs using Jackson ObjectMapper"
            },
            {
                "id": "SEC-010",
                "pattern": re.compile(r"new\s+URL\(\s*(url|target_url|\w+)\)\.openStream\(|new\s+URL\(\s*(url|target_url|\w+)\)\.openConnection\(", re.IGNORECASE),
                "title": "Java Server-Side Request Forgery (SSRF)",
                "severity": "High",
                "classification": "OWASP A10:2021-Server-Side Request Forgery",
                "cwe": "CWE-918",
                "confidence": "Medium",
                "description": "Initiating network requests from dynamic inputs allows server-level network scans.",
                "risk_explanation": "Initiating network requests from dynamic inputs allows server-level network scans.",
                "recommendation": "Validate requested URL patterns against strict domain whitelist configurations.",
                "corrected_code": "if (ALLOWED_DOMAINS.contains(targetHost)) {\n    new URL(targetUrl).openStream();\n}"
            },
            {
                "id": "SEC-011",
                "pattern": re.compile(r"String\s+(password|passwd|pwd)\s*=\s*\"[^\"]{8,}\";|private\s+static\s+final\s+String\s+PASSWORD\s*=\s*\"[^\"]{8,}\";", re.IGNORECASE),
                "title": "Hardcoded Passwords",
                "severity": "High",
                "classification": "OWASP A07:2021-Identification and Authentication Failures",
                "cwe": "CWE-259",
                "confidence": "High",
                "description": "Plaintext passwords or database credentials are declared directly as literal strings in Java source code.",
                "risk_explanation": "Hardcoding sensitive credentials in source code exposes them to anyone with read access to the repository, potentially leading to unauthorized system access.",
                "recommendation": "Move password credentials to configuration files or load them via environment variables.",
                "corrected_code": "String dbPassword = System.getenv(\"DB_PASSWORD\");"
            },
            {
                "id": "SEC-012",
                "pattern": re.compile(r"\.authorizeRequests\(\)\.anyRequest\(\)\.permitAll\(\)", re.IGNORECASE),
                "title": "Broken Access Control",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-284",
                "confidence": "High",
                "description": "Access control variables or permissions configurations are set to permit all requests without role verification.",
                "risk_explanation": "Failing to check user authentication state or permissions when performing actions exposes private endpoints to unauthorized manipulation.",
                "recommendation": "Enforce robust, role-based authorization checks at the handler or middleware layer.",
                "corrected_code": "http.authorizeRequests().anyRequest().authenticated();"
            },
            {
                "id": "SEC-013",
                "pattern": re.compile(r"System\.out\.print(ln)?\(.*(password|secret|token).*?\)|log(ger)?\.(info|debug|warn|error)\(.*(password|secret|token).*?\)", re.IGNORECASE),
                "title": "Sensitive Data Exposure",
                "severity": "High",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-312",
                "confidence": "High",
                "description": "Writing sensitive credentials, tokens, or personal identifiers directly to logger outputs or System.out streams.",
                "risk_explanation": "Exposing sensitive variables through stdout or logger outputs writes credentials into persistent files, which can be read by administrators or monitoring tools.",
                "recommendation": "Redact or mask sensitive parameters before writing them to console streams or logger blocks.",
                "corrected_code": "logger.info(\"User logged in successfully\");"
            },
            {
                "id": "SEC-014",
                "pattern": re.compile(r"multipartFile\.getOriginalFilename\(\)|file\.transferTo\(", re.IGNORECASE),
                "title": "Unsafe File Upload",
                "severity": "High",
                "classification": "OWASP A08:2021-Software and Data Integrity Failures",
                "cwe": "CWE-434",
                "confidence": "High",
                "description": "Accepting uploads using raw user-supplied file names allows attackers to overwrite system configurations or run arbitrary scripts.",
                "risk_explanation": "Uploading files directly under the client's file name can result in path traversal writes, script execution, or arbitrary system overrides.",
                "recommendation": "Use secure filename functions and validate file extensions before writing files.",
                "corrected_code": "String safeName = FilenameUtils.getName(multipartFile.getOriginalFilename());"
            },
            {
                "id": "SEC-015",
                "pattern": re.compile(r"new\s+Random\(\)|Random\s+\w+\s*=\s*new\s+Random", re.IGNORECASE),
                "title": "Insecure Random Number Generation",
                "severity": "Medium",
                "classification": "OWASP A02:2021-Cryptographic Failures",
                "cwe": "CWE-338",
                "confidence": "High",
                "description": "Using standard Random class for security tokens, salts, or passwords.",
                "risk_explanation": "Pseudo-random generators generate numbers in a predictable sequence, making generated security tokens/hashes vulnerable to brute-force prediction.",
                "recommendation": "Use SecureRandom for security-sensitive random number requirements.",
                "corrected_code": "SecureRandom random = new SecureRandom();"
            },
            {
                "id": "SEC-016",
                "pattern": re.compile(r"new\s+File\((request\.getPathInfo\(\)|request\.getServletPath\(\))\)", re.IGNORECASE),
                "title": "Directory Traversal",
                "severity": "High",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-22",
                "confidence": "High",
                "description": "Concatenating user-supplied input strings directly to directory path variables allows directory listing leaks.",
                "risk_explanation": "Allowing users to control parameters used in file paths can expose directories or delete contents if parameters contain double-dots.",
                "recommendation": "Normalize the path and assert that it begins with the authorized base path.",
                "corrected_code": "File safeFile = new File(\"/tmp/\", new File(userInput).getName());"
            },
            {
                "id": "SEC-017",
                "pattern": re.compile(r"response\.sendRedirect\(\s*(request\.getParameter|url)\s*\)", re.IGNORECASE),
                "title": "Open Redirect",
                "severity": "Medium",
                "classification": "OWASP A01:2021-Broken Access Control",
                "cwe": "CWE-601",
                "confidence": "Medium",
                "description": "Redirecting users dynamically based on parameters without checking their target domains.",
                "risk_explanation": "Redirecting users to dynamic URL parameters lets attackers orchestrate phishing campaigns by redirecting authentic users to malicious sites.",
                "recommendation": "Enforce redirection whitelists or check that target URLs reside in internal hosts.",
                "corrected_code": "if (isSafeUrl(redirectUrl)) { response.sendRedirect(redirectUrl); }"
            },
            {
                "id": "SEC-018",
                "pattern": re.compile(r"DocumentBuilderFactory\.newInstance\(", re.IGNORECASE),
                "title": "XXE",
                "severity": "High",
                "classification": "OWASP A05:2021-Security Misconfiguration",
                "cwe": "CWE-611",
                "confidence": "High",
                "description": "Parsing XML data using default libraries without disabling DTD schemas or external entity parsing.",
                "risk_explanation": "Vulnerable XML parsers read references to external entities, enabling attackers to read local files, trigger SSRF requests, or execute denial of service attacks.",
                "recommendation": "Disable external entity resolution features on the DocumentBuilderFactory instance.",
                "corrected_code": "DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();\ndbf.setFeature(\"http://apache.org/xml/features/disallow-doctype-decl\", true);"
            },
            {
                "id": "SEC-019",
                "pattern": re.compile(r"request\.getParameter\(['\"][a-zA-Z0-9_]+['\"]\)(?!\.matches)(?!\.replaceAll)", re.IGNORECASE),
                "title": "Missing Input Validation",
                "severity": "Medium",
                "classification": "OWASP A03:2021-Injection",
                "cwe": "CWE-20",
                "confidence": "Medium",
                "description": "Processing parameters read directly from request query parameters without validating pattern matches or replacing bad characters.",
                "risk_explanation": "Accepting unvalidated inputs makes applications vulnerable to overflow, type coercion failures, or general logic exploitation.",
                "recommendation": "Validate request parameters using regex matches or type castings.",
                "corrected_code": "String userInput = request.getParameter(\"id\");\nif (userInput != null && userInput.matches(\"\\\\d+\")) { int id = Integer.parseInt(userInput); }"
            }
        ]

    def scan_code(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        vulnerabilities = []
        lines = code.split("\n")
        affected_file = filename if filename else "Main.java"
        
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()
            
            if stripped.startswith("//") or not stripped:
                continue

            for rule in self.rules:
                # Avoid false positives for mock secrets in tests
                if rule["id"] in ["SEC-001", "SEC-011"]:
                    if "mock" in stripped.lower() or "test" in stripped.lower():
                        continue
                # Avoid false positives for SSRF checks containing clear internal mock urls
                if rule["id"] == "SEC-010" and "http" in stripped.lower() and not ("new URL" in stripped.lower() and ("url" in stripped.lower() or "target" in stripped.lower())):
                    if re.search(r"['\"]https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}", stripped):
                        continue

                if rule["pattern"].search(stripped):
                    vulnerabilities.append({
                        "id": rule["id"],
                        "line": line_num,
                        "line_number": line_num,
                        "title": rule["title"],
                        "Issue Name": rule["title"],
                        "issue_name": rule["title"],
                        "severity": rule["severity"],
                        "Severity": rule["severity"],
                        "classification": rule["classification"],
                        "OWASP Category": rule["classification"],
                        "owasp_category": rule["classification"],
                        "cwe": rule["cwe"],
                        "confidence": "High" if rule["id"] not in ["SEC-006", "SEC-010", "SEC-017", "SEC-019"] else "Medium",
                        "description": rule["description"],
                        "Description": rule["description"],
                        "Affected File": affected_file,
                        "affected_file": affected_file,
                        "Line Number": line_num,
                        "Code Snippet": stripped,
                        "code_snippet": stripped,
                        "snippet": stripped,
                        "Risk Explanation": rule["risk_explanation"],
                        "risk_explanation": rule["risk_explanation"],
                        "recommendation": rule["recommendation"],
                        "Recommended Fix": rule["recommendation"],
                        "recommended_fix": rule["recommendation"],
                        "Corrected Code Example": rule["corrected_code"],
                        "corrected_code_example": rule["corrected_code"]
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
        # Check if there is an affected file in the state or default it
        filename = "main.py" if language == "python" else "Main.java"
        vulnerabilities = scanner.scan_code(code, filename=filename)

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
