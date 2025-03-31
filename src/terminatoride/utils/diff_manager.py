"""
Diff management utilities for TerminatorIDE.
Provides functionality for generating, displaying, and applying code diffs.

Usage:
    from terminatoride.utils.diff_manager import DiffManager

    # Generate a diff
    diff = DiffManager.generate_diff(original_code, modified_code)

    # Apply a patch
    result = DiffManager.apply_patch(original_code, patch_text)
"""

import difflib
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class DiffType(Enum):
    """Types of diffs."""

    UNIFIED = "unified"
    CONTEXT = "context"
    NDIFF = "ndiff"
    HTML = "html"


@dataclass
class DiffChange:
    """A diff change (insertion or deletion)."""

    line_number: int
    content: str
    is_addition: bool


class DiffManager:
    """Manages code diffs using difflib."""

    @staticmethod
    def generate_diff(
        original: str,
        modified: str,
        diff_type: DiffType = DiffType.UNIFIED,
        context_lines: int = 3,
    ) -> str:
        """
        Generate a diff between original and modified text.

        Args:
            original: Original text
            modified: Modified text
            diff_type: Type of diff to generate
            context_lines: Number of context lines (for unified and context diffs)

        Returns:
            Diff text as a string
        """
        original_lines = original.splitlines(True)
        modified_lines = modified.splitlines(True)

        if diff_type == DiffType.UNIFIED:
            diff = difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile="Original",
                tofile="Modified",
                n=context_lines,
            )
            return "".join(diff)

        elif diff_type == DiffType.CONTEXT:
            diff = difflib.context_diff(
                original_lines,
                modified_lines,
                fromfile="Original",
                tofile="Modified",
                n=context_lines,
            )
            return "".join(diff)

        elif diff_type == DiffType.NDIFF:
            diff = difflib.ndiff(original_lines, modified_lines)
            return "".join(diff)

        elif diff_type == DiffType.HTML:
            diff = difflib.HtmlDiff().make_file(
                original_lines,
                modified_lines,
                "Original",
                "Modified",
                context=context_lines,
            )
            return diff

        # Default to unified diff
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile="Original",
            tofile="Modified",
            n=context_lines,
        )
        return "".join(diff)

    @staticmethod
    def get_changes(original: str, modified: str) -> List[DiffChange]:
        """
        Get a list of changes between original and modified text.

        Args:
            original: Original text
            modified: Modified text

        Returns:
            List of DiffChange objects
        """
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()

        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        changes = []

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "delete":
                for i in range(i1, i2):
                    changes.append(DiffChange(i, original_lines[i], False))
            elif op == "insert":
                for j in range(j1, j2):
                    changes.append(DiffChange(j, modified_lines[j], True))
            elif op == "replace":
                # Handle as deletions followed by insertions
                for i in range(i1, i2):
                    changes.append(DiffChange(i, original_lines[i], False))
                for j in range(j1, j2):
                    changes.append(DiffChange(j, modified_lines[j], True))

        return changes

    @staticmethod
    def apply_patch(original: str, patch_text: str) -> Optional[str]:
        """
        Apply a unified diff patch to the original text.

        Args:
            original: Original text
            patch_text: Unified diff patch

        Returns:
            Modified text or None if patch can't be applied
        """
        try:
            # Parse the patch - this is a simplified implementation
            original_lines = original.splitlines()
            current_line = 0
            result_lines = []

            # Basic regex patterns for unified diff
            hunk_header_pattern = re.compile(r"^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@")

            lines = patch_text.splitlines()
            i = 0

            # Skip the header lines
            while i < len(lines) and not lines[i].startswith("@@"):
                i += 1

            while i < len(lines):
                line = lines[i]

                # Parse hunk header
                match = hunk_header_pattern.match(line)
                if match:
                    orig_start = int(match.group(1))
                    orig_count = int(match.group(2) or "1")
                    _ = int(match.group(3))
                    _ = int(match.group(4) or "1")

                    # Add unchanged lines before this hunk
                    result_lines.extend(original_lines[current_line : orig_start - 1])
                    current_line = orig_start - 1

                    i += 1

                    # Apply the hunk
                    orig_lines_processed = 0

                    while orig_lines_processed < orig_count and i < len(lines):
                        line = lines[i]

                        if line.startswith(" "):  # Context line
                            result_lines.append(line[1:])
                            current_line += 1
                            orig_lines_processed += 1
                        elif line.startswith("-"):  # Deletion
                            current_line += 1
                            orig_lines_processed += 1
                        elif line.startswith("+"):  # Addition
                            result_lines.append(line[1:])
                        elif line.startswith("@@"):  # New hunk
                            break

                        i += 1
                else:
                    i += 1

            # Add any remaining lines
            result_lines.extend(original_lines[current_line:])

            return "\n".join(result_lines)
        except Exception as e:
            print(f"Error applying patch: {e}")
            return None

    @staticmethod
    def highlight_diff(original: str, modified: str) -> Tuple[List[str], List[str]]:
        """Return two lists: lines removed and lines added."""
        matcher = difflib.SequenceMatcher(
            None, original.splitlines(), modified.splitlines()
        )

        removed = []
        added = []

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "delete":
                removed.extend(original.splitlines()[i1:i2])
            elif op == "insert":
                added.extend(modified.splitlines()[j1:j2])
            elif op == "replace":
                removed.extend(original.splitlines()[i1:i2])
                added.extend(modified.splitlines()[j1:j2])

        return removed, added
