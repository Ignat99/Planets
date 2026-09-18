"""
Unit-тесты для yupana_oscillator.py
Запуск: py -m unittest test_yupana_oscillator -v
"""

import unittest
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yupana_oscillator import (
    generate_sine_on_triangular_grid,
    count_operations_per_step,
    generate_two_loop_sine_yupana,
    compare_with_math_sine,
    triangular_grid_sequence,
    oscillator_to_yupana_bottom_row,
    export_oscillator_csv,
    export_two_loop_csv,
    export_oscillator_spice,
    generate_sine_on_triangular_grid_fraction,
)


class TestSingleLoopOscillator(unittest.TestCase):
    """Тесты базового одноконтурного осциллятора."""

    def test_initial_state(self):
        results = generate_sine_on_triangular_grid(steps=1, amplitude=100000)
        self.assertEqual(len(results), 1)
        n, T, S = results[0]
        self.assertEqual(n, 1)
        self.assertEqual(T, 1)
        self.assertEqual(S, 100000)

    def test_steps_count(self):
        for steps in [5, 10, 24, 50]:
            results = generate_sine_on_triangular_grid(steps=steps)
            self.assertEqual(len(results), steps)

    def test_triangular_numbers(self):
        results = generate_sine_on_triangular_grid(steps=20)
        for n, T, S in results:
            expected_T = n * (n + 1) // 2
            self.assertEqual(T, expected_T)

    def test_amplitude_affects_scale(self):
        r1 = generate_sine_on_triangular_grid(steps=12, amplitude=100000)
        r2 = generate_sine_on_triangular_grid(steps=12, amplitude=50000)
        for (n1, T1, S1), (n2, T2, S2) in zip(r1, r2):
            self.assertEqual(T1, T2)
            self.assertEqual(n1, n2)
            self.assertEqual(S1, 2 * S2)

    def test_shift_bit_affects_convergence(self):
        r_small_shift = generate_sine_on_triangular_grid(steps=12, amplitude=100000, shift_bit=4)
        r_large_shift = generate_sine_on_triangular_grid(steps=12, amplitude=100000, shift_bit=8)
        for (n1, T1, S1), (n2, T2, S2) in zip(r_small_shift, r_large_shift):
            self.assertGreaterEqual(abs(S2), abs(S1))

    def test_zero_amplitude(self):
        results = generate_sine_on_triangular_grid(steps=5, amplitude=0)
        for n, T, S in results:
            self.assertEqual(S, 0)

    def test_returns_list_of_tuples(self):
        results = generate_sine_on_triangular_grid(steps=3)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 3)

    def test_large_steps(self):
        results = generate_sine_on_triangular_grid(steps=1000, amplitude=100000)
        self.assertEqual(len(results), 1000)
        for n, T, S in results:
            self.assertTrue(abs(S) < 10**9)

    def test_custom_shift_bit(self):
        for sb in [2, 4, 6, 8, 10, 12]:
            results = generate_sine_on_triangular_grid(steps=8, amplitude=100000, shift_bit=sb)
            self.assertEqual(len(results), 8)


class TestCountOperations(unittest.TestCase):

    def test_ops_structure(self):
        ops = count_operations_per_step()
        self.assertIsInstance(ops, dict)
        self.assertIn("additions_subtractions", ops)
        self.assertIn("bitwise_shifts", ops)
        self.assertIn("bitwise_and", ops)

    def test_ops_values(self):
        ops = count_operations_per_step()
        self.assertEqual(ops["additions_subtractions"], 3)
        self.assertEqual(ops["bitwise_shifts"], 2)
        self.assertEqual(ops["bitwise_and"], 1)

    def test_no_multiplications(self):
        ops = count_operations_per_step()
        for key in ops:
            self.assertNotIn("multiplication", key.lower())


class TestTwoLoopOscillator(unittest.TestCase):

    def test_basic_run(self):
        results = generate_two_loop_sine_yupana(steps=24)
        self.assertEqual(len(results), 24)

    def test_tuple_structure(self):
        results = generate_two_loop_sine_yupana(steps=3)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 5)

    def test_triangular_grid_in_two_loop(self):
        results = generate_two_loop_sine_yupana(steps=15)
        for n, T, S_m, S_s, S_tot in results:
            expected_T = n * (n + 1) // 2
            self.assertEqual(T, expected_T)

    def test_total_is_sum(self):
        results = generate_two_loop_sine_yupana(steps=24)
        for n, T, S_m, S_s, S_tot in results:
            self.assertEqual(S_tot, S_m + S_s)

    def test_moon_amplitude_larger(self):
        results = generate_two_loop_sine_yupana(steps=32, amplitude=100000)
        max_moon = max(abs(S_m) for _, _, S_m, _, _ in results)
        max_sun = max(abs(S_s) for _, _, _, S_s, _ in results)
        self.assertGreater(max_moon, max_sun)

    def test_sun_period_longer(self):
        results = generate_two_loop_sine_yupana(steps=64, amplitude=100000,
                                                 shift_moon=10, shift_sun=10)
        moon_signs = [1 if S_m >= 0 else -1 for _, _, S_m, _, _ in results]
        sun_signs = [1 if S_s >= 0 else -1 for _, _, _, S_s, _ in results]
        moon_crossings = sum(1 for i in range(1, len(moon_signs))
                           if moon_signs[i] != moon_signs[i-1])
        sun_crossings = sum(1 for i in range(1, len(sun_signs))
                          if sun_signs[i] != sun_signs[i-1])
        self.assertGreaterEqual(moon_crossings, sun_crossings)

    def test_custom_shifts(self):
        results = generate_two_loop_sine_yupana(steps=16, amplitude=100000,
                                                 shift_moon=4, shift_sun=7)
        self.assertEqual(len(results), 16)

    def test_custom_amplitude(self):
        r1 = generate_two_loop_sine_yupana(steps=16, amplitude=100000)
        r2 = generate_two_loop_sine_yupana(steps=16, amplitude=200000)
        for (_, _, S_m1, S_s1, _), (_, _, S_m2, S_s2, _) in zip(r1, r2):
            self.assertEqual(S_m2, 2 * S_m1)
            self.assertEqual(S_s2, 2 * S_s1)


class TestCompareWithMathSine(unittest.TestCase):

    def test_comparison_returns_list(self):
        results = compare_with_math_sine(steps=12, amplitude=100000)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 12)

    def test_comparison_structure(self):
        results = compare_with_math_sine(steps=3, amplitude=100000)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 4)

    def test_error_is_finite(self):
        results = compare_with_math_sine(steps=20, amplitude=100000)
        for n, S_yupana, S_math, error_pct in results:
            self.assertTrue(math.isfinite(error_pct))


class TestTriangularGridSequence(unittest.TestCase):

    def test_basic_sequence(self):
        seq = triangular_grid_sequence(length=10)
        expected = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55]
        self.assertEqual(seq, expected)

    def test_length(self):
        for length in [1, 5, 20, 100]:
            seq = triangular_grid_sequence(length=length)
            self.assertEqual(len(seq), length)

    def test_first_and_last(self):
        seq = triangular_grid_sequence(length=10)
        self.assertEqual(seq[0], 1)
        self.assertEqual(seq[9], 55)

    def test_empty(self):
        seq = triangular_grid_sequence(length=0)
        self.assertEqual(seq, [])


class TestOscillatorToYupanaBottomRow(unittest.TestCase):

    def test_returns_list(self):
        row = oscillator_to_yupana_bottom_row(steps=9, amplitude=100000)
        self.assertIsInstance(row, list)
        self.assertEqual(len(row), 9)

    def test_truncation(self):
        row = oscillator_to_yupana_bottom_row(steps=20, amplitude=100000, ncols=6)
        self.assertEqual(len(row), 6)

    def test_default_ncols(self):
        row = oscillator_to_yupana_bottom_row(steps=9, amplitude=100000)
        self.assertEqual(len(row), 9)

    def test_values_are_integers(self):
        row = oscillator_to_yupana_bottom_row(steps=9, amplitude=100000)
        for val in row:
            self.assertIsInstance(val, int)


class TestExportCSV(unittest.TestCase):

    def test_single_loop_csv(self):
        csv_str = export_oscillator_csv(steps=5, amplitude=100000)
        lines = csv_str.strip().split("\n")
        self.assertEqual(len(lines), 6)
        self.assertIn("n", lines[0])
        self.assertIn("T", lines[0])
        self.assertIn("S", lines[0])

    def test_two_loop_csv(self):
        csv_str = export_two_loop_csv(steps=5, amplitude=100000)
        lines = csv_str.strip().split("\n")
        self.assertEqual(len(lines), 6)
        self.assertIn("S_moon", lines[0])
        self.assertIn("S_sun", lines[0])
        self.assertIn("S_total", lines[0])


class TestExportSPICE(unittest.TestCase):

    def test_contains_subckt(self):
        spice = export_oscillator_spice(steps=8, amplitude=100000)
        self.assertIn(".subckt", spice)
        self.assertIn(".ends", spice)

    def test_contains_behavioral_sources(self):
        spice = export_oscillator_spice(steps=8, amplitude=100000)
        self.assertIn("B", spice)

    def test_contains_nodes(self):
        spice = export_oscillator_spice(steps=4, amplitude=100000)
        self.assertIn("n_s0", spice)
        self.assertIn("n_s3", spice)

    def test_amplitude_in_netlist(self):
        spice = export_oscillator_spice(steps=4, amplitude=99999)
        self.assertIn("99999", spice)


class TestFractionVersion(unittest.TestCase):

    def test_basic_run(self):
        results = generate_sine_on_triangular_grid_fraction(steps=5, amplitude=100000)
        self.assertEqual(len(results), 5)

    def test_exact_values(self):
        from fractions import Fraction
        results = generate_sine_on_triangular_grid_fraction(steps=3, amplitude=100000)
        for n, T, S in results:
            self.assertIsInstance(T, int)
            self.assertIsInstance(S, Fraction)

    def test_matches_integer_version(self):
        r_int = generate_sine_on_triangular_grid(steps=8, amplitude=100000, shift_bit=0)
        r_frac = generate_sine_on_triangular_grid_fraction(steps=8, amplitude=100000, shift_bit=0)
        for (n1, T1, S1), (n2, T2, S2) in zip(r_int, r_frac):
            self.assertEqual(T1, T2)
            self.assertEqual(S1, int(S2))


class TestSignPattern(unittest.TestCase):

    def test_moon_sign_period_4(self):
        pattern = []
        for n in range(1, 17):
            is_positive = ((n >> 1) & 1) == 0
            pattern.append("+" if is_positive else "-")
        expected = ["+", "-", "-", "+", "+", "-", "-", "+",
                     "+", "-", "-", "+", "+", "-", "-", "+"]
        self.assertEqual(pattern, expected)

    def test_sun_sign_period_16(self):
        pattern = []
        for n in range(1, 33):
            is_positive = ((n >> 3) & 1) == 0
            pattern.append("+" if is_positive else "-")
        expected = ["+"] * 8 + ["-"] * 8 + ["+"] * 8 + ["-"] * 8
        self.assertEqual(pattern, expected)

    def test_moon_4_signs_per_8_steps(self):
        signs = []
        for n in range(1, 9):
            is_positive = ((n >> 1) & 1) == 0
            signs.append(1 if is_positive else -1)
        crossings = sum(1 for i in range(1, len(signs))
                       if signs[i] != signs[i-1])
        self.assertEqual(crossings, 3)


class TestEdgeCases(unittest.TestCase):

    def test_steps_zero(self):
        results = generate_sine_on_triangular_grid(steps=0)
        self.assertEqual(results, [])

    def test_steps_one(self):
        results = generate_sine_on_triangular_grid(steps=1, amplitude=100000)
        self.assertEqual(len(results), 1)

    def test_two_loop_steps_zero(self):
        results = generate_two_loop_sine_yupana(steps=0)
        self.assertEqual(results, [])

    def test_negative_amplitude(self):
        r_pos = generate_sine_on_triangular_grid(steps=8, amplitude=100000)
        r_neg = generate_sine_on_triangular_grid(steps=8, amplitude=-100000)
        for (n1, T1, S1), (n2, T2, S2) in zip(r_pos, r_neg):
            self.assertEqual(T1, T2)
            self.assertEqual(S1, -S2)

    def test_very_large_steps(self):
        results = generate_sine_on_triangular_grid(steps=5000, amplitude=100000)
        self.assertEqual(len(results), 5000)


if __name__ == "__main__":
    unittest.main()
