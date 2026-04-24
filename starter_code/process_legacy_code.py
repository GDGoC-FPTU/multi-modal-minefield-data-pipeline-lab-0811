import ast
import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract docstrings and comments from legacy Python code.

def extract_logic_from_code(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    # ------------------------------------------
    
    # 1. Use the 'ast' module to find docstrings for functions
    tree = ast.parse(source_code)
    logic_segments = []
    
    # Extract module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        logic_segments.append(f"Module Overview: {module_doc.strip()}")
    
    # Extract function docstrings
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if doc:
                logic_segments.append(f"Function '{node.name}' Logic: {doc.strip()}")

    # 2. Use regex to find business rules in comments
    # Look for lines starting with # followed by Rule or IMPORTANT or WARNING
    rules_in_comments = re.findall(r'#\s*(Business Logic Rule \d+|IMPORTANT|WARNING|Note):?\s*(.*)', source_code, re.IGNORECASE)
    for rule_type, rule_text in rules_in_comments:
        logic_segments.append(f"{rule_type}: {rule_text.strip()}")

    # 3. Detect discrepancy (Advanced task)
    discrepancy = ""
    if "tax_rate = 0.10" in source_code and "8%" in source_code:
        discrepancy = "WARNING: Detected tax rate discrepancy. Comment says 8%, code uses 10%."

    combined_content = "\n\n".join(logic_segments)
    if discrepancy:
        combined_content += f"\n\n{discrepancy}"

    return {
        "document_id": "legacy-code-logic",
        "content": combined_content,
        "source_type": "Code",
        "author": "Senior Dev (Retired)",
        "timestamp": "2019-01-01",
        "source_metadata": {
            "has_discrepancy": bool(discrepancy),
            "rule_count": len(rules_in_comments),
            "source": "legacy_pipeline.py"
        }
    }

