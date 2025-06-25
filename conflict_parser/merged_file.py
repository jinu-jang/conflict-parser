import os
from pathlib import Path
from typing import Literal

from conflict_parser._types import ConflictSegment, ContextSegment, MergeMetadata
from conflict_parser.parser.stateful_parsing import parse_content


class MergedFile:
    """A file with merged segments."""

    def __init__(
        self,
        path: str,
        segments: list[ContextSegment | ConflictSegment],
        metadata: MergeMetadata,
    ):
        self.path = path
        self.segments = segments
        """List of segments, which can be either ContextSegment or ConflictSegment."""
        self.metadata: MergeMetadata = metadata

    @classmethod
    def from_content(
        cls, path: str, content: str, metadata: MergeMetadata
    ) -> "MergedFile":
        """Create a MergedFile instance from file content."""
        segments = parse_content(content, metadata)

        return cls(path, segments, metadata)

    @classmethod
    def from_file(
        cls, path: str | os.PathLike[str] | Path, metadata: MergeMetadata
    ) -> "MergedFile":
        """Create a MergedFile instance from a file path."""
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        path_repr = str(Path(path).resolve())
        return cls.from_content(path_repr, content, metadata)

    def to_original_content(self) -> str:
        """Return a byte-for-byte recreation of the conflicted file.

        All conflict markers (`<<<<<<<`, `|||||||`, `=======`, `>>>>>>>`)
        are regenerated using the stored metadata.
        """
        ms = self.metadata.marker_size
        mark_A = "<" * ms
        mark_B = ">" * ms
        mark_O = "|" * ms  # “base” marker (diff3 only)
        mark_M = "=" * ms

        out: list[str] = []

        for seg in self.segments:
            if isinstance(seg, ContextSegment):
                out.extend(seg.lines)
                continue

            # -------- conflict segment -----------------------------------
            out.append(f"{mark_A} {seg.ours_label}\n")
            out.extend(seg.ours_lines)

            if self.metadata.conflict_style == "diff3":
                base_lbl = seg.base_label or ""
                out.append(f"{mark_O} {base_lbl}\n")
                if seg.base_lines:
                    out.extend(seg.base_lines)

            out.append(f"{mark_M}\n")
            out.extend(seg.theirs_lines)
            out.append(f"{mark_B} {seg.theirs_label}\n")

        return "".join(out)

    def resolve_conflicts(
        self, strategy: Literal["take_ours", "take_theirs"] = "take_ours"
    ) -> str:
        """
        Resolve every conflict in the file and return the clean content.

        Parameters
        ----------
        strategy :
            * ``"take_ours"``  : keep the *ours* side, discard *theirs*.
            * ``"take_theirs"``: keep the *theirs* side, discard *ours*.

        Returns
        -------
        str
            A conflict-free version of the file's contents.
        """
        keep_ours = strategy == "take_ours"
        out: list[str] = []

        for seg in self.segments:
            if isinstance(seg, ContextSegment):
                out.extend(seg.lines)
            else:
                chosen = seg.ours_lines if keep_ours else seg.theirs_lines
                out.extend(chosen)

        return "".join(out)
