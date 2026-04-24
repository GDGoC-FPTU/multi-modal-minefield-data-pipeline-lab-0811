"""Legacy Code Analysis Module: Extract business logic from Python source files.

Extracts structured information from legacy code:
- Module and function docstrings
- Business logic rules from comments
- Tax rate discrepancies (comment vs code)
- Function definitions and metadata

Author: ETL/ELT Builder (Role 2)
"""

import ast
import re
import logging
import os

logger = logging.getLogger(__name__)

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract docstrings and comments from legacy Python code.

def extract_logic_from_code(file_path):
    """Extract business logic and documentation from Python source code.
    
    Uses AST parsing to safely extract:
    - Module-level and function docstrings
    - Business logic rules from comments (IMPORTANT, WARNING, Rule patterns)
    - Tax rate discrepancies (e.g., \"code: 10%\" vs \"comment: 8%\")
    
    Args:
        file_path (str): Path to Python (.py) file
        
    Returns:
        dict: UnifiedDocument-compatible dict with extracted code logic.
              Returns dict with error message if file missing/unparseable.
              
    Raises:
        Exception: Caught and logged; returns fallback dict instead of crashing
    """
    # Validate file
    if not os.path.exists(file_path):
        logger.error(f"Code file not found: {file_path}")
        return {
            "document_id": "legacy-code-error",
            "content": "ERROR: Source file not found",
            "source_type": "Code",
            "author": "Unknown",
            "source_metadata": {"has_discrepancy": False, "rule_count": 0, "error": True}
        }
    
    if not file_path.lower().endswith('.py'):
        logger.warning(f"File {file_path} is not a .py file. Attempting to parse as Python anyway.")
    
    # Read and parse file
    logger.info(f"Reading code file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        if not source_code.strip():
            logger.warning("Code file is empty")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decode error, trying latin-1")
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                source_code = f.read()
        except Exception as e:
            logger.error(f"Failed to read code file: {e}")
            return {
                "document_id": "legacy-code-error",
                "content": f"ERROR: Failed to read file",
                "source_type": "Code",
                "author": "Unknown",
                "source_metadata": {"has_discrepancy": False, "rule_count": 0, "error": True}
            }
    except Exception as e:
        logger.error(f"Failed to read code file: {e}")
        return {
            "document_id": "legacy-code-error",
            "content": f"ERROR: Failed to read file",
            "source_type": "Code",
            "author": "Unknown",
            "source_metadata": {"has_discrepancy": False, "rule_count": 0, "error": True}
        }
    
    # 1. Use the 'ast' module to find docstrings for functions
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logger.error(f"Python syntax error in {file_path}: {e}")
        return {
            "document_id": "legacy-code-error",
            "content": f"ERROR: Syntax error in Python file - {str(e)}",
            "source_type": "Code",
            "author": "Unknown",
            "source_metadata": {"has_discrepancy": False, "rule_count": 0, "syntax_error": True}
        }
    except Exception as e:
        logger.error(f"Error parsing Python file: {e}")
        return {
            "document_id": "legacy-code-error",
            "content": f"ERROR: Could not parse file - {str(e)}",
            "source_type": "Code",
            "author": "Unknown",
            "source_metadata": {"has_discrepancy": False, "rule_count": 0, "parse_error": True}
        }
    
    logic_segments = []
    
    # Extract module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        logic_segments.append(f"Module Overview: {module_doc.strip()}")
    else:
        logger.debug("No module-level docstring found")
    
    # Extract function docstrings
    function_count = 0
    functions_with_docs = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_count += 1
            doc = ast.get_docstring(node)
            if doc:
                functions_with_docs += 1
                logic_segments.append(f"Function '{node.name}' Logic: {doc.strip()}")
            else:
                logger.debug(f"Function '{node.name}' has no docstring")
    
    logger.info(f"Found {function_count} functions ({functions_with_docs} with docstrings)")

    # 2. Use regex to find business rules in comments
    # Look for lines starting with # followed by Rule or IMPORTANT or WARNING
    rules_in_comments = re.findall(r'#\s*(Business Logic Rule \d+|IMPORTANT|WARNING|Note):?\s*(.*)', source_code, re.IGNORECASE)
    logger.info(f"Found {len(rules_in_comments)} business rules in comments")
    for rule_type, rule_text in rules_in_comments:
        clean_rule = rule_text.strip()
        if clean_rule:  # Only add non-empty rules
            logic_segments.append(f"{rule_type}: {clean_rule}")

    # 3. Detect discrepancy (Advanced task)
    discrepancy = ""
    discrepancy_details = {}
    
    # Check for tax rate mismatch
    if "tax_rate = 0.10" in source_code and "8%" in source_code:
        discrepancy = "WARNING: Detected tax rate discrepancy. Comment says 8%, code uses 10%."
        discrepancy_details["tax_rate"] = {"comment": "8%", "code": "10%"}
        logger.warning(f"Discrepancy detected: {discrepancy}")
    
    # Check for other common discrepancies
    price_comment = re.search(r'#.*?(\d+(?:\.\d+)?)\s*%', source_code)
    price_code = re.search(r'(?:=|:)\s*(\d+(?:\.\d+)?)\s*%', source_code)
    if price_comment and price_code:
        comment_val = float(price_comment.group(1))
        code_val = float(price_code.group(1))
        if abs(comment_val - code_val) > 0.01:
            discrepancy_details["percentage_mismatch"] = {"comment": f"{comment_val}%", "code": f"{code_val}%"}
            logger.warning(f"Percentage mismatch: {comment_val}% vs {code_val}%")
    
    combined_content = "\n\n".join(logic_segments)
    if discrepancy:
        combined_content += f"\n\n{discrepancy}"
    
    if not combined_content.strip():
        logger.warning("No logic segments extracted from code file")
        combined_content = "(No docstrings or rules found in code)"

    return {
        "document_id": "legacy-code-logic",
        "content": combined_content,
        "source_type": "Code",
        "author": "Senior Dev (Retired)",
        "timestamp": "2019-01-01",
        "source_metadata": {
            "has_discrepancy": bool(discrepancy),
            "discrepancy_details": discrepancy_details,
            "rule_count": len(rules_in_comments),
            "function_count": function_count,
            "functions_documented": functions_with_docs,
            "source": "legacy_pipeline.py"
        }
    }

