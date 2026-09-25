"""
yupana_lattice.py
Метод умножения «в 4 клетки» (решётка / джелозия) на юпане.
4 клетки 2×2, каждая делится по диагонали:
  верхний треугольник = десятки (белые камешки)
  нижний треугольник = единицы (чёрные камешки)

Связь с 3×3 юпаной: 4 клетки × 2 треугольника = 8 полуклеток,
что соответствует 8 внешним клеткам 3×3 юпаны (без центра).
"""

from typing import List, Tuple, Dict
import copy


# ============================================================
# Section 1: LatticeCell — клетка с диагональным делением
# ============================================================

class LatticeCell:
    """Клетка решётки: верх=десятки(белые), низ=единицы(чёрные)."""
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.upper = 0  # десятки → белые камешки
        self.lower = 0  # единицы → чёрные камешки

    @property
    def product(self) -> int:
        return self.upper * 10 + self.lower

    def set_product(self, val: int, base: int = 10):
        self.upper = val // base
        self.lower = val % base

    def reset(self):
        self.upper = 0
        self.lower = 0

    def __repr__(self):
        return f"LatticeCell(r={self.row},c={self.col},U={self.upper},L={self.lower})"

    def __eq__(self, other):
        if isinstance(other, LatticeCell):
            return self.upper == other.upper and self.lower == other.lower
        return False


# ============================================================
# Section 2: LatticeGrid — сетка 2×2
# ============================================================

class LatticeGrid:
    """Сетка 2×2 для метода решётки."""
    def __init__(self, base: int = 10):
        self.base = base
        self.cells: Dict[Tuple[int,int], LatticeCell] = {}
        for r in range(2):
            for c in range(2):
                self.cells[(r, c)] = LatticeCell(r, c)
        self.a_lo = 0
        self.a_hi = 0
        self.b_lo = 0
        self.b_hi = 0

    def reset(self):
        for cell in self.cells.values():
            cell.reset()
        self.a_lo = self.a_hi = self.b_lo = self.b_hi = 0

    def fill(self, a: int, b: int):
        """Заполнить сетку произведениями."""
        self.reset()
        self.a_lo = a % self.base
        self.a_hi = a // self.base
        self.b_lo = b % self.base
        self.b_hi = b // self.base

        # [0,0] = a_hi * b_hi
        self.cells[(0,0)].set_product(self.a_hi * self.b_hi, self.base)
        # [0,1] = a_hi * b_lo
        self.cells[(0,1)].set_product(self.a_hi * self.b_lo, self.base)
        # [1,0] = a_lo * b_hi
        self.cells[(1,0)].set_product(self.a_lo * self.b_hi, self.base)
        # [1,1] = a_lo * b_lo
        self.cells[(1,1)].set_product(self.a_lo * self.b_lo, self.base)

    def diagonal_sum(self) -> Tuple[int, int, int, int]:
        """Вернуть суммы по 4 диагоналям (справа налево)."""
        d0 = self.cells[(1,1)].lower
        d1 = self.cells[(1,1)].upper + self.cells[(0,1)].lower + self.cells[(1,0)].lower
        d2 = self.cells[(0,1)].upper + self.cells[(1,0)].upper + self.cells[(0,0)].lower
        d3 = self.cells[(0,0)].upper
        return d0, d1, d2, d3

    def read_result(self) -> int:
        """Сложить диагонали с переносом и вернуть результат."""
        d0, d1, d2, d3 = self.diagonal_sum()
        digits = [d0, d1, d2, d3]
        carry = 0
        result_digits = []
        for d in digits:
            total = d + carry
            result_digits.append(total % self.base)
            carry = total // self.base
        if carry > 0:
            result_digits.append(carry)

        result = 0
        for i, d in enumerate(result_digits):
            result += d * (self.base ** i)
        return result

    def copy(self) -> "LatticeGrid":
        g = LatticeGrid(self.base)
        g.a_lo = self.a_lo
        g.a_hi = self.a_hi
        g.b_lo = self.b_lo
        g.b_hi = self.b_hi
        for key, cell in self.cells.items():
            g.cells[key].upper = cell.upper
            g.cells[key].lower = cell.lower
        return g

    def __repr__(self):
        lines = []
        lines.append(f"       {self.a_hi}     {self.a_lo}")
        lines.append("    ┌───┬───┐")
        for r in range(2):
            parts = []
            for c in range(2):
                cell = self.cells[(r, c)]
                parts.append(f" {cell.upper}/{cell.lower} ")
            b_digit = self.b_hi if r == 0 else self.b_lo
            lines.append(f"    │{'│'.join(parts)}│ {b_digit}")
            if r == 0:
                lines.append("    ├───┼───┤")
        lines.append("    └───┴───┘")
        return "\n".join(lines)


# ============================================================
# Section 3: Главная функция — умножение методом решётки
# ============================================================

def lattice_multiply(a: int, b: int, base: int = 10, verbose: bool = False) -> int:
    """
    Умножение методом решётки (4 клетки / джелозия).
    Возвращает a * b.
    """
    grid = LatticeGrid(base)
    grid.fill(a, b)
    result = grid.read_result()

    if verbose:
        print(f"Умножение {a} × {b} методом решётки (4 клетки)")
        print(f"  A: ст={grid.a_hi}, мл={grid.a_lo} | B: ст={grid.b_hi}, мл={grid.b_lo}")
        print(f"  Клетки:")
        for (r,c), cell in sorted(grid.cells.items()):
            a_d = grid.a_hi if r == 0 else grid.a_lo
            b_d = grid.b_hi if c == 0 else grid.b_lo
            print(f"    [{r},{c}]: {a_d} × {b_d} = {cell.product} → белые={cell.upper}, чёрные={cell.lower}")
        d0, d1, d2, d3 = grid.diagonal_sum()
        print(f"  Диагонали: d0={d0}, d1={d1}, d2={d2}, d3={d3}")
        print(f"  Результат: {result}")
        print(f"  Проверка: {a} × {b} = {a * b} → {'OK' if result == a * b else 'FAIL'}")

    return result


# ============================================================
# Section 4: Отображение на 3×3 юпану
# ============================================================

class Yupana3x3Cell:
    """Клетка 3×3 юпаны с белыми и чёрными камешками."""
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.white = 0  # верхний треугольник (десятки)
        self.black = 0  # нижний треугольник (единицы)

    @property
    def total(self) -> int:
        return self.white + self.black

    def reset(self):
        self.white = 0
        self.black = 0

    def __repr__(self):
        return f"[{self.white}W,{self.black}B]"

    def __eq__(self, other):
        if isinstance(other, Yupana3x3Cell):
            return self.white == other.white and self.black == other.black
        return False


class Yupana3x3:
    """3×3 юпана для отображения решётки."""
    def __init__(self):
        self.cells: Dict[Tuple[int,int], Yupana3x3Cell] = {}
        for r in range(1, 4):
            for c in range(1, 4):
                self.cells[(r, c)] = Yupana3x3Cell(r, c)

    def get(self, r: int, c: int) -> Yupana3x3Cell:
        return self.cells[(r, c)]

    def reset(self):
        for cell in self.cells.values():
            cell.reset()

    def copy(self) -> "Yupana3x3":
        y = Yupana3x3()
        for (r,c), cell in self.cells.items():
            y.cells[(r,c)].white = cell.white
            y.cells[(r,c)].black = cell.black
        return y

    def __repr__(self):
        lines = []
        for r in range(1, 4):
            parts = []
            for c in range(1, 4):
                cell = self.get(r, c)
                parts.append(f"[{cell.white}W,{cell.black}B]")
            lines.append(" ".join(parts))
        return "\n".join(lines)


def lattice_to_yupana3x3(a: int, b: int, base: int = 10) -> Yupana3x3:
    """
    Отобразить решётку 2×2 на 3×3 юпану.
    4 клетки × 2 треугольника = 8 полуклеток → 8 внешних клеток 3×3.

    Маппинг:
      Lattice [0,0] upper → [1,1].white    (a_hi×b_hi, десятки)
      Lattice [0,0] lower → [1,1].black   (a_hi×b_hi, единицы)
      Lattice [0,1] upper → [1,3].white    (a_hi×b_lo, десятки)
      Lattice [0,1] lower → [1,3].black   (a_hi×b_lo, единицы)
      Lattice [1,0] upper → [3,1].white    (a_lo×b_hi, десятки)
      Lattice [1,0] lower → [3,1].black   (a_lo×b_hi, единицы)
      Lattice [1,1] upper → [3,3].white    (a_lo×b_lo, десятки)
      Lattice [1,1] lower → [3,3].black   (a_lo×b_lo, единицы)

    Средние клетки — операнды:
      [1,2] = a_lo (белые), [3,2] = a_hi (белые)
      [2,1] = b_lo (чёрные), [2,3] = b_hi (чёрные)
    Центр [2,2] — сумма средних диагоналей.
    """
    yupana = Yupana3x3()
    grid = LatticeGrid(base)
    grid.fill(a, b)

    a_lo, a_hi = grid.a_lo, grid.a_hi
    b_lo, b_hi = grid.b_lo, grid.b_hi

    # Операнды в средние клетки
    yupana.get(1, 2).white = a_lo
    yupana.get(3, 2).white = a_hi
    yupana.get(2, 1).black = b_lo
    yupana.get(2, 3).black = b_hi

    # Произведения в угловые клетки
    mapping = [
        ((0,0), (1,1)),  # a_hi × b_hi
        ((0,1), (1,3)),  # a_hi × b_lo
        ((1,0), (3,1)),  # a_lo × b_hi
        ((1,1), (3,3)),  # a_lo × b_lo
    ]

    for (lr, lc), (yr, yc) in mapping:
        yupana.get(yr, yc).white = grid.cells[(lr, lc)].upper
        yupana.get(yr, yc).black = grid.cells[(lr, lc)].lower

    # Центр — сумма средних диагоналей решётки
    d0, d1, d2, d3 = grid.diagonal_sum()
    yupana.get(2, 2).white = d1  # средняя диагональ 1
    yupana.get(2, 2).black = d2  # средняя диагональ 2

    return yupana


def yupana3x3_read_result(yupana: Yupana3x3, base: int = 10) -> int:
    """Считать результат с 3×3 юпаны по диагоналям."""
    # Диагонали решётки → клетки юпаны:
    # d0 = [3,3].black (младший разряд)
    # d1 = [3,3].white + [1,3].black + [3,1].black
    # d2 = [1,3].white + [3,1].white + [1,1].black
    # d3 = [1,1].white (старший разряд)

    d0 = yupana.get(3, 3).black
    d1 = yupana.get(3, 3).white + yupana.get(1, 3).black + yupana.get(3, 1).black
    d2 = yupana.get(1, 3).white + yupana.get(3, 1).white + yupana.get(1, 1).black
    d3 = yupana.get(1, 1).white

    digits = [d0, d1, d2, d3]
    carry = 0
    result_digits = []
    for d in digits:
        total = d + carry
        result_digits.append(total % base)
        carry = total // base
    if carry > 0:
        result_digits.append(carry)

    result = 0
    for i, d in enumerate(result_digits):
        result += d * (base ** i)
    return result


# ============================================================
# Section 5: Две юпаны — левая (работа), правая (результат)
# ============================================================

def lattice_multiply_two_yupanas(a: int, b: int, base: int = 10) -> Tuple[int, Yupana3x3, Yupana3x3]:
    """
    Левая юпана — рабочая (раскладка решётки).
    Правая юпана — хранение результата по разрядам.
    """
    work = lattice_to_yupana3x3(a, b, base)
    result = yupana3x3_read_result(work, base)

    # Правая юпана — результат по разрядам
    store = Yupana3x3()
    lo = result % base
    mid = (result // base) % base
    hi = (result // (base * base)) % base
    extra = result // (base * base * base)

    # Результат по диагонали: [3,3]=мл, [2,2]=средн, [1,1]=ст
    store.get(3, 3).white = lo
    store.get(2, 2).white = mid
    store.get(1, 1).white = hi
    if extra > 0:
        store.get(1, 3).white = extra

    return result, work, store


# ============================================================
# Section 6: Визуализация
# ============================================================

def visualize_lattice(a: int, b: int, base: int = 10) -> str:
    """Текстовая визуализация решётки 2×2 с диагоналями."""
    grid = LatticeGrid(base)
    grid.fill(a, b)
    a_hi, a_lo = grid.a_hi, grid.a_lo
    b_hi, b_lo = grid.b_hi, grid.b_lo

    lines = []
    lines.append(f"       {a_hi}     {a_lo}")
    lines.append("    ┌───┬───┐")
    for r in range(2):
        parts = []
        for c in range(2):
            cell = grid.cells[(r, c)]
            parts.append(f" {cell.upper}/{cell.lower} ")
        b_digit = b_hi if r == 0 else b_lo
        lines.append(f"    │{'│'.join(parts)}│ {b_digit}")
        if r == 0:
            lines.append("    ├───┼───┤")
    lines.append("    └───┴───┘")
    lines.append("")

    d0, d1, d2, d3 = grid.diagonal_sum()
    lines.append(f"  Диагонали: {d3} | {d2} | {d1} | {d0}")

    result = grid.read_result()
    lines.append(f"  Результат: {result}")
    lines.append(f"  Проверка:  {a} × {b} = {a * b}")

    return "\n".join(lines)


def visualize_yupana3x3(yupana: Yupana3x3) -> str:
    """Текстовая визуализация 3×3 юпаны."""
    lines = []
    lines.append("    ┌─────────┬─────────┬─────────┐")
    for r in range(1, 4):
        parts = []
        for c in range(1, 4):
            cell = yupana.get(r, c)
            parts.append(f" {cell.white}W {cell.black}B ")
        lines.append(f"    │{'│'.join(parts)}│")
        if r < 3:
            lines.append("    ├─────────┼─────────┼─────────┤")
    lines.append("    └─────────┴─────────┴─────────┘")
    return "\n".join(lines)


# ============================================================
# Section 7: Эмулятор-интеграция
# ============================================================

def emulator_lattice_action(a: int, b: int, base: int = 10) -> Dict:
    """
    Действие эмулятора: умножение методом решётки.
    Возвращает состояние левой и правой юпаны + результат.
    """
    result, work, store = lattice_multiply_two_yupanas(a, b, base)

    return {
        "action": "lattice_multiply",
        "operands": {"a": a, "b": b},
        "base": base,
        "left_yupana": {
            "cells": {
                f"{r},{c}": {
                    "white": work.get(r, c).white,
                    "black": work.get(r, c).black,
                }
                for r in range(1, 4) for c in range(1, 4)
            },
            "label": "Рабочая (решётка)"
        },
        "right_yupana": {
            "cells": {
                f"{r},{c}": {
                    "white": store.get(r, c).white,
                    "black": store.get(r, c).black,
                }
                for r in range(1, 4) for c in range(1, 4)
            },
            "label": "Результат"
        },
        "result": result,
        "correct": result == a * b,
    }


# ============================================================
# Section 8: Тесты
# ============================================================

def _run_tests():
    passed = 0
    failed = 0
    errors = []

    def check(name, got, expected):
        nonlocal passed, failed
        if got == expected:
            passed += 1
        else:
            failed += 1
            errors.append(f"{name}: expected {expected}, got {got}")

    # --- LatticeCell ---
    c = LatticeCell(0, 0)
    c.set_product(12)
    check("cell_upper", c.upper, 1)
    check("cell_lower", c.lower, 2)
    check("cell_product", c.product, 12)
    c.set_product(5)
    check("cell_upper_5", c.upper, 0)
    check("cell_lower_5", c.lower, 5)
    c.reset()
    check("cell_reset", c.upper + c.lower, 0)

    # --- LatticeGrid ---
    g = LatticeGrid()
    g.fill(23, 41)
    check("grid_a_lo", g.a_lo, 3)
    check("grid_a_hi", g.a_hi, 2)
    check("grid_b_lo", g.b_lo, 1)
    check("grid_b_hi", g.b_hi, 4)
    check("grid_00", g.cells[(0,0)].product, 8)    # 2×4
    check("grid_01", g.cells[(0,1)].product, 2)    # 2×1
    check("grid_10", g.cells[(1,0)].product, 12)   # 3×4
    check("grid_11", g.cells[(1,1)].product, 3)    # 3×1

    d0, d1, d2, d3 = g.diagonal_sum()
    check("diag_d0", d0, 3)
    check("diag_d1", d1, 2 + 2 + 0)  # upper[1,1] + lower[0,1] + lower[1,0] = 0+2+0
    check("diag_d2", d2, 0 + 1 + 8)  # upper[0,1] + upper[1,0] + lower[0,0] = 0+1+8
    check("diag_d3", d3, 0)          # upper[0,0]

    check("grid_result", g.read_result(), 943)

    # --- lattice_multiply ---
    check("mul_23x41", lattice_multiply(23, 41), 943)
    check("mul_11x22", lattice_multiply(11, 22), 242)
    check("mul_99x99", lattice_multiply(99, 99), 9801)
    check("mul_10x10", lattice_multiply(10, 10), 100)
    check("mul_0x5", lattice_multiply(0, 5), 0)
    check("mul_5x0", lattice_multiply(5, 0), 0)
    check("mul_1x1", lattice_multiply(1, 1), 1)
    check("mul_12x34", lattice_multiply(12, 34), 408)
    check("mul_56x78", lattice_multiply(56, 78), 4368)
    check("mul_50x50", lattice_multiply(50, 50), 2500)
    check("mul_1x99", lattice_multiply(1, 99), 99)
    check("mul_99x1", lattice_multiply(99, 1), 99)

    # --- Отображение на 3×3 юпану ---
    y = lattice_to_yupana3x3(23, 41)
    check("y3_ops_12_white", y.get(1, 2).white, 3)   # a_lo
    check("y3_ops_32_white", y.get(3, 2).white, 2)   # a_hi
    check("y3_ops_21_black", y.get(2, 1).black, 1)   # b_lo
    check("y3_ops_23_black", y.get(2, 3).black, 4)   # b_hi
    # [1,1] = a_hi × b_hi = 2×4 = 8 → upper=0, lower=8
    check("y3_11_white", y.get(1, 1).white, 0)
    check("y3_11_black", y.get(1, 1).black, 8)
    # [1,3] = a_hi × b_lo = 2×1 = 2 → upper=0, lower=2
    check("y3_13_white", y.get(1, 3).white, 0)
    check("y3_13_black", y.get(1, 3).black, 2)
    # [3,1] = a_lo × b_hi = 3×4 = 12 → upper=1, lower=2
    check("y3_31_white", y.get(3, 1).white, 1)
    check("y3_31_black", y.get(3, 1).black, 2)
    # [3,3] = a_lo × b_lo = 3×1 = 3 → upper=0, lower=3
    check("y3_33_white", y.get(3, 3).white, 0)
    check("y3_33_black", y.get(3, 3).black, 3)

    # Чтение результата с юпаны
    check("y3_read", yupana3x3_read_result(y), 943)

    # --- Две юпаны ---
    r, work, store = lattice_multiply_two_yupanas(23, 41)
    check("two_result", r, 943)
    check("two_store_lo", store.get(3, 3).white, 3)
    check("two_store_mid", store.get(2, 2).white, 4)
    check("two_store_hi", store.get(1, 1).white, 9)

    # --- Эмулятор action ---
    act = emulator_lattice_action(23, 41)
    check("emulator_result", act["result"], 943)
    check("emulator_correct", act["correct"], True)
    check("emulator_left_11w", act["left_yupana"]["cells"]["1,1"]["white"], 0)
    check("emulator_right_33w", act["right_yupana"]["cells"]["3,3"]["white"], 3)

    # --- Визуализация ---
    vis = visualize_lattice(23, 41)
    check("vis_contains", "943" in vis, True)

    # --- Yupana3x3 copy ---
    y2 = y.copy()
    y2.get(1, 1).white = 99
    check("copy_independent", y.get(1, 1).white, 0)

    # --- Полный перебор 0–99 × 0–99 ---
    sweep_fail = 0
    for i in range(100):
        for j in range(100):
            r = lattice_multiply(i, j)
            if r != i * j:
                sweep_fail += 1
                if sweep_fail <= 3:
                    errors.append(f"sweep {i}×{j}: expected {i*j}, got {r}")
    if sweep_fail == 0:
        passed += 1
    else:
        failed += sweep_fail

    # --- Полный перебор через 3×3 юпану ---
    y3_fail = 0
    for i in range(100):
        for j in range(100):
            y = lattice_to_yupana3x3(i, j)
            r = yupana3x3_read_result(y)
            if r != i * j:
                y3_fail += 1
                if y3_fail <= 3:
                    errors.append(f"y3_sweep {i}×{j}: expected {i*j}, got {r}")
    if y3_fail == 0:
        passed += 1
    else:
        failed += y3_fail

    # --- Результат ---
    print(f"\n{'='*50}")
    print(f"Тестов пройдено: {passed}")
    print(f"Тестов провалено: {failed}")
    if errors:
        print(f"\nОшибки:")
        for e in errors[:10]:
            print(f"  {e}")
    else:
        print("Все тесты зелёные!")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    _run_tests()
