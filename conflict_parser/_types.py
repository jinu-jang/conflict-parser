from dataclasses import dataclass
from typing import Literal


@dataclass
class MergeMetadata:
    conflict_style: Literal["merge", "diff3"] = "merge"
    """The conflict style used in the merge.
    - "merge" for standard merge conflicts (<<<<<<<, =======, >>>>>>>)
    - "diff3" for three-way merge conflicts (includes base)
    """

    marker_size: int = 7
    """The size of the conflict markers (default is 7)."""


@dataclass
class ContextSegment:
    """Uncontested lines between conflicts."""

    start_line_no: int
    """Original line number in file"""
    lines: list[str]
    """Lines of text, including newline characters for easy joining."""


@dataclass
class ConflictSegment:
    """A `<<<<<<<` … `=======` … `>>>>>>>` chunk."""

    start_line_no: int
    """Where the '<<<<<<<' marker appeared."""
    ours_label: str
    """Label for our side, e.g. 'HEAD' or branch name."""
    theirs_label: str
    """Label for their side, e.g. commit SHA or branch name."""

    ours_lines: list[str]
    """Lines from our side."""
    theirs_lines: list[str]
    """Lines from their side."""

    base_label: str | None = None
    """Label for the base side (diff3 only)."""
    base_lines: list[str] | None = None
    """Lines from the base (diff3 only)."""
