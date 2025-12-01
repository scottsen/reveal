"""B001: Bare except clause detector.

Detects bare except clauses in Python that catch all exceptions including SystemExit.
"""

import ast
import logging
from typing import List, Dict, Any, Optional

from ..base import BaseRule, Detection, RulePrefix, Severity

logger = logging.getLogger(__name__)


class B001(BaseRule):
    """Detect bare except clauses in Python code."""

    code = "B001"
    message = "Bare except clause catches all exceptions including SystemExit"
    category = RulePrefix.B
    severity = Severity.HIGH
    file_patterns = ['.py']
    version = "1.0.0"

    def check(self,
             file_path: str,
             structure: Optional[Dict[str, Any]],
             content: str) -> List[Detection]:
        """
        Check for bare except clauses using AST parsing.

        Args:
            file_path: Path to Python file
            structure: Parsed structure (not used, we parse AST ourselves)
            content: File content

        Returns:
            List of detections
        """
        detections = []

        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            logger.debug(f"Syntax error in {file_path}, skipping B001 check: {e}")
            return detections

        # Walk the AST looking for bare except handlers
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except has type=None
                if node.type is None:
                    # Get context (the except line)
                    try:
                        context = ast.get_source_segment(content, node)
                        if context:
                            # Just show first line of context
                            context = context.split('\n')[0]
                    except Exception:
                        context = None

                    detections.append(self.create_detection(
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset + 1,  # AST is 0-indexed, display is 1-indexed
                        suggestion="Use 'except Exception:' or specific exception types (ValueError, IOError, etc.)",
                        context=context
                    ))

        return detections
