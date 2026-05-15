# guess-sheet-headers

[English README](README.md)

`guess-sheet-headers` 是一个轻量级启发式 Python 包，用于猜测 Excel 类二维数据的表头行范围。它面向自动化处理和 RAG 分块优化，不追求对所有复杂表格完全精确。

输入是二维列表。输出是 `(start, end)` 元组，行号从 0 开始，左闭右开。`(0, 0)` 表示没有可靠识别出表头。

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

## 安装

本地开发安装：

```bash
python -m pip install -e .
```

运行时没有第三方依赖。

## 算法

默认算法分两步：先找疑似数据区，再判断其上方哪些行应保留为表头范围。

1. 最多采样 200 行。
2. 总行数不超过 200 时使用全部行。
3. 否则采样前 100 行、中部 50 行、尾部 50 行，并去重。
4. 采样前裁剪最左和最右的全空列，以及底部全空行。顶部空行、中间空行、中间空列保留。
5. 将单元格转换为整数类型。
6. 每列统计所有类型，包括 `EMPTY`。
7. 每列保留占比超过 30% 的最多前三种类型；如果没有类型超过 30%，该列画像为空集合。
8. 所有列的类型集合组成数据区画像。
9. 从头部开始扫描，第一行匹配分数大于 0.9 的行视为疑似数据区第一行。
10. 在疑似表头区内，找文本密度最高的行。文本密度为 `(PHRASE + SENTENCE) / column_count`，`EMPTY` 仍保留在分母中。
11. 返回 `(0, best_header_row + 1)`，这样字段行上方的合并单元格标题、说明等仍属于表头范围。如果第 0 行已经匹配数据区，返回默认一行表头。

匹配分数：

```text
sum(column_weight) / column_count
```

列权重：

```text
当前类型在该列画像中: 1.0
否则: 0.0
画像为空集合: 跳过，不参与分母
```

## 单元格类型

单元格类型使用普通整数：

```python
EMPTY = 0
NUMBER = 1
DATETIME = 2
NUMERIC_STR = 3
PHRASE = 4
SENTENCE = 5
```

说明：

`DATETIME` 仅在解析器已经返回 Python `datetime`、`date` 或 `time` 对象时使用。

`NUMERIC_STR` 用于数值类字符串，例如 `+25.3`、`2026/3/7`、`55%`。

`PHRASE` 是短语，`SENTENCE` 是长句。对 ASCII 文本，按空白和标点切分，但不按 `-`、`_` 切分；分段数超过 1 时认为是长句。对非 ASCII 文本，去空白后字符数超过 8 时认为是长句。

## 配置

使用 `GuessOptions` 调整阈值和采样参数：

```python
from guess_sheet_headers import GuessOptions, do_guess

options = GuessOptions(
    match_threshold=0.9,
    col_type_threshold=0.3,
    min_sample_rows=10,
)

result = do_guess(rows, options)
```

## 限制

这是面向常见结构化表格的猜测算法，不是完整 Excel 理解引擎。它优先保持简单、可解释和稳定。

已知弱点包括：样本过小、数据行很稀疏、列类型高度混杂、一个 sheet 中存在多个无关表格、表格前有很长说明块，以及稀疏分组表头与数据区画像高度相似的情况。

## 开发

在本目录运行测试：

```bash
python -m unittest discover -s tests
```

## 许可证

MIT License。详见 [LICENSE](LICENSE)。
