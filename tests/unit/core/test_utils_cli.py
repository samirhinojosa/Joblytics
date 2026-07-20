from joblytics.core.utils.cli import render_table, truncate


def test_truncate_none_returns_empty_string() -> None:
    assert truncate(None, 10) == ""


def test_truncate_short_value_is_unchanged() -> None:
    assert truncate("abc", 10) == "abc"


def test_truncate_long_value_is_ellipsized() -> None:
    assert truncate("abcdefgh", 5) == "abcd…"


def test_render_table_no_rows_returns_message() -> None:
    assert render_table([], drop=set()) == "No results."


def test_render_table_uses_str_for_columns_without_limit() -> None:
    rows = [{"title": "Data Engineer", "count": 3}]
    table = render_table(rows, drop=set())
    assert "Data Engineer" in table
    assert "3" in table


def test_render_table_drops_and_truncates_columns() -> None:
    rows = [{"title": "Data Engineer", "company": "Acme", "internal_id": "linkedin:1"}]
    table = render_table(rows, drop={"internal_id"}, col_limits={"title": 4})
    assert "internal_id" not in table
    assert "linkedin:1" not in table
    assert "Dat…" in table
