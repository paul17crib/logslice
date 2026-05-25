"""Tests for logslice.paginator."""
import pytest
from logslice.paginator import Page, PaginateResult, paginate, get_page


LINES = [f"line {i}" for i in range(1, 11)]  # 10 lines


# ---------------------------------------------------------------------------
# paginate – basic structure
# ---------------------------------------------------------------------------

def test_paginate_returns_paginate_result():
    result = paginate(LINES, page_size=3)
    assert isinstance(result, PaginateResult)


def test_paginate_pages_are_page_instances():
    result = paginate(LINES, page_size=3)
    assert all(isinstance(p, Page) for p in result.pages)


def test_paginate_total_lines_matches_input():
    result = paginate(LINES, page_size=3)
    assert result.total_lines == len(LINES)


def test_paginate_correct_page_count():
    # 10 lines / page_size 3 -> ceil(10/3) = 4 pages
    result = paginate(LINES, page_size=3)
    assert result.page_count == 4


def test_paginate_page_size_stored():
    result = paginate(LINES, page_size=5)
    assert result.page_size == 5


def test_paginate_first_page_correct_lines():
    result = paginate(LINES, page_size=4)
    assert result.pages[0].lines == LINES[:4]


def test_paginate_last_page_may_be_smaller():
    result = paginate(LINES, page_size=3)
    last = result.pages[-1]
    assert last.lines == ["line 10"]


def test_paginate_page_index_sequential():
    result = paginate(LINES, page_size=3)
    assert [p.index for p in result.pages] == list(range(result.page_count))


def test_paginate_page_size_property():
    result = paginate(LINES, page_size=3)
    for page in result.pages[:-1]:  # all full pages
        assert page.size == 3


def test_paginate_all_lines_preserved():
    result = paginate(LINES, page_size=3)
    reconstructed = [line for page in result.pages for line in page.lines]
    assert reconstructed == LINES


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_paginate_empty_input_returns_one_empty_page():
    result = paginate([], page_size=10)
    assert result.page_count == 1
    assert result.pages[0].lines == []
    assert result.total_lines == 0
    assert result.is_empty


def test_paginate_page_size_larger_than_input_single_page():
    result = paginate(LINES, page_size=100)
    assert result.page_count == 1
    assert result.pages[0].lines == LINES


def test_paginate_page_size_equal_to_input():
    result = paginate(LINES, page_size=len(LINES))
    assert result.page_count == 1


def test_paginate_page_size_one():
    result = paginate(LINES, page_size=1)
    assert result.page_count == len(LINES)
    assert all(p.size == 1 for p in result.pages)


def test_paginate_invalid_page_size_raises():
    with pytest.raises(ValueError):
        paginate(LINES, page_size=0)


# ---------------------------------------------------------------------------
# get_page
# ---------------------------------------------------------------------------

def test_get_page_returns_correct_page():
    result = paginate(LINES, page_size=3)
    page = get_page(result, 1)
    assert page.index == 1
    assert page.lines == LINES[3:6]


def test_get_page_out_of_range_raises_index_error():
    result = paginate(LINES, page_size=5)
    with pytest.raises(IndexError):
        get_page(result, 99)


def test_get_page_negative_raises_index_error():
    result = paginate(LINES, page_size=5)
    with pytest.raises(IndexError):
        get_page(result, -1)
