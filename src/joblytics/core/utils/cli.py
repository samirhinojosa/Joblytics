from tabulate import tabulate
from typing import Any, Mapping, Sequence

# ============================
# CLI TABLE RENDERING HELPERS
# ============================
# Utilities for formatting and rendering tabular data in console/CLI outputs.
# These functions belong to the presentation layer and should not contain
# business logic or data transformation logic.


def truncate(value: Any, max_len: int) -> str:
    """
    Truncate a value for safe console display.

    Converts any value to string and truncates it to a maximum length,
    appending an ellipsis when needed. Intended for CLI/table rendering
    to preserve readability in terminal outputs.

    Args:
        value (Any): Any printable value.
        max_len (int): Maximum allowed string length.

    Returns:
        Truncated string representation.
    """
    if value is None:
        return ""
    s = str(value)
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def render_table(
    rows: Sequence[Mapping[str, Any]],
    *,
    drop: set[str],
    col_limits: dict[str, int] | None = None,
) -> Any:
    """
    Render a formatted table for console (CLI) output.

    This function is responsible only for presentation logic:
    - column filtering
    - per-column truncation
    - formatting for terminal display

    It must not contain business rules, data extraction logic,
    or persistence logic.

    Args:
        rows: Sequence of dictionaries representing row data.
        drop: Set of column names to exclude from rendering.
        col_limits: Optional per-column maximum length configuration.

    Returns:
        Formatted table string ready for console printing.
    """
    if not rows:
        return "No results."

    col_limits = col_limits or {}

    cols = [k for k in rows[0].keys() if k not in drop]

    table = []
    for r in rows:
        row = []
        for c in cols:
            raw = r.get(c, "")
            limit = col_limits.get(c)
            if limit:
                row.append(truncate(raw, limit))
            else:
                row.append(str(raw))
        table.append(row)

    return tabulate(
        table,
        headers=cols,
        tablefmt="github",
        showindex=False,
        colalign=("left",) * len(cols),
    )
