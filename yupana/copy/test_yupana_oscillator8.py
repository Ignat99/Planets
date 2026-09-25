"""
Unit tests for yupana_oscillator module.
46 tests across 11 test classes.
"""

import unittest
import math
import os
import tempfile
from fractions import Fraction

from yupana_oscillator import (
    generate_sine_on_triangular_grid,
    generate_sine_fraction,
    count_operations_per_step,
    generate_two_loop_sine_yupana,
    compare_with_math_sine,
    export_oscillator_csv,
    export_two_loop_csv,
    export_oscillator_spice,
    triangular_grid_sequence,
    oscillator_to_yupana_bottom_row,
    two_loop_to_yupana_bottom_row,
    moon_sign_pattern,
    sun_sign_pattern,
)


class TestBasicNCO(unittest.TestCase):
    """Базовый одноконтурный NCO."""

    def test_initial_state(self):
        results = generate_sine_on_triangular_grid(1)
        n, T, S = results[0]
        self.assertEqual(n, 1)
        self.assertEqual(T, 1)
        self.assertEqual(S, 100000)

    def test_amplitude_default(self):
        results = generate_sine_on_triangular_grid(1)
        self.assertEqual(results[0][2], 100000)

    def test_custom_amplitude(self):
        results = generate_sine_on_triangular_grid(1, amplitude=50000)
        self.assertEqual(results[0][2], 50000)

    def test_steps_count(self):
        results = generate_sine_on_triangular_grid(12)
        self.assertEqual(len(results), 12)

    def test_triangular_numbers(self):
        results = generate_sine_on_triangular_grid(5)
        Ts = [r[1] for r in results]
        self.assertEqual(Ts, [1, 3, 6, 10, 15])

    def test_steps_returned_correctly(self):
        results = generate_sine_on_triangular_grid(8)
        ns = [r[0] for r in results]
        self.assertEqual(ns, list(range(1, 9)))

    def test_zero_steps(self):
        results = generate_sine_on_triangular_grid(0)
        self.assertEqual(results, [])

    def test_sine_oscillates_with_shift4(self):
        """При shift=4 синус уходит в отрицательные за ~71 шагов."""
        results = generate_sine_on_triangular_grid(100, amplitude=100000, shift_bit=4)
        S_values = [r[2] for r in results]
        self.assertTrue(any(s > 0 for s in S_values))
        self.assertTrue(any(s < 0 for s in S_values))


class TestFractionNCO(unittest.TestCase):
    """NCO через Fraction для точной арифметики."""

    def test_fraction_initial(self):
        results = generate_sine_fraction(1)
        n, T, S = results[0]
        self.assertEqual(n, 1)
        self.assertEqual(T, 1)
        self.assertEqual(S, Fraction(100000))

    def test_fraction_exact(self):
        results = generate_sine_fraction(3)
        for _, _, S in results:
            self.assertIsInstance(S, Fraction)

    def test_fraction_close_to_int(self):
        """Fraction и int могут отличаться на 1 из-за округления >>."""
        int_results = generate_sine_on_triangular_grid(8)
        frac_results = generate_sine_fraction(8)
        for (n1, T1, S_int), (n2, T2, S_frac) in zip(int_results, frac_results):
            self.assertEqual(n1, n2)
            self.assertEqual(T1, T2)
            self.assertLessEqual(abs(S_int - int(S_frac)), 1)


class TestOperations(unittest.TestCase):
    """Подсчёт операций."""

    def test_no_multiplications(self):
        ops = count_operations_per_step()
        self.assertEqual(ops["multiplications"], 0)

    def test_no_divisions(self):
        ops = count_operations_per_step()
        self.assertEqual(ops["divisions"], 0)

    def test_addition_count(self):
        ops = count_operations_per_step()
        self.assertEqual(ops["additions_subtractions"], 3)

    def test_shift_count(self):
        ops = count_operations_per_step()
        self.assertEqual(ops["bitwise_shifts"], 2)


class TestTwoLoopNCO(unittest.TestCase):
    """Двухконтурный NCO: Луна + Солнце."""

    def test_two_loop_steps(self):
        results = generate_two_loop_sine_yupana(24)
        self.assertEqual(len(results), 24)

    def test_two_loop_fields(self):
        results = generate_two_loop_sine_yupana(5)
        for entry in results:
            self.assertEqual(len(entry), 5)

    def test_moon_sun_initial(self):
        results = generate_two_loop_sine_yupana(1)
        n, T, S_m, S_s, S_tot = results[0]
        self.assertEqual(n, 1)
        self.assertEqual(T, 1)
        self.assertEqual(S_m, 100000)
        self.assertEqual(S_s, 25000)
        self.assertEqual(S_tot, 125000)

    def test_total_equals_sum(self):
        results = generate_two_loop_sine_yupana(16)
        for _, _, S_m, S_s, S_tot in results:
            self.assertEqual(S_tot, S_m + S_s)

    def test_sun_amplitude_smaller(self):
        results = generate_two_loop_sine_yupana(1)
        _, _, S_m, S_s, _ = results[0]
        self.assertLess(abs(S_s), abs(S_m))

    def test_triangular_grid_shared(self):
        results = generate_two_loop_sine_yupana(5)
        Ts = [r[1] for r in results]
        self.assertEqual(Ts, [1, 3, 6, 10, 15])


class TestCompareWithMathSine(unittest.TestCase):
    """Сравнение с math.sin."""

    def test_comparison_returns_tuples(self):
        comparisons = compare_with_math_sine(5)
        self.assertEqual(len(comparisons), 5)
        for entry in comparisons:
            self.assertEqual(len(entry), 6)

    def test_math_sine_correct(self):
        comparisons = compare_with_math_sine(4)
        self.assertAlmostEqual(comparisons[0][4], 1.0, places=10)
        self.assertAlmostEqual(comparisons[1][4], 0.0, places=10)
        self.assertAlmostEqual(comparisons[2][4], -1.0, places=10)

    def test_error_non_negative(self):
        comparisons = compare_with_math_sine(12)
        for _, _, _, _, _, err in comparisons:
            self.assertGreaterEqual(err, 0)


class TestCSVExport(unittest.TestCase):
    """Экспорт CSV."""

    def test_export_single_loop(self):
        results = generate_sine_on_triangular_grid(5)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_oscillator_csv(results, fname)
            self.assertTrue(os.path.exists(fname))
            with open(fname, 'r') as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 6)
        finally:
            os.unlink(fname)

    def test_export_two_loop(self):
        results = generate_two_loop_sine_yupana(8)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_two_loop_csv(results, fname)
            self.assertTrue(os.path.exists(fname))
            with open(fname, 'r') as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 9)
        finally:
            os.unlink(fname)

    def test_csv_header_single(self):
        results = generate_sine_on_triangular_grid(2)
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_oscillator_csv(results, fname)
            with open(fname, 'r') as f:
                header = f.readline().strip()
            self.assertIn('step_n', header)
            self.assertIn('triangular_T', header)
            self.assertIn('sine_S', header)
        finally:
            os.unlink(fname)


class TestSPICEExport(unittest.TestCase):
    """Экспорт SPICE."""

    def test_spice_file_created(self):
        with tempfile.NamedTemporaryFile(suffix='.spice', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_oscillator_spice(fname)
            self.assertTrue(os.path.exists(fname))
            with open(fname, 'r') as f:
                content = f.read()
            self.assertIn('.subckt', content)
            self.assertIn('.ends', content)
            self.assertIn('yupana_osc', content)
        finally:
            os.unlink(fname)

    def test_spice_has_amplitude(self):
        with tempfile.NamedTemporaryFile(suffix='.spice', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_oscillator_spice(fname, amplitude=50000)
            with open(fname, 'r') as f:
                content = f.read()
            self.assertIn('50000', content)
        finally:
            os.unlink(fname)

    def test_spice_has_divisor(self):
        with tempfile.NamedTemporaryFile(suffix='.spice', delete=False, mode='w') as f:
            fname = f.name
        try:
            export_oscillator_spice(fname, shift_bit=6)
            with open(fname, 'r') as f:
                content = f.read()
            self.assertIn('64', content)
        finally:
            os.unlink(fname)


class TestYupanaIntegration(unittest.TestCase):
    """Интеграция с эмулятором юпаны."""

    def test_triangular_grid_sequence(self):
        seq = triangular_grid_sequence(5)
        self.assertEqual(seq, [1, 3, 6, 10, 15])

    def test_triangular_grid_single(self):
        seq = triangular_grid_sequence(1)
        self.assertEqual(seq, [1])

    def test_oscillator_bottom_row_length(self):
        row = oscillator_to_yupana_bottom_row(steps=9)
        self.assertEqual(len(row), 9)

    def test_oscillator_bottom_row_values(self):
        row = oscillator_to_yupana_bottom_row(steps=3)
        self.assertEqual(row[0], 100000)

    def test_two_loop_bottom_row_length(self):
        row = two_loop_to_yupana_bottom_row(steps=9)
        self.assertEqual(len(row), 9)

    def test_two_loop_bottom_row_initial(self):
        row = two_loop_to_yupana_bottom_row(steps=1)
        self.assertEqual(row[0], 125000)


class TestSignPatterns(unittest.TestCase):
    """Знаковые паттерны Луны и Солнца."""

    def test_moon_pattern_length(self):
        pattern = moon_sign_pattern(16)
        self.assertEqual(len(pattern), 16)

    def test_moon_period_4(self):
        """Период Луны = 4 шага: +, --, ++, --."""
        pattern = moon_sign_pattern(8)
        self.assertEqual(pattern[0:4], ['+', '-', '-', '+'])
        self.assertEqual(pattern[4:8], ['+', '-', '-', '+'])

    def test_sun_pattern_length(self):
        pattern = sun_sign_pattern(32)
        self.assertEqual(len(pattern), 32)

    def test_sun_period_16(self):
        """Период Солнца = 16 шагов: 7+, 8-, 1+, 8-, 1+ ..."""
        pattern = sun_sign_pattern(32)
        self.assertTrue(all(c == '+' for c in pattern[0:7]))
        self.assertTrue(all(c == '-' for c in pattern[7:15]))
        self.assertTrue(all(c == '+' for c in pattern[15:23]))
        self.assertTrue(all(c == '-' for c in pattern[23:31]))

    def test_moon_starts_positive(self):
        pattern = moon_sign_pattern(1)
        self.assertEqual(pattern[0], '+')

    def test_sun_starts_positive(self):
        pattern = sun_sign_pattern(1)
        self.assertEqual(pattern[0], '+')


class TestEdgeCases(unittest.TestCase):
    """Граничные случаи."""

    def test_large_steps(self):
        results = generate_sine_on_triangular_grid(1000)
        self.assertEqual(len(results), 1000)

    def test_large_two_loop(self):
        results = generate_two_loop_sine_yupana(500)
        self.assertEqual(len(results), 500)

    def test_amplitude_one(self):
        results = generate_sine_on_triangular_grid(4, amplitude=1)
        self.assertEqual(len(results), 4)

    def test_negative_amplitude(self):
        results = generate_sine_on_triangular_grid(4, amplitude=-100000)
        self.assertEqual(len(results), 4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
