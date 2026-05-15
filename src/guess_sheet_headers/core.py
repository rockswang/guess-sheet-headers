from collections import Counter, namedtuple
from datetime import date, datetime, time
from numbers import Number
import re


# 类型值：0 empty, 1 number, 2 datetime, 3 numeric_str, 4 phrase, 5 sentence


class GuessOptions(namedtuple("GuessOptions", "head_rows middle_rows tail_rows max_sample_rows min_sample_rows col_type_threshold match_threshold default_header_rows", defaults=(100, 50, 50, 200, 0, 0.3, 0.9, 1))):
    __slots__ = ()


NUMERIC_STR = re.compile(r"^[\d\s+\-.,:/\\()%￥$€£#*=_~]+$")
ASCII_TEXT = re.compile(r"^[\s\x21-\x7e]+$")
EN_SPLIT = re.compile(r"[\s!\"#$%&'()*+,./:;<=>?@[\]\\^`{|}~]+")  # 不按 - _ 切割


def do_guess(rows, opt=None):
    opt = opt or GuessOptions()
    if not rows:
        return (0, 0)
    rn, cols = _bounds(rows)  # rn: 去掉底部全空行后的行数；cols: 去掉左右全空列后的列号
    if not rn or not cols:
        return (0, 0)

    # 先用裁剪后的有效范围采样并建立“数据区列类型画像”。
    idx = sample_indices(rn, opt)
    if len(idx) < opt.min_sample_rows:
        return (0, 0)
    smp = _prep(rows, idx, cols)  # smp: (原始行号列表, 保留列号列表, 类型矩阵)
    if not smp[2] or not smp[1]:
        return (0, 0)
    prof = _profile(smp[2], opt)  # prof: 列类型画像，每列一个 set
    if not any(prof):
        return (0, 0)

    # 在头部寻找疑似数据区起点，再回看其上方哪一行最像字段表头。
    n = min(rn, opt.head_rows if rn > opt.max_sample_rows else rn)
    head = _prep(rows, range(n), smp[1])
    if not head[2]:
        return (0, 0)
    for p, r in enumerate(head[2]):
        if _score(r, prof, opt) > opt.match_threshold:
            if p == 0:
                return (0, min(len(rows), opt.default_header_rows))
            return (0, _header_end(head[0][:p], head[2][:p]))
    return (0, 0)


def sample_indices(n, opt=None):
    opt = opt or GuessOptions()
    if n <= 0:
        return []
    if n <= opt.max_sample_rows:
        return list(range(n))
    mid = max(0, (n - opt.middle_rows) // 2)  # mid: 中部采样起始行
    idx = [*range(min(opt.head_rows, n)), *range(mid, min(n, mid + opt.middle_rows)), *range(max(0, n - opt.tail_rows), n)]
    return list(dict.fromkeys(idx))[: opt.max_sample_rows]


def type_matrix(rows, opt=None):
    opt = opt or GuessOptions()
    rn, cols = _bounds(rows)
    return _prep(rows, sample_indices(rn, opt), cols)[2] if rn and cols else []


def _bounds(rows):
    rn = len(rows)
    # 采样前只裁剪底部空行和左右边缘空列，避免尾部/边缘空白污染画像。
    while rn and not any(_typ(v) for v in rows[rn - 1]):
        rn -= 1
    w = max((len(r) for r in rows[:rn]), default=0)
    left, right = 0, w - 1
    while left <= right and all(_typ(row[left] if left < len(row) else None) == 0 for row in rows[:rn]):
        left += 1
    while right >= left and all(_typ(row[right] if right < len(row) else None) == 0 for row in rows[:rn]):
        right -= 1
    return rn, list(range(left, right + 1))


def _prep(rows, idx, cols):
    raw = [(i, rows[i]) for i in idx if 0 <= i < len(rows)]  # raw: (原始行号, 原始行数据)
    if not raw or not cols:
        return [], [], []
    return [i for i, _ in raw], cols, [[_typ(r[c] if c < len(r) else None) for c in cols] for _, r in raw]


def _profile(mat, opt):
    # 每列统计所有类型（包括 empty），超过阈值的最多前三类进入该列画像。
    return [{t for t, n in Counter(col).most_common(3) if n / len(col) > opt.col_type_threshold} for col in zip(*mat)]


def _score(row, prof, opt):
    s = n = 0  # s: 命中列数；n: 参与评分列数
    for v, ts in zip(row, prof):
        if not ts:
            continue
        n += 1
        s += v in ts
    return s / n if n else 0


def _header_end(idx, mat):
    # 在疑似表头区内取文本密度最高的行作为最后一行表头；并列取更靠近数据区的行。
    return max(zip(idx, mat), key=lambda x: (sum(v in (4, 5) for v in x[1]) / len(x[1]), x[0]))[0] + 1


def _typ(v):
    if v is None or str(v).strip() == "":
        return 0
    if isinstance(v, (datetime, date, time)):
        return 2
    if isinstance(v, Number) and not isinstance(v, bool):
        return 1
    s = str(v).strip()
    if NUMERIC_STR.fullmatch(s) and any(c.isdigit() for c in s):
        return 3
    if ASCII_TEXT.fullmatch(s):
        return 5 if len([p for p in EN_SPLIT.split(s) if p]) > 1 else 4
    return 5 if len("".join(s.split())) > 8 else 4
