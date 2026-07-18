from backend.app.agents.state import AgentState

def remediation_agent_node(state: AgentState) -> dict:
    """Agent node that inspects flagged vulnerabilities and outputs detailed, language-specific code remediation guides."""
    security_analysis = state.get("security_analysis", {}) or {}
    vulnerabilities = security_analysis.get("vulnerabilities", []) or []
    language = state.get("language", "python").lower()
    
    remediations = []

    for vuln in vulnerabilities:
        vuln_id = vuln.get("id")
        line = vuln.get("line", 1)
        severity = vuln.get("severity", "Medium")
        snippet = vuln.get("snippet", "")
        
        # Build structured remediation report item
        guide = {
            "vulnerability_id": vuln_id,
            "line": line,
            "title": vuln.get("title", "Security Vulnerability"),
            "severity": severity,
            "explanation": "",
            "corrected_code": "",
            "recommendation": "",
            "reference": vuln.get("cwe", "CWE-393") + " | " + vuln.get("classification", "OWASP Top 10"),
            "code_comparison": {
                "before": snippet,
                "after": ""
            }
        }

        # 1. Hardcoded Secrets (SEC-001)
        if vuln_id == "SEC-001":
            guide["explanation"] = "Storing credentials, passwords, or token keys as string literals inside variable definitions leaves keys readable in public code repos."
            guide["recommendation"] = "Store credential configurations inside environment variables or read them dynamically from secrets managers (e.g. AWS Secrets Manager)."
            if language == "python":
                guide["corrected_code"] = "import os\napi_secret = os.getenv('API_SECRET_KEY')"
            else:
                guide["corrected_code"] = "String apiSecret = System.getenv(\"API_SECRET_KEY\");"
        
        # 2. SQL Injection (SEC-002)
        elif vuln_id == "SEC-002":
            guide["explanation"] = "Dynamic string concatenations or formatting inside SQL queries executes parameter strings as active database commands, allowing unauthorized access or data deletion."
            guide["recommendation"] = "Enforce parameterized queries or prepare statements so input values are parsed strictly as parameters, never as SQL syntax blocks."
            if language == "python":
                guide["corrected_code"] = "db.execute(text('SELECT * FROM users WHERE name = :name'), {'name': user_input})"
            else:
                guide["corrected_code"] = "PreparedStatement stmt = conn.prepareStatement(\"SELECT * FROM users WHERE name = ?\");\nstmt.setString(1, user_input);"
        
        # 3. Cross-Site Scripting (SEC-003)
        elif vuln_id == "SEC-003":
            guide["explanation"] = "Outputting raw request parameters directly to HTML responses lets client browsers parse and execute malicious javascript snippets."
            guide["recommendation"] = "Escape HTML content formatting before printing values to DOM blocks or configure templates to enforce automatic escapes."
            if language == "python":
                guide["corrected_code"] = "import html\nreturn HTMLResponse(content=f'<h1>{html.escape(user_input)}</h1>')"
            else:
                guide["corrected_code"] = "response.getWriter().write(StringEscapeUtils.escapeHtml4(user_input));"

        # 4. CSRF disabled (SEC-004)
        elif vuln_id == "SEC-004":
            guide["explanation"] = "Disabling Cross-Site Request Forgery controls allows malicious web scripts to submit post/delete requests on behalf of logged-in sessions."
            guide["recommendation"] = "Enforce global CSRF validation tokens in Spring configurations or Flask settings."
            if language == "python":
                guide["corrected_code"] = "WTF_CSRF_ENABLED = True"
            else:
                guide["corrected_code"] = "// CSRF protection enabled automatically in modern Spring configurations"

        # 5. Broken Auth (SEC-005)
        elif vuln_id == "SEC-005":
            guide["explanation"] = "Enabling JWT signature creation using algorithm 'none' or implementing plaintext encoders allows token forging and credential compromises."
            guide["recommendation"] = "Require cryptographically strong hash algorithms (e.g. HS256/RS256) and reject 'none' values explicitly."
            if language == "python":
                guide["corrected_code"] = "jwt.encode(payload, key, algorithm='HS256')"
            else:
                guide["corrected_code"] = "PasswordEncoder encoder = new BCryptPasswordEncoder();"

        # 6. Path Traversal (SEC-006)
        elif vuln_id == "SEC-006":
            guide["explanation"] = "Constructing file system paths directly using input variables lets attackers fetch unauthorized server directories using double-dots (../)."
            guide["recommendation"] = "Sanitize filenames using basename extractions and assert files reside inside restricted target sub-directories."
            if language == "python":
                guide["corrected_code"] = "import os\nsafe_path = os.path.abspath(os.path.join('/tmp/', os.path.basename(user_input)))"
            else:
                guide["corrected_code"] = "File safeFile = new File(\"/tmp/\", new File(user_input).getName());"

        # 7. Command Injection (SEC-007)
        elif vuln_id == "SEC-007":
            guide["explanation"] = "Running raw terminal subshells executes user inputs directly as OS shell commands, leading to full Remote Code Execution (RCE)."
            guide["recommendation"] = "Set shell=False and pass arguments as lists, or avoid system shells in favor of safe standard libraries."
            if language == "python":
                guide["corrected_code"] = "import subprocess\nsubprocess.run(['echo', user_input], shell=False)"
            else:
                guide["corrected_code"] = "new ProcessBuilder(\"echo\", user_input).start();"

        # 8. Weak Cryptography (SEC-008)
        elif vuln_id == "SEC-008":
            guide["explanation"] = "MD5 and SHA-1 hashing algorithms are cryptographically broken, prone to collision attacks, and insecure for password hashing."
            guide["recommendation"] = "Implement strong slow-hashing algorithms (e.g. BCrypt, Argon2, PBKDF2) to hash passwords."
            if language == "python":
                guide["corrected_code"] = "import bcrypt\nhash_val = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
            else:
                guide["corrected_code"] = "PasswordEncoder encoder = new BCryptPasswordEncoder();"

        # 9. Insecure Deserialization (SEC-009)
        elif vuln_id == "SEC-009":
            guide["explanation"] = "Restoring serialized byte blocks from untrusted inputs lets custom objects call classes inside constructors, enabling arbitrary code injection."
            guide["recommendation"] = "Exchange data parameters using secure JSON formats or configure deserialization class-validation filters."
            if language == "python":
                guide["corrected_code"] = "import json\ndata = json.loads(user_json)"
            else:
                guide["corrected_code"] = "// Configure safer ObjectInputStream filters or parse inputs using Jackson ObjectMapper"

        # 10. SSRF (SEC-010)
        elif vuln_id == "SEC-010":
            guide["explanation"] = "Opening HTTP connections to variable input domains lets attackers scan local virtual interfaces or cloud metadata nodes."
            guide["recommendation"] = "Verify request URLs match an authorized domain whitelist and reject internal IP blocks."
            if language == "python":
                guide["corrected_code"] = "if target_host in ALLOWED_DOMAINS:\n    requests.get(target_url)"
            else:
                guide["corrected_code"] = "if (ALLOWED_DOMAINS.contains(targetHost)) {\n    new URL(targetUrl).openStream();\n}"

        else:
            guide["explanation"] = "Potential vulnerability found by static audit agent."
            guide["recommendation"] = "Apply standard coding standards to secure input validations."
            guide["corrected_code"] = "# Restrict input structures"

        guide["code_comparison"]["after"] = guide["corrected_code"]
        remediations.append(guide)

    return {"remediations": remediations}
