"""
test_yupana_math.py — Unit-тесты для yupana_math.py
Запуск: python test_yupana_math.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math
from fractions import Fraction
from yupana_math import (
    stirling_first_kind, S_MAX,
    rassnos_matrix, stirling_matrix, diff_matrix, normalized_matrix,
    fibonacci_diagonal, a391838_diagonal,
    compute_a391838, a391838_sequence, a391838_normalized, a391838_to_float,
    verify_a391838,
    multiplicative_inverse, compositional_inverse,
    difference_triangle,
    plotnikov_9cell, plotnikov_maxwell_6cell,
    triangular_number, is_triangular, triangular_index,
    find_triangular_representation, a391838_triangular_indices,
    export_matrix_csv, export_sequence_json, export_spice_subcircuit,
    format_fraction, format_cell_display, matrix_to_display,
    self_test,
)


def run_test(name, func):
    try:
        result = func()
        if result:
            print(f"  OK:   {name}")
            return True
        else:
            print(f"  FAIL: {name}")
            return False
    except Exception as e:
        print(f"  FAIL: {name} -- {e}")
        return False


# ── Section 1: Stirling ───────────────────────────────────────────────────────

def test_stirling_basic():
    s = stirling_first_kind(5)
    return s[0][0] == 1 and s[1][1] == 1 and s[2][1] == 1 and s[3][1] == 2

def test_stirling_s51():
    return S_MAX[5][1] == 24

def test_stirling_s53():
    return S_MAX[5][3] == 35

def test_stirling_s44():
    return S_MAX[4][4] == 1

def test_stirling_s61():
    return S_MAX[6][1] == 120

def test_stirling_s10_5():
    return S_MAX[10][5] == 269325

def test_stirling_diagonal():
    return all(S_MAX[n][n] == 1 for n in range(19))

def test_stirling_first_col():
    return all(S_MAX[n][1] == math.factorial(n - 1) for n in range(1, 19))


# ── Section 2: Matrices ──────────────────────────────────────────────────────

def test_rassnos_identity():
    m = rassnos_matrix(5, 5)
    return all(m[n][0] == 1 for n in range(5))

def test_rassnos_pascal():
    m = rassnos_matrix(5, 5)
    return m[4][2] == 6

def test_stirling_matrix_basic():
    m = stirling_matrix(5, 5)
    return m[3][1] == 2 and m[3][2] == 3

def test_stirling_matrix_diag():
    m = stirling_matrix(6, 6)
    return m[5][5] == 1 and m[0][0] == 1

def test_diff_matrix_shift():
    m = diff_matrix(6, 6)
    return m[3][1] == Fraction(S_MAX[2][1], 3) and m[3][1] == Fraction(1, 3)

def test_diff_matrix_k0():
    """d(1,0) = s(0,0)/1 = 1; d(2,0) = s(1,0)/2 = 0."""
    m = diff_matrix(5, 5)
    return m[1][0] == Fraction(1) and m[2][0] == Fraction(0)

def test_diff_matrix_fraction():
    m = diff_matrix(5, 5)
    return m[4][2] == Fraction(S_MAX[3][2], 4)

def test_normalized_matrix():
    m = normalized_matrix(5, 5)
    return m[3][1] == Fraction(2, 6) and m[3][2] == Fraction(3, 6)

def test_normalized_k0():
    m = normalized_matrix(5, 5)
    return m[1][0] == Fraction(0)

def test_fibonacci_diagonal():
    values, hl = fibonacci_diagonal(6, 6)
    return values[3][0] == S_MAX[3][3] and values[3][1] == S_MAX[3][2]


# ── Section 3: A391838 ────────────────────────────────────────────────────────

def test_a391838_oeis():
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
    return a391838_sequence(9) == expected

def test_a391838_n0():
    return compute_a391838(0) == 1

def test_a391838_n1():
    return compute_a391838(1) == 1

def test_a391838_n2():
    return compute_a391838(2) == 2

def test_a391838_n3():
    return compute_a391838(3) == 9

def test_a391838_n4():
    return compute_a391838(4) == 72

def test_a391838_n5():
    return compute_a391838(5) == 760

def test_a391838_n6():
    return compute_a391838(6) == 9900

def test_a391838_n7():
    return compute_a391838(7) == 156240

def test_a391838_n8():
    return compute_a391838(8) == 2903040

def test_a391838_verify():
    return verify_a391838()

def test_a391838_normalized():
    norm = a391838_normalized(5)
    return norm[0] == 1 and norm[1] == 1 and norm[2] == 1 and norm[3] == Fraction(3, 2) and norm[4] == 3

def test_a391838_float():
    f = a391838_to_float(5)
    return abs(f[3] - 1.5) < 1e-10

def test_a391838_diagonal():
    values, hl = a391838_diagonal(6, 6)
    return values[2][0] == S_MAX[2][2] and values[4][1] == S_MAX[3][2]


# ── Section 4: Inversion ─────────────────────────────────────────────────────

def test_mult_inv_basic():
    b = multiplicative_inverse([1, 2])
    return b == [Fraction(1), Fraction(-2)]

def test_mult_inv_const():
    """Inverse of [1,1,1,1] (= 1/(1-x)) is [1,-1,0,0] (= 1-x)."""
    b = multiplicative_inverse([1, 1, 1, 1], 4)
    return b == [Fraction(1), Fraction(-1), Fraction(0), Fraction(0)]

def test_mult_inv_reciprocal():
    b = multiplicative_inverse([2])
    return b == [Fraction(1, 2)]


# ── Section 5: Difference triangle ──────────────────────────────────────────

def test_diff_triangle_basic():
    tri = difference_triangle([1, 3, 6, 10])
    return tri == [[1, 3, 6, 10], [2, 3, 4], [1, 1], [0]]

def test_diff_triangle_single():
    return difference_triangle([5]) == [[5]]

def test_diff_triangle_a391838():
    seq = a391838_sequence(5)
    tri = difference_triangle(seq)
    return len(tri) == 5 and tri[0] == [1, 1, 2, 9, 72]


# ── Section 6: Plotnikov ─────────────────────────────────────────────────────

def test_plotnikov_9cell():
    grid = plotnikov_9cell()
    return len(grid) == 3 and len(grid[0]) == 3 and grid[0][0][0] == "E"

def test_plotnikov_maxwell():
    grid = plotnikov_maxwell_6cell()
    return len(grid) == 2 and len(grid[0]) == 3 and "Faradey" in grid[0][0][1] or "Фарадей" in grid[0][0][1]


# ── Section 7: Triangular numbers ────────────────────────────────────────────

def test_tri_T0():
    return triangular_number(0) == 0

def test_tri_T1():
    return triangular_number(1) == 1

def test_tri_T5():
    return triangular_number(5) == 15

def test_tri_T10():
    return triangular_number(10) == 55

def test_tri_T100():
    return triangular_number(100) == 5050

def test_is_tri_yes():
    return is_triangular(15) and is_triangular(1) and is_triangular(55)

def test_is_tri_no():
    return not is_triangular(4) and not is_triangular(7) and not is_triangular(-1)

def test_tri_index():
    return triangular_index(15) == 5 and triangular_index(1) == 1 and triangular_index(55) == 10

def test_tri_index_none():
    return triangular_index(4) is None

def test_find_repr_single():
    return find_triangular_representation(15) == "T_5"

def test_find_repr_sum():
    return find_triangular_representation(9) == "T_3 + T_2"

def test_find_repr_a391838():
    reps = a391838_triangular_indices(5)
    return reps[0][2] == "T_1" and reps[2][2] == "T_1 + T_1"


# ── Section 8: Export ────────────────────────────────────────────────────────

def test_export_csv():
    m = stirling_matrix(3, 3)
    csv_str = export_matrix_csv(m)
    return "n" in csv_str and "1" in csv_str

def test_export_json():
    json_str = export_sequence_json([1, 2, 3])
    return '"sequence"' in json_str and '"length": 3' in json_str

def test_export_spice():
    m = stirling_matrix(3, 3)
    spice = export_spice_subcircuit(m, "test")
    return ".subckt test" in spice and ".ends" in spice


# ── Section 9: Display ───────────────────────────────────────────────────────

def test_format_frac_int():
    return format_fraction(Fraction(5)) == "5"

def test_format_frac_frac():
    return format_fraction(Fraction(1, 3)) == "1/3"

def test_format_cell_k0():
    return format_cell_display(5, 0, 0) == "5"

def test_format_cell_k2():
    return format_cell_display(3, 0, 2) == "3\u00B7x^2"

def test_format_cell_frac_k0():
    return format_cell_display(Fraction(3, 2), 0, 0) == "3/2"

def test_format_cell_frac_k1():
    return format_cell_display(Fraction(3, 2), 0, 1) == "3/2\u00B7x^1"

def test_format_cell_zero():
    return format_cell_display(0, 0, 0) == ""

def test_format_cell_float_k0():
    return format_cell_display(2.0, 0, 0) == "2"

def test_matrix_to_display():
    m = stirling_matrix(3, 3)
    d = matrix_to_display(m, 3, 3)
    return d[0][0] == "1" and d[1][1] == "1\u00B7x^1"


# ── Section 10: Self-test ─────────────────────────────────────────────────────

def test_self_test():
    results = self_test()
    return all(results.values())


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("stirling_basic", test_stirling_basic),
        ("stirling_s51", test_stirling_s51),
        ("stirling_s53", test_stirling_s53),
        ("stirling_s44", test_stirling_s44),
        ("stirling_s61", test_stirling_s61),
        ("stirling_s10_5", test_stirling_s10_5),
        ("stirling_diagonal", test_stirling_diagonal),
        ("stirling_first_col", test_stirling_first_col),
        ("rassnos_identity", test_rassnos_identity),
        ("rassnos_pascal", test_rassnos_pascal),
        ("stirling_matrix_basic", test_stirling_matrix_basic),
        ("stirling_matrix_diag", test_stirling_matrix_diag),
        ("diff_matrix_shift", test_diff_matrix_shift),
        ("diff_matrix_k0", test_diff_matrix_k0),
        ("diff_matrix_fraction", test_diff_matrix_fraction),
        ("normalized_matrix", test_normalized_matrix),
        ("normalized_k0", test_normalized_k0),
        ("fibonacci_diagonal", test_fibonacci_diagonal),
        ("a391838_oeis", test_a391838_oeis),
        ("a391838_n0", test_a391838_n0),
        ("a391838_n1", test_a391838_n1),
        ("a391838_n2", test_a391838_n2),
        ("a391838_n3", test_a391838_n3),
        ("a391838_n4", test_a391838_n4),
        ("a391838_n5", test_a391838_n5),
        ("a391838_n6", test_a391838_n6),
        ("a391838_n7", test_a391838_n7),
        ("a391838_n8", test_a391838_n8),
        ("a391838_verify", test_a391838_verify),
        ("a391838_normalized", test_a391838_normalized),
        ("a391838_float", test_a391838_float),
        ("a391838_diagonal", test_a391838_diagonal),
        ("mult_inv_basic", test_mult_inv_basic),
        ("mult_inv_const", test_mult_inv_const),
        ("mult_inv_reciprocal", test_mult_inv_reciprocal),
        ("diff_triangle_basic", test_diff_triangle_basic),
        ("diff_triangle_single", test_diff_triangle_single),
        ("diff_triangle_a391838", test_diff_triangle_a391838),
        ("plotnikov_9cell", test_plotnikov_9cell),
        ("plotnikov_maxwell", test_plotnikov_maxwell),
        ("tri_T0", test_tri_T0),
        ("tri_T1", test_tri_T1),
        ("tri_T5", test_tri_T5),
        ("tri_T10", test_tri_T10),
        ("tri_T100", test_tri_T100),
        ("is_tri_yes", test_is_tri_yes),
        ("is_tri_no", test_is_tri_no),
        ("tri_index", test_tri_index),
        ("tri_index_none", test_tri_index_none),
        ("find_repr_single", test_find_repr_single),
        ("find_repr_sum", test_find_repr_sum),
        ("find_repr_a391838", test_find_repr_a391838),
        ("export_csv", test_export_csv),
        ("export_json", test_export_json),
        ("export_spice", test_export_spice),
        ("format_frac_int", test_format_frac_int),
        ("format_frac_frac", test_format_frac_frac),
        ("format_cell_k0", test_format_cell_k0),
        ("format_cell_k2", test_format_cell_k2),
        ("format_cell_frac_k0", test_format_cell_frac_k0),
        ("format_cell_frac_k1", test_format_cell_frac_k1),
        ("format_cell_zero", test_format_cell_zero),
        ("format_cell_float_k0", test_format_cell_float_k0),
        ("matrix_to_display", test_matrix_to_display),
        ("self_test", test_self_test),
    ]

    passed = 0
    failed = 0
    for name, func in tests:
        if run_test(name, func):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"Total: {len(tests)}, Passed: {passed}, Failed: {failed}")
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"{failed} tests failed!")
        sys.exit(1)
