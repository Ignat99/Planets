"""
Yupana Oscillator — целочисленный генератор синуса на треугольной сетке.

Три регистра юпаны:
  Строка 1 (S) — значение синуса (аккумулятор)
  Строка 2 (V) — первая разность / скорость
  Строка 3 (T) — треугольные числа / сетка эклиптики

Арифметика: только сложение, вычитание, битовые сдвиги.
Аналог: диодный формирователь синуса из треугольного сигнала.

Двухконтурная версия:
  Контур Луны — быстрое колебание (сдвиг 6, /64)
  Контур Солнца — медленная аномалия M (сдвиг 9, /512)
"""

import math
from typing import List, Tuple


# ──────────────────────────────────────────────────────────────────────────────
# Section 1: Базовый генератор синуса на треугольной сетке
# ──────────────────────────────────────────────────────────────────────────────

def generate_sine_on_triangular_grid(
    steps: int,
    amplitude: int = 100000,
    shift_bit: int = 6
) -> List[Tuple[int, int, int]]:
    """
    Вычисление дискретного синуса в точках треугольного ряда (3-я строка Юпаны).
    Расчёт идёт через суммы и разности разностных регистров.

    Параметры:
      steps     — количество шагов
      amplitude — начальная амплитуда (значение V при n=0)
      shift_bit — битовый сдвиг масштабирования (6 = деление на 64)

    Возвращает: список кортежей (n, T, S)
      n — номер шага
      T — треугольное число (сетка эклиптики)
      S — значение синуса
    """
    S = 0            # Регистр синуса (Строка 1)
    V = amplitude    # Регистр скорости (Строка 2)
    T = 0            # Регистр треугольных чисел (Строка 3)

    results = []

    for n in range(1, steps + 1):
        # 1. Шаг по сетке эклиптики: T_n = n(n+1)/2
        T = T + n

        # 2. Знаковый флаг: попарное переключение ++, --, ++, -- ...
        is_positive = ((n >> 1) & 1) == 0

        # 3. Перенос разностей между регистрами
        delta = S >> shift_bit

        if is_positive:
            V = V - delta
        else:
            V = V + delta

        S = S + V

        results.append((n, T, S))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Section 2: Подсчёт операций
# ──────────────────────────────────────────────────────────────────────────────

def count_operations_per_step() -> dict:
    """
    Подсчёт арифметических и логических операций на один шаг.

    На каждый шаг:
      - T = T + n                           → 1 сложение
      - (n >> 1) & 1                        → 1 сдвиг, 1 И, 1 сравнение
      - delta = S >> shift_bit              → 1 сдвиг
      - V = V ± delta                       → 1 сложение/вычитание
      - S = S + V                           → 1 сложение

    Итого: 3 сложения/вычитания, 2 сдвига, 1 И, 1 сравнение.
    """
    return {
        "additions_subtractions": 3,
        "bitwise_shifts": 2,
        "bitwise_and": 1,
        "comparisons": 1,
        "total_ops": 7,
        "multiplications": 0,
        "divisions": 0,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Section 3: Двухконтурный генератор (Луна + Солнце)
# ──────────────────────────────────────────────────────────────────────────────

def generate_two_loop_sine_yupana(
    steps: int,
    amplitude: int = 100000,
    shift_moon: int = 6,
    shift_sun: int = 9,
    sun_amplitude_div: int = 2
) -> List[Tuple[int, int, int, int, int]]:
    """
    Разностный алгоритм в стиле Юпаны с двумя независимыми контурами.

    1-й контур (Луна): быстрое колебание, сдвиг shift_moon (по умолчанию /64)
    2-й контур (Солнце): медленная аномалия M, сдвиг shift_sun (по умолчанию /512)
      Знак Солнца переключается каждые 8 шагов (сдвиг индекса на 3 бита).

    Параметры:
      steps           — количество шагов
      amplitude       — начальная амплитуда лунного контура
      shift_moon      — битовый сдвиг для лунной волны (6 = /64)
      shift_sun       — битовый сдвиг для солнечной волны (9 = /512)
      sun_amplitude_div — делитель начальной амплитуды солнца (2 = amplitude/4)

    Возвращает: список кортежей (n, T, S_moon, S_sun, S_total)
    """
    # === КОНТУР ЛУНЫ (Быстрый регистр) ===
    S_moon = 0
    V_moon = amplitude
    T = 0

    # === КОНТУР СОЛНЦА (Медленный регистр для аномалии M) ===
    S_sun = 0
    V_sun = amplitude >> sun_amplitude_div

    results = []

    for n in range(1, steps + 1):
        # --- Шаг 1: Сетка эклиптики ---
        T = T + n

        # --- Шаг 2: Контур Луны (быстрое переключение: каждые 2 шага) ---
        moon_positive = ((n >> 1) & 1) == 0
        delta_moon = S_moon >> shift_moon

        if moon_positive:
            V_moon = V_moon - delta_moon
        else:
            V_moon = V_moon + delta_moon

        S_moon = S_moon + V_moon

        # --- Шаг 3: Контур Солнца (медленное переключение: каждые 8 шагов) ---
        sun_positive = ((n >> 3) & 1) == 0
        delta_sun = S_sun >> shift_sun

        if sun_positive:
            V_sun = V_sun - delta_sun
        else:
            V_sun = V_sun + delta_sun

        S_sun = S_sun + V_sun

        # --- Шаг 4: Слияние двух контуров ---
        S_total = S_moon + S_sun

        results.append((n, T, S_moon, S_sun, S_total))

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Section 4: Сравнение с математическим синусом
# ──────────────────────────────────────────────────────────────────────────────

def compare_with_math_sine(
    steps: int,
    amplitude: int = 100000,
    shift_bit: int = 6
) -> List[Tuple[int, int, float, int, float]]:
    """
    Сравнение целочисленного синуса юпаны с math.sin.

    Возвращает: (n, T, sin_math, S_yupana, error_pct)
    """
    results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)

    comparison = []
    for n, T, S in results:
        # Нормализация: период синуса юпаны ~ 8 шагов (4 положительных + 4 отрицательных)
        sin_math = amplitude * math.sin(2 * math.pi * n / 8)
        if sin_math != 0:
            error_pct = abs((S - sin_math) / sin_math) * 100
        else:
            error_pct = 0.0 if S == 0 else float('inf')
        comparison.append((n, T, sin_math, S, error_pct))

    return comparison


# ──────────────────────────────────────────────────────────────────────────────
# Section 5: Экспорт в CSV
# ──────────────────────────────────────────────────────────────────────────────

def export_oscillator_csv(
    steps: int,
    amplitude: int = 100000,
    shift_bit: int = 6,
    filepath: str = None
) -> str:
    """
    Экспорт таблицы синуса в CSV.
    Если filepath задан — сохраняет в файл, иначе возвращает строку.
    """
    results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)

    lines = ["n,T,S"]
    for n, T, S in results:
        lines.append(f"{n},{T},{S}")

    csv = "\n".join(lines)

    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv)

    return csv


def export_two_loop_csv(
    steps: int,
    amplitude: int = 100000,
    shift_moon: int = 6,
    shift_sun: int = 9,
    filepath: str = None
) -> str:
    """
    Экспорт двухконтурной таблицы в CSV.
    """
    results = generate_two_loop_sine_yupana(steps, amplitude, shift_moon, shift_sun)

    lines = ["n,T,S_moon,S_sun,S_total"]
    for n, T, S_m, S_s, S_tot in results:
        lines.append(f"{n},{T},{S_m},{S_s},{S_tot}")

    csv = "\n".join(lines)

    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv)

    return csv


# ──────────────────────────────────────────────────────────────────────────────
# Section 6: SPICE-экспорт (NCO как поведенческая модель)
# ──────────────────────────────────────────────────────────────────────────────

def export_oscillator_spice(
    steps: int = 32,
    amplitude: int = 100000,
    shift_bit: int = 6,
    filepath: str = None
) -> str:
    """
    Экспорт осциллятора как SPICE поведенческой модели (B-источники).

    Модель: 3 регистра (S, V, T) с дискретным шагом.
    Аналог: цифровой NCO с треугольной сеткой.
    """
    lines = [
        "* Yupana Oscillator — NCO on triangular grid",
        f"* Amplitude={amplitude}, Shift={shift_bit} (/{1 << shift_bit})",
        "* Registers: S (sine), V (velocity), T (triangular grid)",
        ".subckt yupana_osc n_S n_V n_T n_clk",
        "",
        "* Discrete-time registers (clocked)",
        f"B_S n_S 0 V=V(n_S) + V(n_V)",
        f"B_V n_V 0 V={amplitude} - (V(n_S) >> {shift_bit}) * sign(n)",
        f"B_T n_T 0 V=V(n_T) + n",
        "",
        ".ends yupana_osc",
        "",
        "* Testbench",
        "X1 n_S n_V n_T n_clk yupana_osc",
        "Vclk n_clk 0 PULSE(0 1 0 1n 1n 1n 2n)",
        ".tran 2n 64n",
        ".end",
    ]

    spice = "\n".join(lines)

    if filepath:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(spice)

    return spice


# ──────────────────────────────────────────────────────────────────────────────
# Section 7: Интеграция с yupana_math
# ──────────────────────────────────────────────────────────────────────────────

def triangular_grid_sequence(length: int) -> List[int]:
    """
    Возвращает последовательность треугольных чисел T_1, T_2, ..., T_length.
    Это сетка эклиптики — третья строка юпаны.
    """
    return [n * (n + 1) // 2 for n in range(1, length + 1)]


def oscillator_to_yupana_bottom_row(
    steps: int,
    amplitude: int = 100000,
    shift_bit: int = 6
) -> List[int]:
    """
    Возвращает значения синуса (регистр S) — для отображения в нижней строке юпаны.
    """
    results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
    return [S for _, _, S in results]


# ──────────────────────────────────────────────────────────────────────────────
# Самопроверка
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Базовый осциллятор (12 шагов) ===")
    table = generate_sine_on_triangular_grid(12)
    print(f"{'n':>4} | {'T':>6} | {'S':>8}")
    print("-" * 25)
    for n, T, S in table:
        print(f"{n:>4} | {T:>6} | {S:>8}")

    print("\n=== Операций на шаг ===")
    print(count_operations_per_step())

    print("\n=== Двухконтурный (24 шага) ===")
    table2 = generate_two_loop_sine_yupana(24)
    print(f"{'n':>4} | {'T':>6} | {'Moon':>8} | {'Sun':>8} | {'Total':>8}")
    print("-" * 45)
    for n, T, S_m, S_s, S_tot in table2:
        print(f"{n:>4} | {T:>6} | {S_m:>8} | {S_s:>8} | {S_tot:>8}")

    print("\n=== Сравнение с math.sin ===")
    comp = compare_with_math_sine(16)
    print(f"{'n':>4} | {'sin_math':>10} | {'S_yupana':>10} | {'err%':>8}")
    print("-" * 40)
    for n, T, sm, sy, ep in comp:
        print(f"{n:>4} | {sm:>10.1f} | {sy:>10} | {ep:>8.2f}")

    print("\n=== SPICE ===")
    print(export_oscillator_spice()[:200])
