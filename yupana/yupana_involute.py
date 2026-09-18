"""
yupana_involute.py
Библиотека методов для юпаны на основе геометрической
интерпретации ряда Тейлора sin(x) через инволюты окружности.

Видео: https://www.youtube.com/watch?v=x09IsbVZeXo
Ключевая идея: каждый член ряда sin(x) = x - x^3/3! + x^5/5! - ...
это длина последовательной инволюты единичной окружности.

Связи:
- Столбцы юпаны = инволюты Плотникова (c^0, c^1, c^2, ...)
- Белые камешки = положительный член (вверх), чёрные = отрицательный (вниз)
- n! = sum c(n,k) — факториал раскладывается через Стирлинга 1-го рода
- Деление на n! = распределение по n подциклам Стирлинга
"""

import math
from fractions import Fraction
from typing import List, Tuple, Dict


# ============================================================
# Section 1: Беззнаковые числа Стирлинга 1-го рода
# ============================================================

def stirling1_unsigned(n, k):
    """Беззнаковое число Стирлинга 1-го рода c(n,k)."""
    if k > n or k < 0:
        return 0
    if k == 0:
        return 1 if n == 0 else 0
    if k == n:
        return 1
    prev = [0] * (k + 1)
    prev[0] = 1
    for i in range(1, n + 1):
        curr = [0] * (k + 1)
        for j in range(1, min(i, k) + 1):
            curr[j] = (i - 1) * prev[j] + prev[j - 1]
        prev = curr
    return prev[k]


def factorial_stirling_decomposition(n):
    """n! = sum_{k=1}^{n} c(n,k). Возвращает [(k, c(n,k)), ...]."""
    return [(k, stirling1_unsigned(n, k)) for k in range(1, n + 1)
            if stirling1_unsigned(n, k) > 0]


# ============================================================
# Section 2: Члены ряда Тейлора как длины инволют
# ============================================================

def taylor_term_sin(x, n):
    """n-й член sin(x): (-1)^n * x^(2n+1) / (2n+1)!"""
    power = 2 * n + 1
    sign = (-1) ** n
    return Fraction(sign, 1) * Fraction(x) ** power / Fraction(math.factorial(power))


def taylor_term_cos(x, n):
    """n-й член cos(x): (-1)^n * x^(2n) / (2n)!"""
    power = 2 * n
    sign = (-1) ** n
    return Fraction(sign, 1) * Fraction(x) ** power / Fraction(math.factorial(power))


# ============================================================
# Section 3: Инволюта окружности
# ============================================================

def circle_involute_point(r, t):
    """Точка инволюты: x = r(cos t + t sin t), y = r(sin t - t cos t)."""
    return (r * (math.cos(t) + t * math.sin(t)),
            r * (math.sin(t) - t * math.cos(t)))


def circle_involute_arc_length(r, t):
    """Длина дуги инволюты: L = (r/2) * t^2."""
    return Fraction(r, 2) * Fraction(t) ** 2


# ============================================================
# Section 4: Модель инволюты на юпане
# ============================================================

class InvoluteYupanaCell:
    """Клетка юпаны, соответствующая одной инволюте."""
    def __init__(self, order, x_val):
        self.order = order
        self.power = 2 * order + 1
        self.sign = (-1) ** order
        self.fact = math.factorial(self.power)
        self.value = taylor_term_sin(x_val, order)
        self.stirling_decomp = factorial_stirling_decomposition(self.power)
        self.white = abs(self.value) if self.sign > 0 else Fraction(0)
        self.black = abs(self.value) if self.sign < 0 else Fraction(0)

    def __repr__(self):
        color = "белые" if self.sign > 0 else "чёрные"
        sign_str = "+" if self.sign > 0 else "-"
        return (f"Инволюта #{self.order}: {sign_str}x^{self.power}/{self.power}! "
                f"= {float(self.value):.8f} ({color})")


class InvoluteYupana:
    """Юпана инволют: каждый столбец = одна инволюта."""
    def __init__(self, x_val, n_terms=5):
        self.x_val = x_val
        self.n_terms = n_terms
        self.cells = [InvoluteYupanaCell(n, x_val) for n in range(n_terms)]

    def sin_approx(self):
        return sum(c.value for c in self.cells)

    def cos_approx(self):
        return sum(taylor_term_cos(self.x_val, n) for n in range(self.n_terms))

    def display(self):
        lines = [f"Юпана инволют для x = {self.x_val}",
                 f"Цель: sin({self.x_val}) = {math.sin(self.x_val):.10f}",
                 "Столбцы = последовательные инволюты:\n"]
        for cell in self.cells:
            lines.append(f"  Столбец {cell.order}: {cell}")
            if cell.stirling_decomp:
                s_str = " + ".join(f"c({cell.power},{k})={v}" for k, v in cell.stirling_decomp)
                lines.append(f"    {cell.power}! = {s_str} = {cell.fact}")
            lines.append(f"    Белые: {float(cell.white):.8f}, Чёрные: {float(cell.black):.8f}\n")
        approx = float(self.sin_approx())
        exact = math.sin(self.x_val)
        lines.append(f"Сумма: {approx:.10f}")
        lines.append(f"Точно: {exact:.10f}")
        lines.append(f"Ошибка: {abs(approx - exact):.2e}")
        return "\n".join(lines)


# ============================================================
# Section 5: Полигональная спираль
# ============================================================

def polygonal_spiral(x_val, n_terms=5):
    """Точки полигональной спирали инволют."""
    points = [(1.0, 0.0, -1)]
    cx, cy = 1.0, 0.0
    for n in range(n_terms):
        term = float(taylor_term_sin(x_val, n))
        angle = (math.pi / 2) * (n + 1)
        cx += term * math.cos(angle)
        cy += term * math.sin(angle)
        points.append((cx, cy, n))
    return points


def spiral_to_yupana(x_val, n_terms=5):
    """Отобразить спираль на юпану."""
    yupana = InvoluteYupana(x_val, n_terms)
    bottom_row = [float(c.value) for c in yupana.cells]
    columns = []
    for cell in yupana.cells:
        columns.append({
            "order": cell.order, "power": cell.power, "factorial": cell.fact,
            "sign": cell.sign, "value": float(cell.value),
            "stirling": [(k, v) for k, v in cell.stirling_decomp],
            "white": float(cell.white), "black": float(cell.black),
        })
    return {
        "x_val": x_val, "n_terms": n_terms, "bottom_row": bottom_row,
        "columns": columns,
        "sin_approx": float(yupana.sin_approx()),
        "cos_approx": float(yupana.cos_approx()),
        "sin_exact": math.sin(x_val), "cos_exact": math.cos(x_val),
    }


# ============================================================
# Section 6: Хуки для эмулятора
# ============================================================

def involute_to_yupana_bottom_row(x_val=1, n_terms=5, scale=100000):
    """Хук: значения инволют в нижнюю строку юпаны."""
    state = spiral_to_yupana(x_val, n_terms)
    bottom = [int(v * scale) for v in state["bottom_row"]]
    while len(bottom) < 5:
        bottom.append(0)
    return bottom[:5]


def involute_to_yupana_full(x_val=1, n_terms=5, scale=100000):
    """Полный хук: раскладка по столбцам и результат."""
    state = spiral_to_yupana(x_val, n_terms)
    columns_data = []
    for col in state["columns"]:
        columns_data.append({
            "order": col["order"],
            "white_scaled": int(col["white"] * scale),
            "black_scaled": int(col["black"] * scale),
            "stirling": col["stirling"],
        })
    sin_result = int(state["sin_approx"] * scale)
    cos_result = int(state["cos_approx"] * scale)
    info = {
        "action": "involute_sin", "x_val": x_val, "n_terms": n_terms,
        "scale": scale, "sin_approx": state["sin_approx"],
        "sin_exact": state["sin_exact"], "cos_approx": state["cos_approx"],
        "cos_exact": state["cos_exact"],
        "error": abs(state["sin_approx"] - state["sin_exact"]),
    }
    return columns_data, sin_result, cos_result, info


# ============================================================
# Section 7: Таблица соответствия инволют и столбцов
# ============================================================

def involute_column_mapping(max_order=5):
    """Столбец юпаны → инволюта Плотникова → член ряда."""
    mapping = []
    for n in range(max_order):
        power = 2 * n + 1
        fact = math.factorial(power)
        stirling = factorial_stirling_decomposition(power)
        mapping.append({
            "order": n, "column": n, "power": power, "factorial": fact,
            "stirling_sum": fact, "stirling_terms": len(stirling),
            "direction": "вверх" if n % 2 == 0 else "вниз",
            "involute": f"c^{n}", "sign": (-1) ** n,
        })
    return mapping


# ============================================================
# Section 8: Тесты
# ============================================================

def run_tests():
    passed = 0
    failed = 0
    errors = []

    def check(name, got, expected, tol=1e-9):
        nonlocal passed, failed
        if isinstance(got, float) or isinstance(expected, float):
            if abs(got - expected) < tol:
                passed += 1
            else:
                failed += 1
                errors.append(f"{name}: expected {expected}, got {got}")
        elif got == expected:
            passed += 1
        else:
            failed += 1
            errors.append(f"{name}: expected {expected}, got {got}")

    check("stir1_3_1", stirling1_unsigned(3, 1), 2)
    check("stir1_3_2", stirling1_unsigned(3, 2), 3)
    check("stir1_3_3", stirling1_unsigned(3, 3), 1)
    check("stir1_4_2", stirling1_unsigned(4, 2), 11)
    check("stir1_5_3", stirling1_unsigned(5, 3), 35)
    check("stir1_7_1", stirling1_unsigned(7, 1), 720)

    check("fact3", sum(v for _, v in factorial_stirling_decomposition(3)), 6)
    check("fact5", sum(v for _, v in factorial_stirling_decomposition(5)), 120)
    check("fact7", sum(v for _, v in factorial_stirling_decomposition(7)), 5040)

    check("ts0", float(taylor_term_sin(1, 0)), 1.0)
    check("ts1", float(taylor_term_sin(1, 1)), -1/6)
    check("ts2", float(taylor_term_sin(1, 2)), 1/120)
    check("tc0", float(taylor_term_cos(1, 0)), 1.0)
    check("tc1", float(taylor_term_cos(1, 1)), -1/2)

    for x in [0.1, 0.5, 1.0, 1.5, 2.0, math.pi/4, math.pi/3, math.pi/2]:
        yupana = InvoluteYupana(x, 8)
        check(f"sin_{x:.1f}", float(yupana.sin_approx()), math.sin(x), 1e-3)

    for x in [0.1, 0.5, 1.0, 1.5, 2.0, math.pi/4, math.pi/3]:
        yupana = InvoluteYupana(x, 8)
        check(f"cos_{x:.1f}", float(yupana.cos_approx()), math.cos(x), 1e-3)

    check("inv_len", float(circle_involute_arc_length(1, 1)), 0.5)
    bottom = involute_to_yupana_bottom_row(1, 5, 100000)
    check("hook_len", len(bottom), 5)

    print(f"\n{'='*50}")
    print(f"Тестов пройдено: {passed}")
    print(f"Тестов провалено: {failed}")
    if errors:
        for e in errors:
            print(f"  {e}")
    else:
        print("Все тесты зелёные!")
    print(f"{'='*50}")

    # Демонстрация
    print("\n" + "="*50)
    print("sin(π/6) = 0.5")
    print("="*50)
    print(InvoluteYupana(math.pi/6, 5).display())

    print("\n" + "="*50)
    print("Таблица: инволюты и столбцы юпаны")
    print("="*50)
    for m in involute_column_mapping(5):
        print(f"  Столбец {m['column']} | {m['involute']} | "
              f"x^{m['power']}/{m['power']}! | {m['direction']} | "
              f"Стирлинга: {m['stirling_terms']} членов")

    return failed == 0

if __name__ == "__main__":
    run_tests()
