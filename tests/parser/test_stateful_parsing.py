import textwrap
from pathlib import Path

from conflict_parser import ConflictSegment, ContextSegment, MergedFile, MergeMetadata
from conflict_parser.parser.stateful_parsing import parse_content


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _strip_margin(s: str) -> str:
    """Convenient multi-line string literal helper."""
    return textwrap.dedent(s.lstrip("\n"))


def _as_lines(src: str) -> list[str]:
    """Split into lines **with** their trailing newlines (`keepends=True`)."""
    return src.splitlines(keepends=True)


# --------------------------------------------------------------------------- #
# Merge-style conflict tests
# --------------------------------------------------------------------------- #
MERGE_SAMPLE = _strip_margin(
    """
    line1
    <<<<<<< HEAD
    ours1
    ours2
    =======
    theirs1
    theirs2
    >>>>>>> feature-branch
    line_after
    """
)


def test_parse_merge_conflict_segments():
    meta = MergeMetadata(conflict_style="merge")
    segments = parse_content(MERGE_SAMPLE, meta)

    # Expect: context / conflict / context  => 3 segments
    assert len(segments) == 3

    # ---- first context block ------------------------------------------------
    ctx1 = segments[0]
    assert isinstance(ctx1, ContextSegment)
    assert ctx1.start_line_no == 1
    assert ctx1.lines == _as_lines("line1\n")

    # ---- conflict block -----------------------------------------------------
    c1 = segments[1]
    assert isinstance(c1, ConflictSegment)
    assert c1.start_line_no == 2
    assert c1.ours_label == "HEAD"
    assert c1.theirs_label == "feature-branch"
    assert c1.base_label is None
    assert c1.ours_lines == _as_lines("ours1\nours2\n")
    assert c1.theirs_lines == _as_lines("theirs1\n" "theirs2\n")

    # ---- trailing context ---------------------------------------------------
    ctx2 = segments[2]
    assert isinstance(ctx2, ContextSegment)
    assert ctx2.start_line_no == 9
    assert ctx2.lines == _as_lines("line_after\n")


# --------------------------------------------------------------------------- #
# diff3-style conflict tests
# --------------------------------------------------------------------------- #
DIFF3_SAMPLE = _strip_margin(
    """
    start
    <<<<<<< HEAD
    ours only
    ||||||| base
    base line
    =======
    theirs only
    >>>>>>> feature-branch
    end
    """
)


def test_parse_diff3_conflict_segments():
    meta = MergeMetadata(conflict_style="diff3")
    segments = parse_content(DIFF3_SAMPLE, meta)

    # context / conflict / context  => 3 segments
    assert len(segments) == 3

    # ---- conflict block specifics ------------------------------------------
    c1 = segments[1]
    assert isinstance(c1, ConflictSegment)

    assert c1.start_line_no == 2
    assert c1.ours_label == "HEAD"
    assert c1.base_label == "base"
    assert c1.theirs_label == "feature-branch"

    assert c1.ours_lines == _as_lines("ours only\n")
    assert c1.base_lines == _as_lines("base line\n")
    assert c1.theirs_lines == _as_lines("theirs only\n")


# --------------------------------------------------------------------------- #
# Integration test via MergedFile helpers
# --------------------------------------------------------------------------- #
def test_mergedfile_from_content_and_file(tmp_path: Path):
    meta = MergeMetadata(conflict_style="merge")
    content = MERGE_SAMPLE

    # -- from_content --------------------------------------------------------
    mf_mem = MergedFile.from_content("dummy.txt", content, meta)
    assert mf_mem.path == "dummy.txt"
    assert mf_mem.segments == parse_content(content, meta)

    # -- from_file -----------------------------------------------------------
    p = tmp_path / "merge.txt"
    p.write_text(content, encoding="utf-8")

    mf_disk = MergedFile.from_file(p, meta)

    # Path should be absolute because from_file() resolves it
    assert Path(mf_disk.path).resolve() == p.resolve()
    assert mf_disk.segments == mf_mem.segments
