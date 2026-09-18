"""
test_yupana_math.py — Unit-тесты для yupana_math.

Запуск: python -m pytest test_yupana_math.py -v
Или:    python test_yupana_math.py
"""

import unittest
from fractions import Fraction
from yupana_math import (
    stirling_first_kind,
    rassnos_matrix,
    stirling_matrix,
    diff_matrix,
    normalized_matrix,
    fibonacci_diagonal,
    a391838_diagonal,
    compute_a391838,
    compute_a391838_sequence,
    verify_a391838,
    multiplicative_inverse,
    compositional_inverse,
    difference_triangle,
    plotnikov_9cell,
    plotnikov_maxwell_6cell,
    export_matrix_csv,
    export_sequence_json,
    export_spice_subcircuit,
    a391838_to_float,
    format_cell_display,
    get_matrix_values,
    S_MAX,
)


class TestStirling(unittest.TestCase):

    def test_s00(self):
        self.assertEqual(S_MAX[0][0], 1)

    def test_s11(self):
        self.assertEqual(S_MAX[1][1], 1)

    def test_s21(self):
        self.assertEqual(S_MAX[2][1], 1)  # s(2,1) = s(1,0) + 1*s(1,1) = 0 + 1

    def test_s22(self):
        self.assertEqual(S_MAX[2][2], 1)  # s(2,2) = s(1,1) + 1*s(1,2) = 1

    def test_s31(self):
        # s(3,1) = s(2,0) + 2*s(2,1) = 0 + 2*1 = 2
        self.assertEqual(S_MAX[3][1], 2)

    def test_s32(self):
        # s(3,2) = s(2,1) + 2*s(2,2) = 1 + 2*1 = 3
        self.assertEqual(S_MAX[3][2], 3)

    def test_s33(self):
        self.assertEqual(S_MAX[3][3], 1)

    def test_s41(self):
        # s(4,1) = s(3,0) + 3*s(3,1) = 0 + 3*2 = 6
        self.assertEqual(S_MAX[4][1], 6)

    def test_s44(self):
        self.assertEqual(S_MAX[4][4], 1)

    def test_recurrence(self):
        """Проверка рекуррентного соотношения s(n,k) = s(n-1,k-1) + (n-1)*s(n-1,k)"""
        for n in range(5, 18):
            for k in range(1, n + 1):
                expected = S_MAX[n - 1][k - 1] + (n - 1) * S_MAX[n - 1][k]
                self.assertEqual(S_MAX[n][k], expected,
                                 f"s({n},{k}) mismatch")

    def test_stirling_matrix_4x4(self):
        m = stirling_matrix(4, 4)
        self.assertEqual(m[0][0], 1)
        self.assertEqual(m[1][1], 1)
        self.assertEqual(m[2][1], 1)
        self.assertEqual(m[3][1], 2)
        self.assertEqual(m[3][2], 3)


class TestRassnos(unittest.TestCase):

    def test_pascal_triangle(self):
        m = rassnos_matrix(5, 5)
        self.assertEqual(m[0][0], 1)
        self.assertEqual(m[1][0], 1)
        self.assertEqual(m[1][1], 1)
        self.assertEqual(m[2][1], 2)
        self.assertEqual(m[3][1], 3)
        self.assertEqual(m[4][2], 6)

    def test_identity(self):
        """Диагональ = 1"""
        m = rassnos_matrix(6, 6)
        for n in range(6):
            self.assertEqual(m[n][0], 1)
            self.assertEqual(m[n][n], 1)


class TestDiff(unittest.TestCase):

    def test_diff_2x2(self):
        m = diff_matrix(2, 2)
        # n=0: нули
        self.assertEqual(m[0][0], Fraction(0))
        self.assertEqual(m[0][1], Fraction(0))
        # n=1: s(0,k)/1 = s(0,0) = 1
        self.assertEqual(m[1][0], Fraction(1))
        self.assertEqual(m[1][1], Fraction(0))

    def test_diff_4x4(self):
        m = diff_matrix(4, 4)
        # n=2: s(1,k)/2
        self.assertEqual(m[2][0], Fraction(0))  # s(1,0)/2 = 0
        self.assertEqual(m[2][1], Fraction(1, 2))  # s(1,1)/2 = 1/2
        # n=3: s(2,k)/3
        self.assertEqual(m[3][1], Fraction(1, 3))  # s(2,1)/3 = 1/3
        self.assertEqual(m[3][2], Fraction(1, 3))  # s(2,2)/3 = 1/3

    def test_diff_shifts_up(self):
        """Дифференцирование — переход вверх: s(n-1,k)/n, не s(n,k)/n"""
        m = diff_matrix(4, 4)
        # n=3, k=1: должно быть s(2,1)/3 = 1/3, а не s(3,1)/3 = 2/3
        self.assertEqual(m[3][1], Fraction(1, 3))
        self.assertNotEqual(m[3][1], Fraction(2, 3))


class TestNormalized(unittest.TestCase):

    def test_normalized_3x3(self):
        m = normalized_matrix(3, 3)
        # n=0: s(0,0)/0! = 1/1 = 1
        self.assertEqual(m[0][0], Fraction(1))
        # n=1: s(1,1)/1! = 1/1 = 1
        self.assertEqual(m[1][1], Fraction(1))
        # n=2: s(2,1)/2! = 1/2
        self.assertEqual(m[2][1], Fraction(1, 2))
        # n=2: s(2,2)/2! = 1/2
        self.assertEqual(m[2][2], Fraction(1, 2))


class TestFibonacciDiagonal(unittest.TestCase):

    def test_fibonacci_5x5(self):
        vals, hl = fibonacci_diagonal(5, 5)
        # n=0, k=0: s(0,0) = 1
        self.assertEqual(vals[0][0], 1)
        # n=1, k=0: s(1,1) = 1  (dk=1)
        self.assertEqual(vals[1][0], 1)
        # n=2, k=1: s(2,1) = 1  (dk=1)
        self.assertEqual(vals[2][1], 1)
        # n=3, k=1: s(3,2) = 3  (dk=2)
        self.assertEqual(vals[3][1], 3)

    def test_highlight(self):
        _, hl = fibonacci_diagonal(5, 5)
        self.assertTrue(len(hl) > 0)


class TestA391838Diagonal(unittest.TestCase):

    def test_diagonal_4x4(self):
        vals, hl = a391838_diagonal(4, 4)
        # n=0, k=0: s(0,0) = 1
        self.assertEqual(vals[0][0], 1)
        # n=2, k=1: s(1,0) = 0
        self.assertEqual(vals[2][1], 0)
        # n=3, k=0: s(3,3) = 1
        self.assertEqual(vals[3][0], 1)

    def test_highlight_not_empty(self):
        _, hl = a391838_diagonal(6, 6)
        self.assertTrue(len(hl) > 0)


class TestComputeA391838(unittest.TestCase):

    def test_a0(self):
        self.assertEqual(compute_a391838(0), 1)

    def test_a1(self):
        self.assertEqual(compute_a391838(1), 1)

    def test_a2(self):
        self.assertEqual(compute_a391838(2), 2)

    def test_a3(self):
        self.assertEqual(compute_a391838(3), 9)

    def test_a4(self):
        self.assertEqual(compute_a391838(4), 72)

    def test_a5(self):
        self.assertEqual(compute_a391838(5), 760)

    def test_a6(self):
        self.assertEqual(compute_a391838(6), 9900)

    def test_a7(self):
        self.assertEqual(compute_a391838(7), 156240)

    def test_a8(self):
        self.assertEqual(compute_a391838(8), 2903040)

    def test_full_sequence(self):
        expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
        actual = compute_a391838_sequence(8)
        self.assertEqual(actual, expected)

    def test_verify(self):
        self.assertTrue(verify_a391838())


class TestMultiplicativeInverse(unittest.TestCase):

    def test_inverse_of_identity(self):
        """Обращение [1, 0, 0, ...] = [1, 0, 0, ...]"""
        seq = [1, 0, 0, 0, 0]
        inv = multiplicative_inverse(seq)
        self.assertEqual(inv[0], Fraction(1))
        self.assertEqual(inv[1], Fraction(0))

    def test_inverse_of_geometric(self):
        """Обращение [1, 2, 4, 8, 16] = [1, -2, 0, 0, 0]"""
        seq = [1, 2, 4, 8, 16]
        inv = multiplicative_inverse(seq)
        self.assertEqual(inv[0], Fraction(1))
        self.assertEqual(inv[1], Fraction(-2))
        self.assertEqual(inv[2], Fraction(0))

    def test_inverse_product(self):
        """f * g = 1"""
        seq = [1, 3, 5, 7]
        inv = multiplicative_inverse(seq)
        # Проверяем свёртку: Σ a_k * b_{n-k} = δ_{n,0}
        for n in range(len(seq)):
            conv = sum(Fraction(seq[k]) * inv[n - k]
                       for k in range(n + 1) if k < len(seq) and n - k >= 0)
            if n == 0:
                self.assertEqual(conv, Fraction(1))
            else:
                self.assertEqual(conv, Fraction(0),
                                 f"Convolution at n={n} should be 0, got {conv}")


class TestCompositionalInverse(unittest.TestCase):

    def test_basic(self):
        seq = [0, 1, 2, 3, 4]
        inv = compositional_inverse(seq)
        self.assertEqual(inv[0], Fraction(0))
        self.assertEqual(inv[1], Fraction(1))


class TestDifferenceTriangle(unittest.TestCase):

    def test_simple(self):
        seq = [1, 3, 6, 10, 15]
        tri = difference_triangle(seq)
        self.assertEqual(tri[0], [1, 3, 6, 10, 15])
        self.assertEqual(tri[1], [2, 3, 4, 5])
        self.assertEqual(tri[2], [1, 1, 1])
        self.assertEqual(tri[3], [0, 0])

    def test_a391838_triangle(self):
        seq = [1, 1, 2, 9, 72, 760]
        tri = difference_triangle(seq)
        self.assertEqual(tri[0], [1, 1, 2, 9, 72, 760])
        self.assertEqual(tri[1], [0, 1, 7, 63, 688])

    def test_empty(self):
        self.assertEqual(difference_triangle([]), [])
        self.assertEqual(difference_triangle([1]), [[1]])


class TestPlotnikov(unittest.TestCase):

    def test_9cell(self):
        grid = plotnikov_9cell()
        self.assertEqual(len(grid), 3)
        self.assertEqual(len(grid[0]), 3)
        self.assertIn("L", grid[0][0])

    def test_maxwell_6cell(self):
        grid = plotnikov_maxwell_6cell()
        self.assertEqual(len(grid), 2)
        self.assertEqual(len(grid[0]), 3)
        self.assertIn("E", grid[0][0])


class TestExport(unittest.TestCase):

    def test_csv(self):
        m = stirling_matrix(4, 4)
        csv_str = export_matrix_csv(m, "stirling", 4)
        self.assertIn("row/col", csv_str)
        self.assertIn("0,1,2,3", csv_str)

    def test_json(self):
        seq = [1, 1, 2, 9, 72]
        json_str = export_sequence_json(seq, "a391838")
        self.assertIn('"sequence"', json_str)
        self.assertIn("1, 1, 2, 9, 72", json_str)

    def test_spice(self):
        m = stirling_matrix(3, 3)
        spice_str = export_spice_subcircuit(m, "test_circuit", 3)
        self.assertIn(".subckt", spice_str)
        self.assertIn(".ends", spice_str)

    def test_spice_skips_zeros(self):
        m = [[0, 0, 0], [0, 1, 0], [0, 0, 1]]
        spice_str = export_spice_subcircuit(m, "zeros_test", 3)
        # Нулевые элементы пропускаются
        self.assertNotIn("R0_0", spice_str)


class TestFormatCellDisplay(unittest.TestCase):

    def test_int_k0(self):
        self.assertEqual(format_cell_display(5, 0, 0), "5")

    def test_int_k2(self):
        self.assertEqual(format_cell_display(5, 0, 2), "5\u00B7x^2")

    def test_fraction_k0(self):
        self.assertEqual(format_cell_display(Fraction(1, 3), 0, 0), "1/3")

    def test_fraction_k2(self):
        self.assertEqual(format_cell_display(Fraction(1, 3), 0, 2), "1/3\u00B7x^2")

    def test_zero(self):
        self.assertEqual(format_cell_display(0, 0, 0), "")

    def test_float_int(self):
        self.assertEqual(format_cell_display(3.0, 0, 0), "3")


class TestGetMatrixValues(unittest.TestCase):

    def test_stirling(self):
        vals, hl = get_matrix_values("stirling", 4, 4)
        self.assertEqual(vals[0][0], 1)
        self.assertEqual(len(hl), 0)

    def test_rassnos(self):
        vals, hl = get_matrix_values("rassnos", 4, 4)
        self.assertEqual(vals[2][1], 2)

    def test_unknown_mode(self):
        vals, hl = get_matrix_values("unknown", 4, 4)
        self.assertEqual(vals[0][0], 1)


class TestA391838ToFloat(unittest.TestCase):

    def test_normalization(self):
        seq = [1, 1, 2, 9, 72]
        floats = a391838_to_float(seq)
        self.assertAlmostEqual(floats[0], 1.0)
        self.assertAlmostEqual(floats[1], 1.0)
        self.assertAlmostEqual(floats[2], 1.0)  # 2/2! = 1
        self.assertAlmostEqual(floats[3], 1.5)  # 9/3! = 1.5
        self.assertAlmostEqual(floats[4], 3.0)  # 72/4! = 3


if __name__ == "__main__":
    unittest.main(verbosity=2)
