import ast
import re

def validate_python_syntax(code: str) -> None:
    """Validate Python code syntax by compiling it to Abstract Syntax Tree (AST)."""
    try:
        ast.parse(code)
    except SyntaxError as e:
        # Format a descriptive error specifying line and offset
        error_msg = f"Python Syntax Error: {e.msg} on line {e.lineno}"
        if e.text:
            error_msg += f" near code: '{e.text.strip()}'"
        raise ValueError(error_msg) from e

def validate_java_syntax(code: str, filename_hint: str = None) -> None:
    """Validate Java syntax using bracket balancing, public class layout, and keywords matching."""
    if not code.strip():
        raise ValueError("Java file content is empty")

    # 1. Bracket balancing checks
    brackets_stack = []
    brackets_map = {')': '(', '}': '{', ']': '['}
    line_number = 1
    
    # Track chars to extract line numbers for brace mismatches
    for idx, char in enumerate(code):
        if char == '\n':
            line_number += 1
            
        if char in brackets_map.values():
            brackets_stack.append((char, line_number))
        elif char in brackets_map.keys():
            if not brackets_stack:
                raise ValueError(f"Java Syntax Error: Mismatched closing bracket '{char}' on line {line_number}")
            
            top_char, top_line = brackets_stack.pop()
            if top_char != brackets_map[char]:
                raise ValueError(
                    f"Java Syntax Error: Closing bracket '{char}' on line {line_number} "
                    f"does not match opening bracket '{top_char}' from line {top_line}"
                )

    if brackets_stack:
        unclosed_char, unclosed_line = brackets_stack.pop()
        raise ValueError(f"Java Syntax Error: Unclosed opening bracket '{unclosed_char}' starting on line {unclosed_line}")

    # 2. Key Java keywords checklist
    # Standard Java source files must contain at least basic structural declarations
    required_matches = ["class", "interface", "enum"]
    if not any(req in code for req in required_matches):
        raise ValueError("Java Syntax Error: Missing class, interface, or enum definition")

    # 3. Filename matching check for public classes (if filename_hint is provided)
    if filename_hint and filename_hint.endswith(".java"):
        expected_class = filename_hint.replace(".java", "").strip()
        # Find any public class definition: "public class ClassName"
        public_class_match = re.search(r"public\s+class\s+(\w+)", code)
        if public_class_match:
            declared_class = public_class_match.group(1)
            if declared_class != expected_class:
                raise ValueError(
                    f"Java Syntax Error: Public class '{declared_class}' must be defined "
                    f"in a file named '{declared_class}.java' (current file is '{filename_hint}')"
                )

def validate_code_syntax(filename: str, code: str) -> None:
    """Route code validations based on file extensions."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext == "py":
        validate_python_syntax(code)
    elif ext == "java":
        validate_java_syntax(code, filename)
    else:
        raise ValueError(f"Unsupported file format for syntax analysis: '.{ext}'")
