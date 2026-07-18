import ast
import re
from backend.app.agents.state import AgentState

def analyze_python_ast(code: str) -> list:
    """Analyze Python code using AST to identify unused variables, dead code, nesting, magic numbers, poor naming, and SOLID smells."""
    findings = []
    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{
            "id": "QLY-ERR",
            "line": 1,
            "title": "Python AST Parser Failure",
            "severity": "High",
            "category": "Syntax",
            "description": f"The Python code has syntax errors and could not be parsed for quality analysis: {str(e)}",
            "snippet": ""
        }]

    # Helper function to get node code lines
    lines = code.split("\n")
    def get_snippet(node) -> str:
        try:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            return "\n".join(lines[start:end]).strip()
        except Exception:
            return ""

    # 1. Scope-based Checkers (Functions and Classes)
    for node in ast.walk(tree):
        # Functions and Methods Scans
        if isinstance(node, ast.FunctionDef):
            # A. Long Methods Check (> 50 lines)
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            method_len = end_line - start_line + 1
            if method_len > 50:
                findings.append({
                    "id": "QLY-001",
                    "line": start_line,
                    "title": "Long Method Smell",
                    "severity": "Medium",
                    "category": "Design Smells",
                    "description": f"Method '{node.name}' is too long ({method_len} lines). It should be refactored into smaller, single-purpose functions.",
                    "snippet": get_snippet(node)[:150] + "..."
                })

            # B. Too Many Parameters Check (> 4 parameters)
            param_count = len(node.args.args)
            if param_count > 4:
                findings.append({
                    "id": "QLY-002",
                    "line": start_line,
                    "title": "Too Many Method Parameters",
                    "severity": "Medium",
                    "category": "Design Smells",
                    "description": f"Method '{node.name}' accepts {param_count} parameters (limit is 4). High parameter lists couple code classes.",
                    "snippet": f"def {node.name}({', '.join(a.arg for a in node.args.args)}):"
                })

            # C. Unused Local Variables Check
            local_assignments = {}
            local_reads = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            local_assignments[target.id] = target.lineno
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    local_reads.add(child.id)
            
            # Filter variables defined inside parameters
            param_names = {a.arg for a in node.args.args}
            for var_name, line_num in local_assignments.items():
                if var_name not in local_reads and var_name not in param_names and not var_name.startswith("_"):
                    findings.append({
                        "id": "QLY-003",
                        "line": line_num,
                        "title": "Unused Local Variable",
                        "severity": "Low",
                        "category": "Clean Code",
                        "description": f"Variable '{var_name}' is assigned but never referenced or read. Remove it to clean code scope.",
                        "snippet": f"{var_name} = ..."
                    })

        # Classes Scans
        elif isinstance(node, ast.ClassDef):
            # D. Large Classes Check (> 150 lines or > 10 methods)
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            class_len = end_line - start_line + 1
            methods_in_class = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            if class_len > 150 or len(methods_in_class) > 10:
                findings.append({
                    "id": "QLY-004",
                    "line": start_line,
                    "title": "Large Class Violation (SRP)",
                    "severity": "High",
                    "category": "SOLID Violations",
                    "description": f"Class '{node.name}' has {class_len} lines and {len(methods_in_class)} methods. This signals a Single Responsibility Principle (SRP) violation.",
                    "snippet": f"class {node.name}:"
                })

    # 2. Dead Code Check (unreachable block sequences)
    # Check blocks in AST (bodies of FunctionDef, If, For, While, Try)
    for node in ast.walk(tree):
        if hasattr(node, "body") and isinstance(node.body, list):
            found_terminator = False
            for child in node.body:
                if found_terminator:
                    findings.append({
                        "id": "QLY-005",
                        "line": child.lineno,
                        "title": "Unreachable Dead Code",
                        "severity": "Critical",
                        "category": "Clean Code",
                        "description": "Detected statement instructions immediately following a return, break, or raise terminator. This code is dead and can never be reached.",
                        "snippet": get_snippet(child)
                    })
                    break
                if isinstance(child, (ast.Return, ast.Break, ast.Continue, ast.Raise)):
                    found_terminator = True

    # 3. Deep Nesting Check (> 3 levels deep)
    def check_nesting(node, current_depth=0):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            current_depth += 1
            if current_depth > 3:
                findings.append({
                    "id": "QLY-006",
                    "line": node.lineno,
                    "title": "Deeply Nested Control Flow Blocks",
                    "severity": "Medium",
                    "category": "Design Smells",
                    "description": f"Detected nesting depth of {current_depth} levels (limit is 3). Deep nesting makes code hard to read and test.",
                    "snippet": get_snippet(node)[:100] + "..."
                })
        for child in ast.iter_child_nodes(node):
            check_nesting(child, current_depth)

    check_nesting(tree)

    # 4. Magic Numbers & Poor Naming Check
    for node in ast.walk(tree):
        # A. Magic Numbers Check
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            val = node.value
            if val not in [-1, 0, 1, 2]:
                # Check if it is inside an assignment target (which means it's a declared constant, which is fine!)
                # If parent is an Assign node and node is not the target, we check context
                parent = getattr(node, "parent", None)
                # To be simple and robust: flag numbers directly inside BinOp or Compare operations
                findings.append({
                    "id": "QLY-007",
                    "line": node.lineno,
                    "title": "Magic Numbers Smell",
                    "severity": "Low",
                    "category": "Clean Code",
                    "description": f"The literal numeric value '{val}' is used directly in expressions. Define it as a descriptive constant instead.",
                    "snippet": f"... {val} ..."
                })

        # B. Poor Naming Check (variable targets and function declarations)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
            if len(name) <= 2 and name not in ["i", "j", "k", "x", "y", "z", "_"]:
                findings.append({
                    "id": "QLY-008",
                    "line": node.lineno,
                    "title": "Poor Naming Style (Short Variable)",
                    "severity": "Low",
                    "category": "Style",
                    "description": f"Variable name '{name}' is too short (length under 3 characters). Use descriptive variable names.",
                    "snippet": f"{name} = ..."
                })
            elif not re.match(r"^[a-z_][a-z0-9_]*$", name) and not name.isupper():
                findings.append({
                    "id": "QLY-009",
                    "line": node.lineno,
                    "title": "Naming Convention Violation (non-snake_case)",
                    "severity": "Info",
                    "category": "Style",
                    "description": f"Python variable '{name}' is not in snake_case naming style. Standard style guidelines recommend lowercase with underscores.",
                    "snippet": f"{name} = ..."
                })

        # C. Empty Except Block
        elif isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                findings.append({
                    "id": "QLY-010",
                    "line": node.lineno,
                    "title": "Empty Except Block (Exception Swallowing)",
                    "severity": "High",
                    "category": "Design Smells",
                    "description": "Detected an empty except handler block catching all exceptions with a 'pass' statement. This swallows errors and makes debugging hard.",
                    "snippet": "except:\n    pass"
                })

    return findings

def analyze_java_lexical(code: str) -> list:
    """Lexically scan Java code blocks to identify nested loops, naming styles, magic numbers, empty catch blocks, and parameters smells."""
    findings = []
    lines = code.split("\n")
    
    current_nesting = 0
    in_comment = False
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.strip()
        
        # Track block comments
        if "/*" in stripped:
            in_comment = True
        if "*/" in stripped:
            in_comment = False
            continue
        if in_comment or stripped.startswith("//") or not stripped:
            continue

        # 1. Bracket Nesting Checks
        for char in stripped:
            if char == "{":
                current_nesting += 1
                if current_nesting > 3:
                    findings.append({
                        "id": "QLY-006",
                        "line": line_num,
                        "title": "Deeply Nested Scopes in Java",
                        "severity": "Medium",
                        "category": "Design Smells",
                        "description": f"Java block nesting depth reached {current_nesting} levels (limit is 3). Deep nesting suggests high complexity.",
                        "snippet": stripped
                    })
                    break
            elif char == "}":
                current_nesting = max(0, current_nesting - 1)

        # 2. Magic Numbers Check
        # Match literal integers / floats not inside variable declarations containing final or static
        magic_match = re.search(r"\b([3-9]|[1-9]\d+)(\.\d+)?\b", stripped)
        if magic_match and not any(k in stripped for k in ["final", "static", "import", "package", "version", "L"]):
            val = magic_match.group(0)
            findings.append({
                "id": "QLY-007",
                "line": line_num,
                "title": "Java Magic Numbers Smell",
                "severity": "Low",
                "category": "Clean Code",
                "description": f"Literal magic number value '{val}' is used in Java code expression without variable constant declaration.",
                "snippet": stripped
            })

        # 3. Poor Naming & Style
        # Match variable declarations inside methods: "int x = 5;" or "String user_name = ...;"
        var_match = re.search(r"\b(int|double|float|String|boolean|char)\s+(\w+)\b", stripped)
        if var_match:
            var_name = var_match.group(2)
            if len(var_name) <= 2 and var_name not in ["i", "j", "k", "x", "y", "z"]:
                findings.append({
                    "id": "QLY-008",
                    "line": line_num,
                    "title": "Java Poor Naming Style (Short Variable)",
                    "severity": "Low",
                    "category": "Style",
                    "description": f"Java variable name '{var_name}' is too short. Use descriptive variable names.",
                    "snippet": stripped
                })
            # Java variable should be camelCase (no underscores, lower starting letter)
            if "_" in var_name:
                findings.append({
                    "id": "QLY-009",
                    "line": line_num,
                    "title": "Java Naming Style Violation (non-camelCase)",
                    "severity": "Info",
                    "category": "Style",
                    "description": f"Java variable '{var_name}' uses underscores. Standard Java styling conventions recommend camelCase variables.",
                    "snippet": stripped
                })

        # 4. Empty Catch Blocks Check
        if "catch" in stripped and "{" in stripped and "}" in stripped:
            inside_braces = stripped.split("{")[-1].split("}")[0].strip()
            if not inside_braces or inside_braces == ";":
                findings.append({
                    "id": "QLY-010",
                    "line": line_num,
                    "title": "Java Empty Catch Block (Exception Swallowing)",
                    "severity": "High",
                    "category": "Design Smells",
                    "description": "Empty Java catch block detected. Catching exceptions without logging or propagation swallows errors.",
                    "snippet": stripped
                })

        # 5. Method parameter limits (> 4 params)
        if ("public " in stripped or "private " in stripped) and "(" in stripped and ")" in stripped and not ";" in stripped:
            param_section = stripped.split("(")[1].split(")")[0]
            params = [p.strip() for p in param_section.split(",") if p.strip()]
            if len(params) > 4:
                findings.append({
                    "id": "QLY-002",
                    "line": line_num,
                    "title": "Java Method Parameter Limits Breached",
                    "severity": "Medium",
                    "category": "Design Smells",
                    "description": f"Java method declares {len(params)} arguments (limit is 4). High parameters suggest SRP violations.",
                    "snippet": stripped
                })

    return findings

def code_analysis_agent_node(state: AgentState) -> dict:
    """Agent node that inspects source structure, checks complexity, and scans for code quality smells."""
    code = state.get("code", "")
    language = state.get("language", "python").lower()
    
    # 1. Execute language-specific static smells scanners
    if language == "python":
        quality_findings = analyze_python_ast(code)
    elif language == "java":
        quality_findings = analyze_java_lexical(code)
    else:
        quality_findings = []

    lines = code.split("\n")
    lines_count = len(lines)
    
    # 2. Estimate base cyclomatic complexity and counts
    complexity_score = 1
    functions_count = 0
    classes_count = 0
    for line in lines:
        stripped = line.strip().lower()
        if language == "python":
            complexity_score += sum(1 for kwd in ["if ", "for ", "while ", "except ", "and ", "or "] if kwd in stripped)
            if line.strip().startswith("def "):
                functions_count += 1
            elif line.strip().startswith("class "):
                classes_count += 1
        else:
            complexity_score += sum(1 for kwd in ["if (", "for (", "while (", "catch (", "&& ", "|| "] if kwd in stripped)
            stripped_raw = line.strip()
            if "class " in stripped_raw and not stripped_raw.startswith("//"):
                classes_count += 1
            if ("public " in stripped_raw or "private " in stripped_raw) and "(" in stripped_raw and ")" in stripped_raw and not ";" in stripped_raw and not "=" in stripped_raw:
                functions_count += 1

    if complexity_score > 15:
        complexity_rating = "Critical Complexity - Refactor Needed"
    elif complexity_score > 8:
        complexity_rating = "Moderate Complexity"
    else:
        complexity_rating = "Low Complexity (Clean)"

    summary = (
        f"Analyzed {lines_count} lines of {language.capitalize()} code. "
        f"Detected {len(quality_findings)} code quality smells and complexity issues. "
        f"Cyclomatic complexity is rated as: {complexity_rating} (Score: {complexity_score})."
    )

    analysis_report = {
        "lines_count": lines_count,
        "functions_count": functions_count,
        "classes_count": classes_count,
        "complexity_score": complexity_score,
        "complexity_rating": complexity_rating,
        "summary": summary,
        "quality_findings": quality_findings
    }

    return {"code_analysis": analysis_report}
