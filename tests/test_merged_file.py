import textwrap
from typing import Literal

import pytest

from conflict_parser import MergedFile, MergeMetadata


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _clean(src: str) -> str:
    """Remove margin and initial newline for nicer literals."""
    return textwrap.dedent(src.lstrip("\n"))


# -------------------- example inputs used across tests --------------------- #
MERGE_RAW = _clean(
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

DIFF3_RAW = _clean(
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


# --------------------------------------------------------------------------- #
# 1. Exact round-trip for `to_original_content`
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("raw", "style"),
    [(MERGE_RAW, "merge"), (DIFF3_RAW, "diff3")],
)
def test_roundtrip_to_original_content(raw: str, style: Literal["merge", "diff3"]):
    meta = MergeMetadata(conflict_style=style)
    mf = MergedFile.from_content("dummy.txt", raw, meta)

    assert mf.to_original_content() == raw


# --------------------------------------------------------------------------- #
# 2. Conflict-resolution helper
# --------------------------------------------------------------------------- #
def test_resolve_conflicts_merge():
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", MERGE_RAW, meta)

    ours_expected = _clean(
        """
        line1
        ours1
        ours2
        line_after
        line1
        ours1
        ours2
        line_after
        """
    )
    theirs_expected = _clean(
        """
        line1
        theirs1
        theirs2
        line_after
        line1
        theirs1
        theirs2
        line_after
        """
    )

    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


def test_resolve_conflicts_diff3():
    meta = MergeMetadata(conflict_style="diff3")
    mf = MergedFile.from_content("demo", DIFF3_RAW, meta)

    ours_expected = _clean(
        """
        start
        ours only
        end
        start
        ours only
        end
        """
    )
    theirs_expected = _clean(
        """
        start
        theirs only
        end
        start
        theirs only
        end
        """
    )

    # default strategy is "take_ours"
    assert mf.resolve_conflicts() == ours_expected
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# --------------------------------------------------------------------------- #
# 3. Edge-cases requested by the user
# --------------------------------------------------------------------------- #


# 3.1. Conflict starts on line 1 (merge)
def test_merge_conflict_at_start():
    raw = _clean(
        """
        <<<<<<< HEAD
        ours
        =======
        theirs
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        ours
        after
        """
    )
    theirs_expected = _clean(
        """
        theirs
        after
        """
    )

    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.2. Conflict has only an empty line afterwards (merge)
def test_merge_conflict_only_empty_line_after():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        ours
        =======
        theirs
        >>>>>>> branch
        """
    )
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        ours
        """
    )
    theirs_expected = _clean(
        """
        line
        theirs
        """
    )
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.3. Conflict ends directly at EOF (merge)
@pytest.mark.skip("Git merge algorithm always adds an EOL")
def test_merge_conflict_at_eof():
    raw = _clean(
        """line
        <<<<<<< HEAD
        ours
        =======
        theirs
        >>>>>>> branch"""
    )
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", raw, meta)

    assert mf.resolve_conflicts("take_ours") == "line\nours"
    assert mf.resolve_conflicts("take_theirs") == "line\ntheirs"


# 3.4. Merge style – ours (A) empty
def test_merge_ours_empty():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        =======
        theirs
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        after
        """
    )
    theirs_expected = _clean(
        """
        line
        theirs
        after
        """
    )
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.5. Merge style – theirs (B) empty
def test_merge_theirs_empty():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        ours
        =======
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="merge")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        ours
        after
        """
    )
    theirs_expected = _clean(
        """
        line
        after
        """
    )
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.6. Diff3 style – ours (A) empty
def test_diff3_ours_empty():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        ||||||| base
        base
        =======
        theirs
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="diff3")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        after
        """
    )
    theirs_expected = _clean(
        """
        line
        theirs
        after
        """
    )
    assert mf.resolve_conflicts() == ours_expected  # default take_ours
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.7. Diff3 style – base empty
def test_diff3_base_empty():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        ours
        ||||||| base
        =======
        theirs
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="diff3")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        ours
        after
        """
    )
    theirs_expected = _clean(
        """
        line
        theirs
        after
        """
    )
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected


# 3.8. Diff3 style – theirs (B) empty
def test_diff3_theirs_empty():
    raw = _clean(
        """
        line
        <<<<<<< HEAD
        ours
        ||||||| base
        base
        =======
        >>>>>>> branch
        after
        """
    )
    meta = MergeMetadata(conflict_style="diff3")
    mf = MergedFile.from_content("demo", raw, meta)

    ours_expected = _clean(
        """
        line
        ours
        after
        """
    )
    theirs_expected = _clean(
        """
        line
        after
        """
    )
    assert mf.resolve_conflicts("take_ours") == ours_expected
    assert mf.resolve_conflicts("take_theirs") == theirs_expected
