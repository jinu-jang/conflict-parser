from typing import Literal

from conflict_parser._types import ConflictSegment, ContextSegment, MergeMetadata


def parse_content(
    content: str, metadata: MergeMetadata
) -> list[ContextSegment | ConflictSegment]:
    """
    Split a merge-conflicted file into context and conflict segments.

    The function understands the two styles Git can emit:

    * merge: `<<<<<<< / ======= / >>>>>>>`
    * diff3: `<<<<<<< / ||||||| / ======= / >>>>>>>`

    It returns the pieces in the original order, each tagged with the
    1-based line-number where the segment began.
    """
    mark_A = "<" * metadata.marker_size
    mark_O = "|" * metadata.marker_size
    mark_Mid = "=" * metadata.marker_size
    mark_B = ">" * metadata.marker_size

    lines = content.splitlines(keepends=True)

    segments: list[ContextSegment | ConflictSegment] = []

    # --- running buffers ---------------------------------------------------
    ctx_lines: list[str] = []
    ctx_start: int | None = None

    conflict: ConflictSegment | None = None
    state: Literal["context", "ours", "base", "theirs"] = "context"
    # ----------------------------------------------------------------------

    def flush_context() -> None:
        nonlocal ctx_lines, ctx_start
        if ctx_start is None:
            # No context to flush
            # Expected only when file starts or ends with a conflict
            return

        if ctx_lines:
            segments.append(
                ContextSegment(start_line_no=ctx_start, lines=ctx_lines.copy())
            )
            ctx_lines = []
            ctx_start = None

    for idx, line in enumerate(lines):
        lineno = idx + 1

        # -------------------------------- context ---------------------------
        if state == "context":
            if line.startswith(mark_A):
                flush_context()

                ours_label = line[metadata.marker_size :].strip()
                conflict = ConflictSegment(
                    start_line_no=lineno,
                    ours_label=ours_label,
                    theirs_label="",
                    ours_lines=[],
                    theirs_lines=[],
                    base_label=None,
                    base_lines=None,
                )
                state = "ours"
            else:
                if ctx_start is None:
                    ctx_start = lineno
                ctx_lines.append(line)

        # -------------------------------- ours ------------------------------
        elif state == "ours":
            if line.startswith(mark_Mid):
                state = "theirs"
                continue

            if conflict is None:
                raise ValueError(
                    f"State 'ours' without an active conflict segment: line {lineno}."
                )

            if metadata.conflict_style == "diff3" and line.startswith(mark_O):
                conflict.base_label = line[metadata.marker_size :].strip()
                conflict.base_lines = []
                state = "base"
            else:
                conflict.ours_lines.append(line)

        # -------------------------------- base ------------------------------
        elif state == "base":
            if line.startswith(mark_Mid):
                state = "theirs"
                continue

            if conflict is None or conflict.base_lines is None:
                raise ValueError(
                    f"State 'base' without an active conflict segment: line {lineno}."
                )
            conflict.base_lines.append(line)

        # ------------------------------- theirs -----------------------------
        elif state == "theirs":
            if conflict is None:
                raise ValueError(
                    f"State 'theirs' without an active conflict segment: line {lineno}."
                )

            if line.startswith(mark_B):
                conflict.theirs_label = line[metadata.marker_size :].strip()
                segments.append(conflict)
                conflict = None
                state = "context"
            else:
                conflict.theirs_lines.append(line)

    # trailing context that follows the final conflict
    flush_context()

    return segments
