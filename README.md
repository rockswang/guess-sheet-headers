# guess-sheet-headers

[中文文档](README_zh.md)

`guess-sheet-headers` is a small heuristic Python package for guessing the header row range of Excel-like two-dimensional data. It is designed for practical automation, not perfect spreadsheet understanding.

The input is a two-dimensional list-like object. The output is a `(start, end)` tuple using zero-based, left-closed/right-open row indexes. `(0, 0)` means no reliable header was detected.

```python
from datetime import date
from guess_sheet_headers import do_guess

rows = [
    ["姓名", "金额", "日期"],
    ["张三", 10, date(2026, 1, 1)],
    ["李四", 20, date(2026, 1, 2)],
]

assert do_guess(rows) == (0, 1)
```

## Install

For local development:

```bash
python -m pip install -e .
```

The package has no runtime dependencies.

## Algorithm

The default heuristic is intentionally simple and works in two stages: first find a suspected data region, then decide how many rows above it should be kept as the header range.

1. Sample at most 200 rows.
2. If total rows are at most 200, use all rows.
3. Otherwise sample the first 100 rows, 50 middle rows, and 50 tail rows, then remove duplicate indexes.
4. Before sampling, trim all-empty columns at the left and right edges and all-empty rows at the bottom. Top empty rows, middle empty rows, and middle empty columns are kept.
5. Convert cells to integer types.
6. For each column, count all types including `EMPTY`.
7. Keep at most three types whose per-column ratio is greater than 30%; if none exceed 30%, the column profile is an empty set.
8. All column type sets form the data-region profile.
9. Scan top rows. The first row whose score is greater than 0.9 is treated as the suspected first data row.
10. In the suspected header area before that row, find the row with the highest text density, where text density is `(PHRASE + SENTENCE) / column_count` and empty cells stay in the denominator.
11. Return `(0, best_header_row + 1)` so merged-cell titles and notes above the field row remain part of the header range. If the first row already matches data, return one default header row.

The match score is:

```text
sum(column_weight) / column_count
```

Column weights:

```text
type is in column profile: 1.0
otherwise: 0.0
empty profile set: skipped, not included in denominator
```

## Cell Types

Cell types are plain integers:

```python
EMPTY = 0
NUMBER = 1
DATETIME = 2
NUMERIC_STR = 3
PHRASE = 4
SENTENCE = 5
```

Notes:

`DATETIME` is used only when the parser has already returned a Python `datetime`, `date`, or `time` object.

`NUMERIC_STR` is used for strings that contain digits plus numeric separators or symbols, such as `+25.3` or `2026/3/7`.

`PHRASE` is short text. `SENTENCE` is longer natural-language text. For ASCII text, the rule splits by whitespace and punctuation except `-` and `_`; more than one segment is a sentence. For non-ASCII text, more than 8 non-space characters is a sentence.

## Configuration

Use `GuessOptions` to tune thresholds and sample sizes:

```python
from guess_sheet_headers import GuessOptions, do_guess

options = GuessOptions(
    match_threshold=0.9,
    col_type_threshold=0.3,
    min_sample_rows=10,
)

result = do_guess(rows, options)
```

## Limitations

This is a guessing algorithm for common structured tables, not a strict Excel understanding engine. It intentionally favors simple, predictable behavior over exhaustive edge-case handling.

Known weak cases include very small sheets, sparse data rows, heavily mixed column types, multiple unrelated tables in one sheet, long title/description blocks before the table, and sheets where group headers have many empty cells that match a sparse data profile.

## Development

Run tests from this directory:

```bash
python -m unittest discover -s tests
```

## License

MIT License. See [LICENSE](LICENSE).
