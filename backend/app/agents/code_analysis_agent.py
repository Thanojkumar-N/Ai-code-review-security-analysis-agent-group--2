import ast
import re
from backend.app.agents.state import AgentState

def analyze_python_ast(code: str) -> list:
    """Analyze Python code using AST to identify unused variables, dead code, nesting, magic numbers, poor naming, complexity, SOLID principles, and best practices."""
    findings = []
    lines = code.split("\n")
    total_lines = len(lines)

    try:
        tree = ast.parse(code)
    except Exception as e:
        return [{
            "id": "QLY-ERR",
            "title": "Python AST Parser Failure",
            "description": f"The Python code has syntax errors and could not be parsed for quality analysis: {str(e)}",
            "language": "python",
            "severity": "High",
            "category": "Coding Best Practice",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "The file contains syntactic errors that prevent Python's built-in AST compiler from building the parse tree.",
            "recommendation": "Resolve the syntax error in the python file."
        }]

    # Helper function to get node code lines
    def get_snippet(node) -> str:
        try:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            return "\n".join(lines[start:end]).strip()
        except Exception:
            return ""

    # Populate parent pointers
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent

    # 1. Duplicate Code Check
    clean_lines = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("'''") and not stripped.startswith('"""'):
            clean_lines.append((idx + 1, stripped))
    
    duplicates = set()
    for i in range(len(clean_lines) - 2):
        seq = (clean_lines[i][1], clean_lines[i+1][1], clean_lines[i+2][1])
        for j in range(i + 3, len(clean_lines) - 2):
            other_seq = (clean_lines[j][1], clean_lines[j+1][1], clean_lines[j+2][1])
            if seq == other_seq:
                duplicates.add((clean_lines[i][0], clean_lines[j][0]))
                
    for line_a, line_b in sorted(duplicates)[:5]:
        findings.append({
            "id": "QLY-015",
            "title": "Duplicate Code Block",
            "description": f"Identical sequence of statements found starting at line {line_a} and line {line_b}.",
            "language": "python",
            "severity": "Medium",
            "category": "Code Smell",
            "line_number": line_a,
            "line": line_a,
            "code_snippet": "\n".join(lines[line_a - 1 : line_a + 2]),
            "snippet": "\n".join(lines[line_a - 1 : line_a + 2]),
            "explanation": "Identical lines of code duplicated across different parts of the file violate the DRY (Don't Repeat Yourself) principle, increasing maintenance overhead.",
            "recommendation": "Extract the common statements into a single helper function or method and call it from both locations."
        })

    # 2. Excessive Comments Ratio
    comment_lines = 0
    in_block_comment = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("'''") or stripped.startswith('"""'):
            comment_lines += 1
            if stripped.count("'''") == 1 or stripped.count('"""') == 1:
                in_block_comment = not in_block_comment
            continue
        if in_block_comment:
            comment_lines += 1
            if "'''" in stripped or '"""' in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("#"):
            comment_lines += 1
            
    comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
    if comment_ratio > 0.3:
        findings.append({
            "id": "QLY-012",
            "title": "Excessive Comments Ratio",
            "description": f"Comments represent {comment_ratio:.1%} of the code base, which exceeds the recommended 30% ratio.",
            "language": "python",
            "severity": "Low",
            "category": "Code Smell",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "While documentation is key, excessively high comment density typically signals complex, confusing code that requires narratives to be understood, or large segments of dead commented-out code.",
            "recommendation": "Refactor the logic to make it self-documenting through clean variable and function names, and remove commented-out code segments."
        })

    # 3. Cyclomatic Complexity
    decision_points = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.And, ast.Or, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            decision_points += 1
    cyclomatic = decision_points + 1
    if cyclomatic > 10:
        findings.append({
            "id": "QLY-COMP-001",
            "title": "High Cyclomatic Complexity",
            "description": f"File has a cyclomatic complexity score of {cyclomatic}, exceeding the recommended limit of 10.",
            "language": "python",
            "severity": "Medium",
            "category": "Complexity",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": f"The complexity score of {cyclomatic} indicates many conditional execution paths, which makes testing and debugging more challenging.",
            "recommendation": "Simplify complex conditionals and extract control branches into smaller, dedicated sub-functions."
        })

    # 4. Tight Coupling: imports list
    unique_imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                unique_imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                unique_imports.add(node.module.split(".")[0])
    if len(unique_imports) > 10:
        findings.append({
            "id": "QLY-DSGN-002",
            "title": "Tight Coupling - High Import Count",
            "description": f"The file imports {len(unique_imports)} external modules/packages.",
            "language": "python",
            "severity": "Medium",
            "category": "Design Problem",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "A high number of unique imports suggests high coupling. This class depends on many packages, making it fragile to downstream API changes.",
            "recommendation": "Partition this module or group functionalities under separate namespaces to reduce import dependencies."
        })

    # Scope and flow rules
    for node in ast.walk(tree):
        # A. Method-level Scans
        if isinstance(node, ast.FunctionDef):
            # i. Long Method (> 50 lines)
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            method_len = end_line - start_line + 1
            if method_len > 50:
                findings.append({
                    "id": "QLY-001",
                    "title": "Long Method Smell",
                    "description": f"Method '{node.name}' is too long ({method_len} lines). It should be refactored into smaller, single-purpose functions.",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Code Smell",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": get_snippet(node)[:150] + "...",
                    "snippet": get_snippet(node)[:150] + "...",
                    "explanation": f"Method '{node.name}' spans {method_len} lines. Extremely long methods suffer from low cohesion and are difficult to read and unit test.",
                    "recommendation": "Extract logical sub-steps of the method body into smaller functions."
                })

            # ii. Long Parameter List (> 4 parameters)
            param_count = len(node.args.args)
            if hasattr(node.args, 'posonlyargs'):
                param_count += len(node.args.posonlyargs)
            if hasattr(node.args, 'kwonlyargs'):
                param_count += len(node.args.kwonlyargs)
            if param_count > 4:
                findings.append({
                    "id": "QLY-002",
                    "title": "Too Many Method Parameters",
                    "description": f"Method '{node.name}' accepts {param_count} parameters (limit is 4).",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Code Smell",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": f"def {node.name}({', '.join(a.arg for a in node.args.args)}):",
                    "snippet": f"def {node.name}({', '.join(a.arg for a in node.args.args)}):",
                    "explanation": f"A parameter count of {param_count} makes the method signature difficult to understand and increases coupling with caller code.",
                    "recommendation": "Introduce a parameter object/dataclass or extract logical segments of the method."
                })

            # iii. Unused Local Variables Check
            local_assignments = {}
            local_reads = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            local_assignments[target.id] = (target.lineno, get_snippet(child))
                elif isinstance(child, ast.AnnAssign):
                    if isinstance(child.target, ast.Name):
                        local_assignments[child.target.id] = (child.target.lineno, get_snippet(child))
                elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    local_reads.add(child.id)
            
            param_names = {a.arg for a in node.args.args}
            for var_name, (line_num, snippet) in local_assignments.items():
                if var_name not in local_reads and var_name not in param_names and not var_name.startswith("_") and var_name not in ["i", "j", "k"]:
                    findings.append({
                        "id": "QLY-003",
                        "title": "Unused Local Variable",
                        "description": f"Variable '{var_name}' is assigned but never referenced or read.",
                        "language": "python",
                        "severity": "Low",
                        "category": "Code Smell",
                        "line_number": line_num,
                        "line": line_num,
                        "code_snippet": snippet,
                        "snippet": snippet,
                        "explanation": f"Variable '{var_name}' was initialized but is never read or referenced. This clutters scope and is often a symptom of incomplete refactoring.",
                        "recommendation": "Remove the assignment statement or reference the variable."
                    })

            # iv. Cognitive Complexity (Method level)
            cog_score = 0
            def traverse_cog(c_node, nesting=0):
                nonlocal cog_score
                if isinstance(c_node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    cog_score += 1 + nesting
                    new_nest = nesting + 1
                else:
                    new_nest = nesting
                
                if isinstance(c_node, ast.BoolOp):
                    cog_score += len(c_node.values) - 1
                
                for child in ast.iter_child_nodes(c_node):
                    traverse_cog(child, new_nest)
            
            traverse_cog(node)
            if cog_score > 10:
                findings.append({
                    "id": "QLY-COMP-002",
                    "title": "High Cognitive Complexity",
                    "description": f"Method '{node.name}' has cognitive complexity of {cog_score}, exceeding the limit of 10.",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Complexity",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": get_snippet(node)[:150] + "...",
                    "snippet": get_snippet(node)[:150] + "...",
                    "explanation": f"Mentally parsing the nested conditional paths inside '{node.name}' is highly demanding due to its complexity score of {cog_score}.",
                    "recommendation": "Reduce nested structures by returning early using guard clauses, or dividing logic into helper methods."
                })

            # v. Feature Envy Check
            external_accesses = {}
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                    obj_id = child.value.id
                    if obj_id != "self":
                        external_accesses[obj_id] = external_accesses.get(obj_id, 0) + 1
            for obj_id, count in external_accesses.items():
                if count > 4:
                    findings.append({
                        "id": "QLY-DSGN-005",
                        "title": "Feature Envy Smell",
                        "description": f"Method '{node.name}' accesses the attributes of external object '{obj_id}' {count} times.",
                        "language": "python",
                        "severity": "Medium",
                        "category": "Design Problem",
                        "line_number": start_line,
                        "line": start_line,
                        "code_snippet": get_snippet(node)[:150],
                        "snippet": get_snippet(node)[:150],
                        "explanation": f"The method '{node.name}' interacts with object '{obj_id}' more than its local scope, indicating low cohesion with its current class.",
                        "recommendation": "Move this method or parts of its logic into the class defining '{obj_id}'."
                    })

            # vi. SOLID OCP Check: isinstance chain
            isinstance_calls = 0
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "isinstance":
                    isinstance_calls += 1
            if isinstance_calls >= 3:
                findings.append({
                    "id": "QLY-DSGN-001",
                    "title": "SOLID - Open-Closed Principle Violation",
                    "description": f"Method '{node.name}' uses {isinstance_calls} isinstance type checks.",
                    "language": "python",
                    "severity": "High",
                    "category": "Design Problem",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": get_snippet(node)[:150],
                    "snippet": get_snippet(node)[:150],
                    "explanation": "Type checks using isinstance block code from being open to extension. Use polymorphism rather than switching on object types.",
                    "recommendation": "Replace type conditions with dynamic polymorphic method calls on target classes."
                })

            # vii. SOLID LSP/ISP Check: unimplemented raise
            has_nie = False
            for child in ast.walk(node):
                if isinstance(child, ast.Raise) and isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name) and child.exc.func.id == "NotImplementedError":
                    has_nie = True
            is_abstract = any(
                isinstance(d, ast.Name) and d.id == "abstractmethod" or 
                isinstance(d, ast.Attribute) and d.attr == "abstractmethod"
                for d in node.decorator_list
            )
            if has_nie and not is_abstract:
                findings.append({
                    "id": "QLY-DSGN-001",
                    "title": "SOLID - Liskov Substitution Principle Violation",
                    "description": f"Method '{node.name}' throws NotImplementedError directly in non-abstract scope.",
                    "language": "python",
                    "severity": "High",
                    "category": "Design Problem",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": get_snippet(node)[:100],
                    "snippet": get_snippet(node)[:100],
                    "explanation": "Throwing NotImplementedError inside concretely defined method blocks forces classes inheriting them to break LSP, because they cannot substitute parent objects safely.",
                    "recommendation": "Refactor interface hierarchies, using Abstract classes, or omit unused method requirements entirely."
                })

            # viii. Missing Documentation - Function
            if node.name not in ["__init__", "__str__", "__repr__"]:
                doc = ast.get_docstring(node)
                if not doc:
                    findings.append({
                        "id": "QLY-BP-001",
                        "title": "Missing Documentation",
                        "description": f"Missing docstring in function '{node.name}'.",
                        "language": "python",
                        "severity": "Low",
                        "category": "Coding Best Practice",
                        "line_number": start_line,
                        "line": start_line,
                        "code_snippet": f"def {node.name}(...):",
                        "snippet": f"def {node.name}(...):",
                        "explanation": "Missing function documentation reduces codebase maintainability.",
                        "recommendation": "Add a structured Python docstring to the top of the function block."
                    })

            # ix. Missing Type Hints
            if node.name not in ["__init__", "__str__", "__repr__"]:
                missing_annotation = False
                for arg in node.args.args:
                    if arg.arg != "self" and not arg.annotation:
                        missing_annotation = True
                if not node.returns:
                    missing_annotation = True
                if missing_annotation:
                    findings.append({
                        "id": "QLY-BP-002",
                        "title": "Missing Type Hints",
                        "description": f"Function '{node.name}' lacks parameter or return type annotations.",
                        "language": "python",
                        "severity": "Low",
                        "category": "Coding Best Practice",
                        "line_number": start_line,
                        "line": start_line,
                        "code_snippet": f"def {node.name}(...):",
                        "snippet": f"def {node.name}(...):",
                        "explanation": "Python type hints enable static type verification and help developers understand argument scopes without reading function body logic.",
                        "recommendation": "Add argument type declarations (e.g. arg: int) and return type declarations (e.g. -> bool) to method signature."
                    })

        # B. Class-level Scans
        elif isinstance(node, ast.ClassDef):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            class_len = end_line - start_line + 1
            methods_in_class = [n for n in node.body if isinstance(n, ast.FunctionDef)]
            
            # i. Large Classes Check (> 150 lines or > 10 methods)
            if class_len > 150 or len(methods_in_class) > 10:
                findings.append({
                    "id": "QLY-004",
                    "title": "Large Class Smell",
                    "description": f"Class '{node.name}' has {class_len} lines and {len(methods_in_class)} methods.",
                    "language": "python",
                    "severity": "High",
                    "category": "Code Smell",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": f"class {node.name}:",
                    "snippet": f"class {node.name}:",
                    "explanation": f"Class '{node.name}' exceeds the limits of 150 lines or 10 methods. This signals a Single Responsibility Principle (SRP) violation.",
                    "recommendation": "Decompose this large class into cohesive sub-classes or classes."
                })

            # ii. Cohesion (LCOM check approximation)
            if len(methods_in_class) >= 3:
                method_attrs = {}
                for m in methods_in_class:
                    if m.name == "__init__":
                        continue
                    attrs = set()
                    for child in ast.walk(m):
                        if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name) and child.value.id == "self":
                            attrs.add(child.attr)
                    method_attrs[m.name] = attrs
                all_attrs = set().union(*method_attrs.values())
                if all_attrs:
                    pairs_sharing = 0
                    total_pairs = 0
                    m_names = list(method_attrs.keys())
                    for i in range(len(m_names)):
                        for j in range(i + 1, len(m_names)):
                            total_pairs += 1
                            if method_attrs[m_names[i]].intersection(method_attrs[m_names[j]]):
                                pairs_sharing += 1
                    share_ratio = pairs_sharing / total_pairs if total_pairs > 0 else 1
                    if share_ratio < 0.2:
                        findings.append({
                            "id": "QLY-DSGN-003",
                            "title": "Low Class Cohesion",
                            "description": f"Class '{node.name}' methods share few instance fields ({share_ratio:.1%} overlap).",
                            "language": "python",
                            "severity": "Medium",
                            "category": "Design Problem",
                            "line_number": start_line,
                            "line": start_line,
                            "code_snippet": f"class {node.name}:",
                            "snippet": f"class {node.name}:",
                            "explanation": "Methods within the class operate independently, indicating class is doing too many unrelated tasks.",
                            "recommendation": "Split class into smaller components where attributes and methods share unified scopes."
                        })

            # iii. God Object
            class_complexity = sum(
                1 for child in ast.walk(node)
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.And, ast.Or))
            )
            if class_len > 250 and class_complexity > 20:
                findings.append({
                    "id": "QLY-DSGN-004",
                    "title": "God Object Violation",
                    "description": f"Class '{node.name}' acts as a God Object ({class_len} lines, complexity {class_complexity}).",
                    "language": "python",
                    "severity": "Critical",
                    "category": "Design Problem",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": f"class {node.name}:",
                    "snippet": f"class {node.name}:",
                    "explanation": "A God Object is an object that controls too many aspects of the application, concentrating logic into a single monolithic class.",
                    "recommendation": "Refactor the class to distribute tasks to other auxiliary objects."
                })

            # iv. Class Documentation
            doc = ast.get_docstring(node)
            if not doc:
                findings.append({
                    "id": "QLY-BP-001",
                    "title": "Missing Documentation",
                    "description": f"Class '{node.name}' lacks docstring documentation.",
                    "language": "python",
                    "severity": "Low",
                    "category": "Coding Best Practice",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": f"class {node.name}:",
                    "snippet": f"class {node.name}:",
                    "explanation": "Documentation of classes is critical to communicate class role and properties to other developers.",
                    "recommendation": "Add a descriptive docstring explaining class behaviors at the top of class declaration."
                })

            # v. Class Naming
            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                findings.append({
                    "id": "QLY-009",
                    "title": "Incorrect Naming Convention",
                    "description": f"Class '{node.name}' is not in PascalCase.",
                    "language": "python",
                    "severity": "Low",
                    "category": "Coding Best Practice",
                    "line_number": start_line,
                    "line": start_line,
                    "code_snippet": f"class {node.name}:",
                    "snippet": f"class {node.name}:",
                    "explanation": "Python conventions (PEP 8) require that classes use PascalCase formatting (words combined without underscores, first letter capitalized).",
                    "recommendation": f"Rename the class using PascalCase."
                })

    # 4. Dead Code (unreachable statements)
    for node in ast.walk(tree):
        if hasattr(node, "body") and isinstance(node.body, list):
            found_terminator = False
            for child in node.body:
                if found_terminator:
                    findings.append({
                        "id": "QLY-005",
                        "title": "Unreachable Dead Code",
                        "description": "Detected statement instructions immediately following a return, break, or raise terminator.",
                        "language": "python",
                        "severity": "High",
                        "category": "Code Smell",
                        "line_number": child.lineno,
                        "line": child.lineno,
                        "code_snippet": get_snippet(child),
                        "snippet": get_snippet(child),
                        "explanation": "Detected statement instructions immediately following a return, break, or raise terminator. This code is dead and can never be reached.",
                        "recommendation": "Remove this unreachable statement block."
                    })
                    break
                if isinstance(child, (ast.Return, ast.Break, ast.Continue, ast.Raise)):
                    found_terminator = True

    # 5. Nested Loops and Nesting depth
    def check_nesting(node, current_depth=0, in_loop=False, in_cond=False):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            current_depth += 1
            if current_depth > 3:
                findings.append({
                    "id": "QLY-006",
                    "title": "Deeply Nested Control Flow Blocks",
                    "description": f"Detected nesting depth of {current_depth} levels (limit is 3).",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Code Smell",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": get_snippet(node)[:100] + "...",
                    "snippet": get_snippet(node)[:100] + "...",
                    "explanation": "Highly nested code makes parsing execution logic difficult and prone to errors.",
                    "recommendation": "Refactor nesting layers by writing separate functions or combining logical terms."
                })

            if isinstance(node, (ast.For, ast.While)):
                if in_loop:
                    findings.append({
                        "id": "QLY-COMP-003",
                        "title": "Nested Loop Complexity",
                        "description": "Loop nested inside another loop.",
                        "language": "python",
                        "severity": "Medium",
                        "category": "Complexity",
                        "line_number": node.lineno,
                        "line": node.lineno,
                        "code_snippet": get_snippet(node)[:100],
                        "snippet": get_snippet(node)[:100],
                        "explanation": "Nested loops increase worst-case runtime complexity (e.g. O(N^2)) and make tracking indices error-prone.",
                        "recommendation": "Extract inner loop logic, or replace loop matching with dict/set lookups."
                    })
                in_loop = True

            if isinstance(node, ast.If):
                if in_cond:
                    findings.append({
                        "id": "QLY-COMP-004",
                        "title": "Nested Conditions Complexity",
                        "description": "Conditional statement is nested inside another conditional branch.",
                        "language": "python",
                        "severity": "Medium",
                        "category": "Complexity",
                        "line_number": node.lineno,
                        "line": node.lineno,
                        "code_snippet": get_snippet(node)[:100],
                        "snippet": get_snippet(node)[:100],
                        "explanation": "Nested conditions decrease cognitive readability and should be combined using boolean operations.",
                        "recommendation": "Use guard clauses (return early) or flatten logic using 'and' / 'or'."
                    })
                in_cond = True

        for child in ast.iter_child_nodes(node):
            check_nesting(child, current_depth, in_loop, in_cond)

    check_nesting(tree)

    # 6. Constants, variables, Exception check
    for node in ast.walk(tree):
        # A. Magic Numbers
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            val = node.value
            if val not in [-1, 0, 1, 2]:
                parent = getattr(node, "parent", None)
                is_const_declaration = False
                if isinstance(parent, ast.Assign):
                    for t in parent.targets:
                        if isinstance(t, ast.Name) and t.id.isupper():
                            is_const_declaration = True
                if not is_const_declaration:
                    findings.append({
                        "id": "QLY-007",
                        "title": "Magic Numbers Smell",
                        "description": f"The literal numeric value '{val}' is used directly in expressions. Define it as a descriptive constant instead.",
                        "language": "python",
                        "severity": "Low",
                        "category": "Code Smell",
                        "line_number": node.lineno,
                        "line": node.lineno,
                        "code_snippet": get_snippet(node) or str(val),
                        "snippet": get_snippet(node) or str(val),
                        "explanation": f"Hardcoding literal '{val}' inside logic leaves developers guessing its significance and makes configuration changes hard.",
                        "recommendation": "Declare a descriptive variable or class constant to label this literal."
                    })

        # B. Name validation
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name = node.id
            parent_func = None
            curr = node
            while hasattr(curr, "parent"):
                curr = curr.parent
                if isinstance(curr, ast.FunctionDef):
                    parent_func = curr
                    break
            
            # Short names
            if len(name) <= 2 and name not in ["i", "j", "k", "x", "y", "z", "_"]:
                findings.append({
                    "id": "QLY-008",
                    "title": "Poor Naming Style (Short Variable)",
                    "description": f"Variable name '{name}' is too short (length under 3 characters).",
                    "language": "python",
                    "severity": "Low",
                    "category": "Code Smell",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": f"{name} = ...",
                    "snippet": f"{name} = ...",
                    "explanation": "Variables with very short names (1-2 characters) do not explain their value, making logic difficult to digest.",
                    "recommendation": "Replace short names with descriptive labels."
                })
            
            # snake_case variables in functions
            if parent_func and not re.match(r"^[a-z_][a-z0-9_]*$", name) and not name.isupper():
                findings.append({
                    "id": "QLY-009",
                    "title": "Naming Convention Violation",
                    "description": f"Python variable '{name}' is not in snake_case naming style.",
                    "language": "python",
                    "severity": "Low",
                    "category": "Coding Best Practice",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": f"{name} = ...",
                    "snippet": f"{name} = ...",
                    "explanation": "Variables declared inside function scope should follow standard snake_case styling.",
                    "recommendation": "Rename the variable using lowercase letters and underscores."
                })

        # C. Empty Except Block
        elif isinstance(node, ast.ExceptHandler):
            is_empty = False
            if len(node.body) == 1:
                child = node.body[0]
                if isinstance(child, ast.Pass):
                    is_empty = True
                elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                    is_empty = True
            if is_empty:
                findings.append({
                    "id": "QLY-010",
                    "title": "Empty Except Block (Exception Swallowing)",
                    "description": "Detected an empty except handler block catching all exceptions with a 'pass' statement.",
                    "language": "python",
                    "severity": "High",
                    "category": "Code Smell",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": "except:\n    pass",
                    "snippet": "except:\n    pass",
                    "explanation": "Silently passing exceptions hides runtime failures, making operations unstable and hard to troubleshoot.",
                    "recommendation": "Add exception logging or raise the caught error."
                })

            # Broad Except Handling
            is_broad = False
            if node.type is None:
                is_broad = True
            elif isinstance(node.type, ast.Name) and node.type.id in ["Exception", "BaseException"]:
                is_broad = True
            if is_broad:
                findings.append({
                    "id": "QLY-013",
                    "title": "Broad Exception Handling",
                    "description": "Broad exception class Exception/BaseException is caught.",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Code Smell",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": get_snippet(node)[:100],
                    "snippet": get_snippet(node)[:100],
                    "explanation": "Broad catch statements mask all unexpected errors. Catch specific exceptions instead.",
                    "recommendation": "Replace generic Exception catches with precise class names like KeyError, ValueError."
                })

        # D. Generic Raise Check
        elif isinstance(node, ast.Raise):
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name) and node.exc.func.id in ["Exception", "BaseException"]:
                findings.append({
                    "id": "QLY-014",
                    "title": "Improper Exception Handling",
                    "description": "Raising generic Exception class directly.",
                    "language": "python",
                    "severity": "Medium",
                    "category": "Coding Best Practice",
                    "line_number": node.lineno,
                    "line": node.lineno,
                    "code_snippet": get_snippet(node),
                    "snippet": get_snippet(node),
                    "explanation": "Throwing base Exception prevents callers from defining specific catch blocks, leading to fragile architectures.",
                    "recommendation": "Throw subclassed custom Exceptions or specific built-in Exceptions (e.g. ValueError)."
                })

    return findings

def analyze_java_lexical(code: str) -> list:
    """Scan Java code blocks structurally and lexically to identify nesting, complexity, SOLID violations, and coding standard smells."""
    findings = []
    lines = code.split("\n")
    total_lines = len(lines)
    
    # 1. Comment ratio scan
    comment_lines = 0
    in_block = False
    clean_lines = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        line_num = idx + 1
        if "/*" in stripped:
            comment_lines += 1
            if "*/" not in stripped:
                in_block = True
            continue
        if "*/" in stripped:
            comment_lines += 1
            in_block = False
            continue
        if in_block or stripped.startswith("//") or stripped.startswith("*"):
            comment_lines += 1
            continue
        if stripped:
            clean_lines.append((line_num, stripped))
            
    comment_ratio = comment_lines / total_lines if total_lines > 0 else 0
    if comment_ratio > 0.3:
        findings.append({
            "id": "QLY-012",
            "title": "Excessive Comments Ratio",
            "description": f"Comments cover {comment_ratio:.1%} of Java file lines (limit is 30%).",
            "language": "java",
            "severity": "Low",
            "category": "Code Smell",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "High comment counts suggest code is overly complex or contains massive unused chunks of commented out code.",
            "recommendation": "Remove commented-out statements and simplify structure so code is self-documenting."
        })

    # 2. Duplicate code check (3 consecutive clean lines)
    duplicates = set()
    for i in range(len(clean_lines) - 2):
        seq = (clean_lines[i][1], clean_lines[i+1][1], clean_lines[i+2][1])
        for j in range(i + 3, len(clean_lines) - 2):
            other_seq = (clean_lines[j][1], clean_lines[j+1][1], clean_lines[j+2][1])
            if seq == other_seq:
                duplicates.add((clean_lines[i][0], clean_lines[j][0]))
                
    for line_a, line_b in sorted(duplicates)[:5]:
        findings.append({
            "id": "QLY-015",
            "title": "Duplicate Code Block",
            "description": f"Identical logic duplicate sequences starting at line {line_a} and line {line_b}.",
            "language": "java",
            "severity": "Medium",
            "category": "Code Smell",
            "line_number": line_a,
            "line": line_a,
            "code_snippet": "\n".join(lines[line_a - 1 : line_a + 2]),
            "snippet": "\n".join(lines[line_a - 1 : line_a + 2]),
            "explanation": "Java code duplication is a violation of Dry code guidelines, multiplying bug fixing efforts.",
            "recommendation": "Extract common logic into separate helper methods."
        })

    # 3. Cyclomatic Complexity approximation
    cyclomatic_points = 0
    for line_num, line in clean_lines:
        cyclomatic_points += sum(1 for kw in ["if ", "if(", "for ", "for(", "while ", "while(", "catch ", "catch(", "&&", "||", "case ", " ? "] if kw in line)
    cyclomatic_score = cyclomatic_points + 1
    if cyclomatic_score > 10:
        findings.append({
            "id": "QLY-COMP-001",
            "title": "High Cyclomatic Complexity",
            "description": f"Java complexity score is {cyclomatic_score} (exceeds recommended threshold of 10).",
            "language": "java",
            "severity": "Medium",
            "category": "Complexity",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "Having many execution branches raises the likelihood of testing escapes and bugs.",
            "recommendation": "Reduce nested structures and distribute flow paths into independent methods."
        })

    # 4. Imports and Coupling Check
    imports_list = []
    for line_num, line in clean_lines:
        if line.startswith("import "):
            parts = line.split()
            if len(parts) >= 2:
                imports_list.append((line_num, parts[1].replace(";", "")))
    if len(imports_list) > 10:
        findings.append({
            "id": "QLY-DSGN-002",
            "title": "Tight Coupling - High Import Count",
            "description": f"Java class depends on {len(imports_list)} external package imports.",
            "language": "java",
            "severity": "Medium",
            "category": "Design Problem",
            "line_number": 1,
            "line": 1,
            "code_snippet": "",
            "snippet": "",
            "explanation": "Importing a high volume of dependencies increases coupling and complicates dependency management.",
            "recommendation": "Separate core functionalities into secondary classes to limit dependencies."
        })

    # Structure Parser (Extract classes and methods)
    class_ranges = []
    method_ranges = []
    
    bracket_stack = []
    current_class = None
    current_method = None
    
    # Simple parse to trace method brackets
    for line_num, line in clean_lines:
        # Match class declaration
        class_match = re.search(r"\b(?:class|interface|enum)\s+(\w+)", line)
        if class_match and not line.endswith(";"):
            current_class = {
                "name": class_match.group(1),
                "start": line_num,
                "end": None,
                "methods": []
            }
            class_ranges.append(current_class)

        # Match method declaration (avoid loops/control flows)
        if ("public" in line or "private" in line or "protected" in line or "static" in line) and "(" in line and ")" in line and not line.endswith(";") and not "class" in line:
            # Extract method name
            method_match = re.search(r"(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{", line)
            if method_match:
                m_name = method_match.group(1)
                current_method = {
                    "name": m_name,
                    "start": line_num,
                    "end": None,
                    "class": current_class["name"] if current_class else None
                }
                method_ranges.append(current_method)
                if current_class:
                    current_class["methods"].append(current_method)

        for char in line:
            if char == "{":
                bracket_stack.append(line_num)
            elif char == "}":
                if bracket_stack:
                    start_pos = bracket_stack.pop()
                    # Check matching method
                    if current_method and current_method["start"] == start_pos:
                        current_method["end"] = line_num
                        current_method = None
                    # Check matching class
                    if current_class and current_class["start"] == start_pos:
                        current_class["end"] = line_num
                        current_class = None

    # Analyze extracted components
    # A. Class Checks
    for cls in class_ranges:
        class_start = cls["start"]
        class_end = cls["end"] or total_lines
        class_len = class_end - class_start + 1
        num_methods = len(cls["methods"])
        
        # i. Large Class check
        if class_len > 150 or num_methods > 10:
            findings.append({
                "id": "QLY-004",
                "title": "Large Class Smell",
                "description": f"Class '{cls['name']}' has {class_len} lines and {num_methods} methods.",
                "language": "java",
                "severity": "High",
                "category": "Code Smell",
                "line_number": class_start,
                "line": class_start,
                "code_snippet": lines[class_start - 1],
                "snippet": lines[class_start - 1],
                "explanation": f"The class '{cls['name']}' handles too many tasks, raising lines count to {class_len}. This violates Single Responsibility limits.",
                "recommendation": "Split this class responsibilities into multiple cohesive helper classes."
            })

        # ii. PascalCase check
        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", cls["name"]):
            findings.append({
                "id": "QLY-009",
                "title": "Incorrect Naming Convention",
                "description": f"Java class name '{cls['name']}' should follow PascalCase convention.",
                "language": "java",
                "severity": "Low",
                "category": "Coding Best Practice",
                "line_number": class_start,
                "line": class_start,
                "code_snippet": lines[class_start - 1],
                "snippet": lines[class_start - 1],
                "explanation": "Standard Java styling requires classes, interfaces, and enums to be in PascalCase.",
                "recommendation": f"Rename '{cls['name']}' to capitalize the starting letter."
            })

        # iii. God Object Check
        if class_len > 250 and num_methods > 10:
            findings.append({
                "id": "QLY-DSGN-004",
                "title": "God Object Violation",
                "description": f"Java class '{cls['name']}' is a God Object ({class_len} lines, {num_methods} methods).",
                "language": "java",
                "severity": "Critical",
                "category": "Design Problem",
                "line_number": class_start,
                "line": class_start,
                "code_snippet": lines[class_start - 1],
                "snippet": lines[class_start - 1],
                "explanation": "God classes orchestrate too many functionalities and fields, making the application tightly coupled and rigid.",
                "recommendation": "Delegate parts of class responsibilities to subclass services."
            })

        # iv. Missing JavaDoc
        has_doc = False
        scan_idx = class_start - 2
        while scan_idx >= 0:
            prev_line = lines[scan_idx].strip()
            if prev_line.endswith("*/"):
                if "/**" in lines[max(0, scan_idx - 5) : scan_idx + 1]:
                    has_doc = True
                break
            if not prev_line or prev_line.startswith("@"):
                scan_idx -= 1
                continue
            break
        if not has_doc:
            findings.append({
                "id": "QLY-BP-003",
                "title": "Missing JavaDoc",
                "description": f"Class '{cls['name']}' lacks class-level Javadoc comments.",
                "language": "java",
                "severity": "Low",
                "category": "Coding Best Practice",
                "line_number": class_start,
                "line": class_start,
                "code_snippet": lines[class_start - 1],
                "snippet": lines[class_start - 1],
                "explanation": "Failing to document public classes limits API onboarding and general comprehension.",
                "recommendation": "Add a JavaDoc comment starting with /** above the class definition."
            })

    # B. Method Checks
    for m in method_ranges:
        m_start = m["start"]
        m_end = m["end"] or total_lines
        m_len = m_end - m_start + 1
        m_name = m["name"]
        
        # i. Long Method check
        if m_len > 50:
            findings.append({
                "id": "QLY-001",
                "title": "Long Method Smell",
                "description": f"Method '{m_name}' has {m_len} lines, exceeding the recommended limit of 50 lines.",
                "language": "java",
                "severity": "Medium",
                "category": "Code Smell",
                "line_number": m_start,
                "line": m_start,
                "code_snippet": lines[m_start - 1],
                "snippet": lines[m_start - 1],
                "explanation": "Long method blocks perform too many internal tasks, reducing maintainability.",
                "recommendation": "Split method logic into smaller sub-methods."
            })

        # ii. camelCase method naming
        if not re.match(r"^[a-z][a-zA-Z0-9]*$", m_name) and m_name not in ["main"]:
            findings.append({
                "id": "QLY-009",
                "title": "Incorrect Naming Convention",
                "description": f"Java method '{m_name}' should follow camelCase convention.",
                "language": "java",
                "severity": "Low",
                "category": "Coding Best Practice",
                "line_number": m_start,
                "line": m_start,
                "code_snippet": lines[m_start - 1],
                "snippet": lines[m_start - 1],
                "explanation": "Java specifications advise using camelCase starting with a lowercase character for methods.",
                "recommendation": f"Rename '{m_name}' to start with a lowercase letter."
            })

        # iii. Long parameter list (> 4 params)
        sig_line = lines[m_start - 1]
        param_section = sig_line.split("(")[1].split(")")[0] if "(" in sig_line and ")" in sig_line else ""
        params = [p.strip() for p in param_section.split(",") if p.strip()]
        if len(params) > 4:
            findings.append({
                "id": "QLY-002",
                "title": "Too Many Method Parameters",
                "description": f"Method '{m_name}' accepts {len(params)} parameters (limit is 4).",
                "language": "java",
                "severity": "Medium",
                "category": "Code Smell",
                "line_number": m_start,
                "line": m_start,
                "code_snippet": sig_line.strip(),
                "snippet": sig_line.strip(),
                "explanation": "Accepting many arguments increases interface coupling and complicates calls.",
                "recommendation": "Introduce a parameter wrapper class or separate interface scopes."
            })

        # iv. Feature Envy / instance variables check
        envy_count = 0
        for idx in range(m_start, m_end):
            l_text = lines[idx]
            matches = re.findall(r"\b([a-zA-Z_]\w*)\.[a-zA-Z_]\w*\(", l_text)
            for m_obj in matches:
                if m_obj not in ["System", "this", "Math", "Log", "logger"]:
                    envy_count += 1
        if envy_count > 6:
            findings.append({
                "id": "QLY-DSGN-005",
                "title": "Feature Envy Smell",
                "description": f"Method '{m_name}' makes {envy_count} calls to attributes/methods of external objects.",
                "language": "java",
                "severity": "Medium",
                "category": "Design Problem",
                "line_number": m_start,
                "line": m_start,
                "code_snippet": lines[m_start - 1].strip(),
                "snippet": lines[m_start - 1].strip(),
                "explanation": f"Method '{m_name}' calls external interfaces {envy_count} times, indicating high coupling with data inside other classes.",
                "recommendation": "Move this method logic into the class defining the accessed data fields."
            })

        # v. Missing Method JavaDoc
        has_doc = False
        scan_idx = m_start - 2
        while scan_idx >= 0:
            prev_line = lines[scan_idx].strip()
            if prev_line.endswith("*/"):
                if "/**" in lines[max(0, scan_idx - 5) : scan_idx + 1]:
                    has_doc = True
                break
            if not prev_line or prev_line.startswith("@"):
                scan_idx -= 1
                continue
            break
        if not has_doc:
            findings.append({
                "id": "QLY-BP-003",
                "title": "Missing JavaDoc",
                "description": f"Method '{m_name}' lacks Javadoc documentation.",
                "language": "java",
                "severity": "Low",
                "category": "Coding Best Practice",
                "line_number": m_start,
                "line": m_start,
                "code_snippet": sig_line.strip(),
                "snippet": sig_line.strip(),
                "explanation": "Documenting class method contracts simplifies developer integration and API onboarding.",
                "recommendation": "Add a Javadoc block comment starting with /** above the method signature."
            })

    # 5. Core Lexical scans
    nesting_level = 0
    in_method = False
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        stripped = line.strip()
        
        # Skip comment lines
        if not stripped or stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*") or stripped.endswith("*/"):
            continue
            
        # Brace nesting & Nested loop/conditions
        for char in stripped:
            if char == "{":
                nesting_level += 1
                if nesting_level > 3:
                    findings.append({
                        "id": "QLY-006",
                        "title": "Deeply Nested Scopes in Java",
                        "description": f"Java block nesting depth reached {nesting_level} levels (limit is 3).",
                        "language": "java",
                        "severity": "Medium",
                        "category": "Code Smell",
                        "line_number": line_num,
                        "line": line_num,
                        "code_snippet": stripped,
                        "snippet": stripped,
                        "explanation": "Extremely deep brace levels suggests control logic is complex and uncohesive.",
                        "recommendation": "Flatten nested blocks using return-early checks or extracting helper methods."
                    })
            elif char == "}":
                nesting_level = max(0, nesting_level - 1)

        # Magic numbers in expressions
        magic_match = re.search(r"\b([3-9]|[1-9]\d+)(\.\d+)?\b", stripped)
        if magic_match and not any(k in stripped for k in ["final", "static", "import", "package", "version", "L", "@"]):
            val = magic_match.group(0)
            findings.append({
                "id": "QLY-007",
                "title": "Java Magic Numbers Smell",
                "description": f"Literal magic number value '{val}' is used in Java code expression.",
                "language": "java",
                "severity": "Low",
                "category": "Code Smell",
                "line_number": line_num,
                "line": line_num,
                "code_snippet": stripped,
                "snippet": stripped,
                "explanation": f"Numeric constant '{val}' has no label, making maintenance and configuration changes fragile.",
                "recommendation": "Declare a static final constant mapping to the literal numeric value."
            })

        # Naming variables inside methods
        var_match = re.search(r"\b(int|double|float|String|boolean|char|long|byte|short|var|List<[\w_]+>|Map<[\w_,\s]+>)\s+(\w+)\b", stripped)
        if var_match:
            var_name = var_match.group(2)
            if len(var_name) <= 2 and var_name not in ["i", "j", "k", "x", "y", "z"]:
                findings.append({
                    "id": "QLY-008",
                    "title": "Java Poor Naming Style (Short Variable)",
                    "description": f"Java variable name '{var_name}' is too short (under 3 characters).",
                    "language": "java",
                    "severity": "Low",
                    "category": "Code Smell",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Short variables fail to declare their purpose.",
                    "recommendation": "Use descriptive variable names (e.g. counter instead of c)."
                })
            if "_" in var_name and not var_name.isupper():
                findings.append({
                    "id": "QLY-009",
                    "title": "Java Naming Style Violation",
                    "description": f"Java variable '{var_name}' contains underscores.",
                    "language": "java",
                    "severity": "Low",
                    "category": "Coding Best Practice",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Variable naming should be camelCase in Java without using underscores.",
                    "recommendation": "Rename variable to use camelCase styling."
                })

        # Empty Catch Block Check
        if "catch" in stripped and "{" in stripped:
            catch_idx = idx
            catch_body = ""
            braces = 0
            while catch_idx < total_lines:
                curr_line = lines[catch_idx]
                for char in curr_line:
                    if char == "{":
                        braces += 1
                    elif char == "}":
                        braces -= 1
                if braces == 0 and catch_idx > idx:
                    break
                catch_body += curr_line
                catch_idx += 1
            
            inside = catch_body.split("{", 1)[-1].rsplit("}", 1)[0].strip()
            inside_clean = re.sub(r"//.*|/\*.*?\*/", "", inside, flags=re.DOTALL).strip()
            if not inside_clean or inside_clean == ";":
                findings.append({
                    "id": "QLY-010",
                    "title": "Java Empty Catch Block (Exception Swallowing)",
                    "description": "Empty Java catch block detected.",
                    "language": "java",
                    "severity": "High",
                    "category": "Code Smell",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Failing to handle caught errors swallows bugs, making software systems fragile.",
                    "recommendation": "Add logging, or throw exceptions up the stack trace."
                })

            # Broad Catch check
            if "catch" in stripped and ("Exception " in stripped or "Throwable " in stripped or "Exception)" in stripped or "Throwable)" in stripped):
                findings.append({
                    "id": "QLY-013",
                    "title": "Broad Exception Handling",
                    "description": "Broad exception class Exception/Throwable is caught.",
                    "language": "java",
                    "severity": "Medium",
                    "category": "Code Smell",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Generic catch blocks catch System errors that should propagate, masking core faults.",
                    "recommendation": "Catch specific exception subclasses like IOException or SQLException."
                })

        # Throw generic exceptions
        if "throw new " in stripped:
            if "Exception(" in stripped or "Throwable(" in stripped or "RuntimeException(" in stripped or "NullPointerException(" in stripped:
                findings.append({
                    "id": "QLY-014",
                    "title": "Improper Exception Handling",
                    "description": "Throwing generic Exception, Throwable, RuntimeException, or NullPointerException.",
                    "language": "java",
                    "severity": "Medium",
                    "category": "Coding Best Practice",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Throwing raw exceptions reduces API clarity and downstream handling precision.",
                    "recommendation": "Define customized domain exceptions or throw standard specific exceptions (e.g. IllegalArgumentException)."
                })

        # Nested loop scan
        if "for (" in stripped or "for(" in stripped or "while (" in stripped or "while(" in stripped:
            loop_nest = sum(1 for prev_idx in range(max(0, idx - 10), idx) if "for" in lines[prev_idx] or "while" in lines[prev_idx])
            if loop_nest > 0 and nesting_level > 2:
                findings.append({
                    "id": "QLY-COMP-003",
                    "title": "Nested Loop Complexity",
                    "description": "Loop is nested inside another loop context.",
                    "language": "java",
                    "severity": "Medium",
                    "category": "Complexity",
                    "line_number": line_num,
                    "line": line_num,
                    "code_snippet": stripped,
                    "snippet": stripped,
                    "explanation": "Nested loops complicate execution time and index tracking.",
                    "recommendation": "Deconstruct loops or use map/collection search patterns."
                })

        # Nested condition scan
        if "if (" in stripped or "if(" in stripped:
            if nesting_level > 2:
                if_nest = sum(1 for prev_idx in range(max(0, idx - 5), idx) if "if" in lines[prev_idx])
                if if_nest > 0:
                    findings.append({
                        "id": "QLY-COMP-004",
                        "title": "Nested Conditions Complexity",
                        "description": "Nested conditional statement inside another condition block.",
                        "language": "java",
                        "severity": "Medium",
                        "category": "Complexity",
                        "line_number": line_num,
                        "line": line_num,
                        "code_snippet": stripped,
                        "snippet": stripped,
                        "explanation": "Deep conditional nesting makes tracking code paths hard.",
                        "recommendation": "Return early using guards or combine logical clauses."
                    })

    # Unused Imports Java
    for line_num, imp_path in imports_list:
        imp_class = imp_path.split(".")[-1]
        used = False
        for l_num, l_text in clean_lines:
            if l_num != line_num and imp_class in l_text:
                used = True
                break
        if not used:
            findings.append({
                "id": "QLY-011",
                "title": "Unused Import",
                "description": f"Imported Java class '{imp_path}' is never referenced.",
                "language": "java",
                "severity": "Low",
                "category": "Code Smell",
                "line_number": line_num,
                "line": line_num,
                "code_snippet": f"import {imp_path};",
                "snippet": f"import {imp_path};",
                "explanation": "Unused imports clutter dependency scopes.",
                "recommendation": "Remove the unused import statement."
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
