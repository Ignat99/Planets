"""
Yupana Oscillator — целочисленный NCO на разностных регистрах юпаны.

Три регистра = три строки юпаны:
  Строка 1 (S) — значение синуса (аккумулятор)
  Строка 2 (V) — первая разность (скорость)
  Строка 3 (T) — треугольные числа (сетка эклиптики)

Два контура:
  Луна  — быстрый, сдвиг 6 (период 4 шага)
  Солнце — медленный, сдвиг 9 (период 16 шагов, аномалия M)
"""

import math
import csv
from fractions import Fraction
from typing import List, Tuple


# ── Section 1: Базовый NCO ─────────────────────────────────────────────────

def generate_sine_on_triangular_grid(steps: int, amplitude: int = 100000, shift_bit: int = 6):
    """
    Вычисление дискретного синуса в точках треугольного ряда.
    Расчёт через суммы и разности разностных регистров.
    shift_bit: битовый сдвиг для масштабирования (деление на 2^shift_bit).
               6 = деление на 64 (исходный алгоритм, слабая обратная связь).
               4 = деление на 16 (более сильная, период ~71 шага).
    """
    S = 0
    V = amplitude
    T = 0
    results = []
    for n in range(1, steps + 1):
        T = T + n
        is_positive = ((n >> 1) & 1) == 0
        delta = S >> shift_bit
        if is_positive:
            V = V - delta
        else:
            V = V + delta
        S = S + V
        results.append((n, T, S))
    return results


def generate_sine_fraction(steps: int, amplitude: Fraction = Fraction(100000), shift_bit: int = 6):
    """Та же генерация, но через Fraction для точной арифметики."""
    S = Fraction(0)
    V = amplitude
    T = Fraction(0)
    divisor = Fraction(1 << shift_bit)
    results = []
    for n in range(1, steps + 1):
        T = T + n
        is_positive = ((n >> 1) & 1) == 0
        delta = S / divisor
        if is_positive:
            V = V - delta
        else:
            V = V + delta
        S = S + V
        results.append((n, int(T), S))
    return results


# ── Section 2: Подсчёт операций ─────────────────────────────────────────────

def count_operations_per_step():
    """Количество арифметических операций на один шаг."""
    return {
        "additions_subtractions": 3,
        "bitwise_shifts": 2,
        "bitwise_and": 1,
        "multiplications": 0,
        "divisions": 0,
    }


# ── Section 3: Двухконтурный NCO ────────────────────────────────────────────

def generate_two_loop_sine_yupana(steps: int, amplitude: int = 100000,
                                  shift_moon: int = 6, shift_sun: int = 9):
    """
    Двухконтурный разностный алгоритм.
    1-й контур: Луна (быстрый, сдвиг shift_moon, период 4)
    2-й контур: Солнце (медленный, сдвиг shift_sun, период 16)
    """
    S_moon = 0
    V_moon = amplitude
    T = 0
    
    S_sun = 0
    V_sun = amplitude >> 2
    
    results = []
    for n in range(1, steps + 1):
        T = T + n
        
        # Контур Луны
        moon_positive = ((n >> 1) & 1) == 0
        delta_moon = S_moon >> shift_moon
        if moon_positive:
            V_moon = V_moon - delta_moon
        else:
            V_moon = V_moon + delta_moon
        S_moon = S_moon + V_moon
        
        # Контур Солнца
        sun_positive = ((n >> 3) & 1) == 0
        delta_sun = S_sun >> shift_sun
        if sun_positive:
            V_sun = V_sun - delta_sun
        else:
            V_sun = V_sun + delta_sun
        S_sun = S_sun + V_sun
        
        S_total = S_moon + S_sun
        results.append((n, T, S_moon, S_sun, S_total))
    
    return results


# ── Section 4: Сравнение с math.sin ─────────────────────────────────────────

def compare_with_math_sine(steps: int, amplitude: int = 100000, shift_bit: int = 6):
    """Сравнение целочисленного NCO с math.sin."""
    results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
    comparisons = []
    for n, T, S in results:
        normalized = S / amplitude
        math_val = math.sin(n * math.pi / 2)
        error = abs(normalized - math_val)
        comparisons.append((n, T, S, normalized, math_val, error))
    return comparisons


# ── Section 5: Экспорт CSV ──────────────────────────────────────────────────

def export_oscillator_csv(results, filename):
    """Экспорт одноконтурного осциллятора в CSV."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['step_n', 'triangular_T', 'sine_S'])
        for n, T, S in results:
            writer.writerow([n, T, S])


def export_two_loop_csv(results, filename):
    """Экспорт двухконтурного осциллятора в CSV."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['step_n', 'grid_T', 'moon_S', 'sun_S', 'total_S'])
        for n, T, S_m, S_s, S_tot in results:
            writer.writerow([n, T, S_m, S_s, S_tot])


# ── Section 6: Экспорт SPICE ─────────────────────────────────────────────────

def export_oscillator_spice(filename, amplitude=100000, shift_bit=6):
    """Экспорт NCO как SPICE .subckt с поведенческими B-источниками."""
    divisor = 1 << shift_bit
    code = f"""* Yupana Oscillator NCO
* Amplitude: {amplitude}, Shift: {shift_bit} (divisor: {divisor})
.subckt yupana_osc n_clk n_sine n_grid 0
.param AMP={amplitude}
.param DIV={divisor}
BSINE n_sine 0 V=V(n_sine_int)
BGRID n_grid 0 V=V(n_grid_int)
BVEL n_vel 0 V=V(n_vel_int)
BSINT n_sine_int 0 I=V(n_sine)
BVELINT n_vel_int 0 I=V(n_vel) - V(n_sine)/{divisor}
BGRIDINT n_grid_int 0 I=V(n_grid) + 1
.ends
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    return filename


# ── Section 7: Интеграция с эмулятором юпаны ─────────────────────────────────

def triangular_grid_sequence(n):
    """Возвращает треугольные числа T_1 .. T_n."""
    return [(k * (k + 1)) // 2 for k in range(1, n + 1)]


def oscillator_to_yupana_bottom_row(steps=9, amplitude=100000, shift_bit=6):
    """Возвращает значения синуса для нижней строки юпаны."""
    results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
    return [S for _, _, S in results]


def two_loop_to_yupana_bottom_row(steps=9, amplitude=100000, shift_bit_moon=6, shift_bit_sun=9):
    """Возвращает итоговые значения двухконтурного осциллятора для нижней строки."""
    results = generate_two_loop_sine_yupana(steps, amplitude, shift_bit_moon, shift_bit_sun)
    return [S_tot for _, _, _, _, S_tot in results]


# ── Section 8: Знаковые паттерны ─────────────────────────────────────────────

def moon_sign_pattern(steps):
    """Знаковый паттерн Луны: период 4 (+, --, ++, --)."""
    return ['+' if ((n >> 1) & 1) == 0 else '-' for n in range(1, steps + 1)]


def sun_sign_pattern(steps):
    """Знаковый паттерн Солнца: период 16."""
    return ['+' if ((n >> 3) & 1) == 0 else '-' for n in range(1, steps + 1)]


# ── Section 9: Самопроверка ──────────────────────────────────────────────────

if __name__ == '__main__':
    print("=== Одноконтурный NCO (12 шагов, shift=6) ===")
    table = generate_sine_on_triangular_grid(12)
    print(f"{'n':>4} {'T':>6} {'S':>10}")
    for n, T, S in table:
        print(f"{n:>4} {T:>6} {S:>10}")
    
    print("\n=== Двухконтурный NCO (24 шага) ===")
    table2 = generate_two_loop_sine_yupana(24)
    print(f"{'n':>4} {'T':>6} {'Moon':>10} {'Sun':>10} {'Total':>10}")
    for n, T, Sm, Ss, St in table2:
        print(f"{n:>4} {T:>6} {Sm:>10} {Ss:>10} {St:>10}")
    
    print("\n=== Операций на шаг ===")
    print(count_operations_per_step())
    
    print("\n=== Знаковый паттерн Луны (16) ===")
    print(' '.join(moon_sign_pattern(16)))
    print("\n=== Знаковый паттерн Солнца (32) ===")
    print(' '.join(sun_sign_pattern(32)))
