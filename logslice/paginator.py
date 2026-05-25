"""Paginator: split a sequence of log lines into fixed-size pages."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class Page:
    """A single page of log lines."""
    index: int          # 0-based page number
    lines: List[str]

    @property
    def size(self) -> int:
        return len(self.lines)


@dataclass
class PaginateResult:
    """Result returned by :func:`paginate`."""
    pages: List[Page]
    page_size: int
    total_lines: int

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def is_empty(self) -> bool:
        return self.total_lines == 0


def paginate(
    lines: Sequence[str],
    page_size: int = 50,
) -> PaginateResult:
    """Split *lines* into pages of at most *page_size* entries each.

    Parameters
    ----------
    lines:
        The input lines to paginate.
    page_size:
        Maximum number of lines per page.  Must be >= 1.

    Returns
    -------
    PaginateResult
    """
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size}")

    lines = list(lines)
    pages: List[Page] = []

    for page_index, offset in enumerate(range(0, max(len(lines), 1), page_size)):
        chunk = lines[offset: offset + page_size]
        if not chunk and pages:  # empty tail – only possible when len==0
            break
        pages.append(Page(index=page_index, lines=chunk))

    if not pages:
        pages.append(Page(index=0, lines=[]))

    return PaginateResult(
        pages=pages,
        page_size=page_size,
        total_lines=len(lines),
    )


def get_page(result: PaginateResult, page_number: int) -> Page:
    """Return page by 0-based *page_number*, raising IndexError if out of range."""
    if page_number < 0 or page_number >= len(result.pages):
        raise IndexError(
            f"page_number {page_number} out of range "
            f"(0..{len(result.pages) - 1})"
        )
    return result.pages[page_number]
