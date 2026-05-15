from datetime import date
import unittest

from guess_sheet_headers import GuessOptions, do_guess, sample_indices, type_matrix


class GuessHeaderRangeTest(unittest.TestCase):
    def test_simple_header(self):
        rows = [["姓名", "金额", "日期"], ["张三", 10, date(2026, 1, 1)], ["李四", 20, date(2026, 1, 2)]]
        self.assertEqual(do_guess(rows), (0, 1))

    def test_leading_empty_rows_are_mapped_to_original_index(self):
        rows = [[None, ""], [], ["姓名", "金额"], ["张三", 10], ["李四", 20]]
        self.assertEqual(do_guess(rows), (0, 1))

    def test_column_profile_tolerates_row_variation(self):
        rows = [["编号", "摘要", "状态"], ["001", "短文本", "open"], ["002", "这是一段比较长的问题描述", "closed"]]
        self.assertEqual(do_guess(rows), (0, 1))

    def test_returns_through_best_text_density_header(self):
        rows = [
            ["标题", None, None, None],
            ["说明文字很多", None, None, None],
            ["序号", "姓名", "日期", "金额"],
        ]
        rows += [[i, f"姓名{i}", date(2026, 1, i), i * 10] for i in range(1, 9)]
        self.assertEqual(do_guess(rows), (0, 3))

    def test_keeps_middle_empty_columns_but_trims_edges(self):
        rows = [[None, "姓名", None, "金额", None], [None, "张三", None, 10, None], [None, "李四", None, 20, None]]
        self.assertEqual(type_matrix(rows), [[4, 0, 4], [4, 0, 1], [4, 0, 1]])

    def test_trims_bottom_empty_rows_before_sampling(self):
        rows = [["姓名", "金额"], ["张三", 10], ["李四", 20], [None, None], []]
        self.assertEqual(type_matrix(rows), [[4, 4], [4, 1], [4, 1]])

    def test_min_sample_rows(self):
        rows = [["姓名", "金额"], ["张三", 10], ["李四", 20]]
        self.assertEqual(do_guess(rows, GuessOptions(min_sample_rows=10)), (0, 0))

    def test_numeric_string_is_distinct_from_datetime(self):
        matrix = type_matrix([['2026/3/7', date(2026, 3, 7)]])
        self.assertEqual(matrix, [[3, 2]])

    def test_phrase_sentence_rule(self):
        rows = [["HistoryOrdersList", "I am ok", "GB44263-2024", "问题状态", "这是一段较长的中文表头"]]
        self.assertEqual(type_matrix(rows), [[4, 5, 4, 4, 5]])

    def test_sampling_limit(self):
        idx = sample_indices(1000, GuessOptions())
        self.assertLessEqual(len(idx), 200)
        self.assertEqual(idx[:3], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
