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
