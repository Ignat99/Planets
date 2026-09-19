"""
test_yupana.py
Юнит-тесты для yupana_core и yupana_lattice.
Запуск: python test_yupana.py
"""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yupana_core import (
    stirling_unsigned_first, stirling_second_kind_val,
    lift_columns, lower_columns,
    shift_rows_right, shift_rows_left,
    stirling_diagonal, stirling_diagonal_components,
    a391838_row, compute_a391838_sequence,
    transformation_journal,
)

from yupana_lattice import (
    emulator_lattice_action, emulator_lattice_action_old,
    emulator_inca_lattice_action,
    emulator_stirling_diagonal_action, emulator_a391838_action,
    emulator_column_lift_action, emulator_column_lower_action,
    emulator_row_shift_right_action, emulator_row_shift_left_action,
    export_journal_json, export_journal_text,
)

from fractions import Fraction

# ============================================================
# Тестовый фреймворк (минимальный)
# ============================================================

_tests_passed = 0
_tests_total = 0
_tests_failed = []

def check(name, actual, expected):
    global _tests_passed, _tests_total
    _tests_total += 1
    if actual == expected:
        _tests_passed += 1
    else:
        _tests_failed.append(f"FAIL: {name}: expected {expected}, got {actual}")
        print(f"  FAIL: {name}: expected {expected}, got {actual}")

def check_true(name, actual):
    global _tests_passed, _tests_total
    _tests_total += 1
    if actual:
        _tests_passed += 1
    else:
        _tests_failed.append(f"FAIL: {name}: expected True, got {actual}")
        print(f"  FAIL: {name}: expected True, got {actual}")


# ============================================================
# Тесты yupana_core
# ============================================================

def test_stirling_table():
    """Таблица беззнаковых чисел Стирлинга I рода."""
    c = stirling_unsigned_first(9)
    check("c(0,0)", c[0][0], 1)
    check("c(1,1)", c[1][1], 1)
    check("c(2,1)", c[2][1], 1)
    check("c(3,1)", c[3][1], 2)
    check("c(3,2)", c[3][2], 3)
    check("c(4,2)", c[4][2], 11)
    check("c(5,3)", c[5][3], 35)
    check("c(7,4)", c[7][4], 735)
    check("c(8,4)", c[8][4], 6769)
    check("c(9,4)", c[9][4], 67284)

    # Сумма строки n = n!
    for n in range(10):
        row_sum = sum(c[n])
        check(f"sum row {n} = {n}!", row_sum, math.factorial(n))


def test_stirling_second_kind():
    """Числа Стирлинга II рода."""
    check("S(0,0)", stirling_second_kind_val(0, 0), 1)
    check("S(1,1)", stirling_second_kind_val(1, 1), 1)
    check("S(3,2)", stirling_second_kind_val(3, 2), 3)
    check("S(4,2)", stirling_second_kind_val(4, 2), 7)
    check("S(5,3)", stirling_second_kind_val(5, 3), 25)
    check("S(0,1)", stirling_second_kind_val(0, 1), 0)


def test_lift_columns():
    """Действие 13: Поднятие столбцов."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)

    # lifted[r][k] = c(r+k, k)
    for r in range(size):
        for k in range(size):
            if r + k <= N:
                check(f"lifted[{r}][{k}]=c({r+k},{k})", lifted[r][k], c[r+k][k])

    # Строка 1 = треугольные числа
    row1 = [lifted[1][k] for k in range(10)]
    check("lift row1 = triangular", row1, [k*(k+1)//2 for k in range(10)])

    # Строка 0 = все единицы (c(k,k) = 1)
    row0 = [lifted[0][k] for k in range(10)]
    check("lift row0 = all 1s", row0, [1]*10)

    # Строка 2 = c(2+k, k)
    row2 = [lifted[2][k] for k in range(8)]
    check("lift row2", row2, [0, 2, 11, 35, 85, 175, 322, 546])


def test_lower_columns():
    """Действие 14: Опускание столбцов — обратное к поднятию."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    lowered = lower_columns(lifted, size, N)

    # lowered[n][k] = c(n, k)
    for n in range(size):
        for k in range(size):
            if n <= N:
                check(f"lowered[{n}][{k}]=c({n},{k})", lowered[n][k], c[n][k])


def test_roundtrip_lift_lower():
    """Round-trip: lift → lower = исходная таблица."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    lowered = lower_columns(lifted, size, N)

    for n in range(size):
        for k in range(size):
            if n <= N:
                check(f"round-trip lift/lower c({n},{k})", lowered[n][k], c[n][k])


def test_shift_rows_right():
    """Действие 15: Сдвиг строк вправо — верхнетреугольная матрица."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    tri = shift_rows_right(lifted, size)

    # triangular[r][c] = c(c, c-r) при c >= r
    for r in range(size):
        for col in range(size):
            if col >= r and col <= N:
                check(f"tri[{r}][{col}]=c({col},{col-r})", tri[r][col], c[col][col-r])
            elif col < r:
                check(f"tri[{r}][{col}]=0 (ниже диагонали)", tri[r][col], 0)

    # Нет отрицательных значений
    for r in range(size):
        for col in range(size):
            check_true(f"tri[{r}][{col}] >= 0", tri[r][col] >= 0)


def test_shift_rows_left():
    """Действие 16: Сдвиг строк влево — обратное к сдвигу вправо."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    tri = shift_rows_right(lifted, size)
    lifted_back = shift_rows_left(tri, size)

    # lifted_back[r][c] = lifted[r][c] — только для значений, помещающихся в сетку
    for r in range(size):
        for c in range(size):
            if r + c < size:
                check(f"shift_left[{r}][{c}]", lifted_back[r][c], lifted[r][c])


def test_full_roundtrip():
    """Полный round-trip: lift → shift_right → shift_left → lower = исходная."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    tri = shift_rows_right(lifted, size)
    lifted_back = shift_rows_left(tri, size)
    original = lower_columns(lifted_back, size, N)

    # Проверяем только значения, помещающиеся в size×size сетку
    for n in range(size):
        for k in range(size):
            if n <= N and (n - k) + k < size and k + (n - k) < size:
                # n-k = r, k = c в lifted; r+c = n < size — должно поместиться
                if n < size:
                    check(f"full round-trip c({n},{k})", original[n][k], c[n][k])


def test_stirling_diagonal():
    """Действие 11: Диональная формула."""
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040, 61943616]
    for n in range(10):
        result = stirling_diagonal(n)
        check(f"diag a({n})", result, expected[n])


def test_stirling_diagonal_components():
    """Проверка компонентов диагональной формулы."""
    comps = stirling_diagonal_components(4)
    # k=0: c(4,4)=1, k=1: c(3,2)=3, k=2: c(2,0)=0
    check("comp k=0 value", comps[0][1], 1)
    check("comp k=1 value", comps[1][1], 3)
    check("comp k=2 value", comps[2][1], 0)
    # Сумма компонентов = 72
    total = sum(c for _, _, c in comps)
    check("sum components n=4", total, 72)


def test_a391838():
    """Действие 12: A391838."""
    expected = [1, 6, 40, 336, 3456, 42240, 599040, 9676800, 175472640, 3530096640]
    for n in range(10):
        result = a391838_row(n)
        check(f"A391838 n={n}", result, expected[n])

    seq = compute_a391838_sequence(8)
    check("A391838 sequence", seq, expected[:8])


def test_transformation_journal():
    """Проверка журнала преобразований."""
    journal = transformation_journal()
    check("journal length", len(journal), 4)
    check("journal[0] этап", journal[0]["этап"], "Исходная таблица")
    check("journal[0] шаг_строки", journal[0]["шаг_строки"], -1)
    check("journal[0] шаг_столбца", journal[0]["шаг_столбца"], -2)
    check("journal[1] шаг_строки", journal[1]["шаг_строки"], 1)
    check("journal[1] шаг_столбца", journal[1]["шаг_столбца"], -2)
    check("journal[2] шаг_столбца", journal[2]["шаг_столбца"], -1)
    check("journal[3] шаг_столбца", journal[3]["шаг_столбца"], -1)

    # JSON экспорт
    json_str = export_journal_json()
    check_true("journal JSON not empty", len(json_str) > 10)

    # Текстовый экспорт
    text_str = export_journal_text()
    check_true("journal text not empty", len(text_str) > 10)
    check_true("journal text has этап", "Этап" in text_str)


# ============================================================
# Тесты yupana_lattice (адаптеры с анимацией)
# ============================================================

def test_lattice_multiply():
    """Умножение решёткой."""
    r = emulator_lattice_action(23, 41)
    check("mult 23x41", r["result"], 943)
    r = emulator_lattice_action(99, 99)
    check("mult 99x99", r["result"], 9801)

    r_old = emulator_lattice_action_old(23, 41)
    check("mult_old 23x41", r_old["result"], 943)


def test_inca_multiply():
    """Умножение инков с анимацией."""
    r = emulator_inca_lattice_action(12, 34)
    check("inca 12x34", r["result"], 408)
    check("inca steps count", len(r["steps"]), 5)


def test_emulator_diagonal():
    """Эмулятор действия 11 — диагональ Стирлинга."""
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040, 61943616]
    for n in range(10):
        r = emulator_stirling_diagonal_action(n)
        check(f"emulator diag n={n}", r["result"], expected[n])
        check_true(f"emulator diag steps n={n}", len(r["steps"]) > 0)
        # Проверка журнала в шагах
        for step in r["steps"]:
            if "journal" in step:
                check_true(f"emulator diag journal n={n}", "этап" in step["journal"])


def test_emulator_a391838():
    """Эмулятор действия 12 — A391838."""
    expected = [1, 6, 40, 336, 3456, 42240, 599040, 9676800]
    for n in range(8):
        r = emulator_a391838_action(n)
        check(f"emulator A391838 n={n}", r["result"], expected[n])


def test_emulator_column_lift():
    """Эмулятор действия 13 — поднятие столбцов."""
    r = emulator_column_lift_action(7)
    lifted = r["steps"][-1]["right"]
    row1 = [lifted.get((1, k), 0) for k in range(8)]
    check("emulator lift row1 = triangular", row1, [0, 1, 3, 6, 10, 15, 21, 28])
    check_true("emulator lift has steps", len(r["steps"]) > 0)
    # Проверка журнала
    for step in r["steps"]:
        if "journal" in step:
            check_true("emulator lift journal has этап", "этап" in step["journal"])
            check_true("emulator lift journal has шаг_строки", "шаг_строки" in step["journal"])
            check_true("emulator lift journal has шаг_столбца", "шаг_столбца" in step["journal"])


def test_emulator_column_lower():
    """Эмулятор действия 14 — опускание столбцов."""
    r = emulator_column_lower_action(7)
    lowered = r["steps"][-1]["right"]
    check("emulator lower[0][0]", lowered.get((0, 0), 0), 1)
    check("emulator lower[3][1]", lowered.get((3, 1), 0), 2)
    check("emulator lower[3][2]", lowered.get((3, 2), 0), 3)
    check("emulator lower[4][2]", lowered.get((4, 2), 0), 11)
    check_true("emulator lower has steps", len(r["steps"]) > 0)


def test_emulator_row_shift_right():
    """Эмулятор действия 15 — сдвиг строк вправо."""
    r = emulator_row_shift_right_action(7)
    tri = r["steps"][-1]["right"]

    # triangular[r][c] = c(c, c-r)
    N = 9
    c = stirling_unsigned_first(N)
    for row in range(8):
        for col in range(8):
            if col >= row and col <= N:
                expected = c[col][col - row]
                actual = tri.get((row, col), 0)
                if expected > 0:
                    check(f"emulator shift_right tri[{row}][{col}]", actual, expected)

    # Проверка: нет значений ниже диагонали
    for row in range(8):
        for col in range(8):
            if col < row:
                check(f"emulator shift_right below diag [{row}][{col}]", tri.get((row, col), 0), 0)

    # Проверка журнала
    for step in r["steps"]:
        if "journal" in step:
            check_true("emulator shift_right journal has этап", "этап" in step["journal"])
            check_true("emulator shift_right journal has шаг_столбца", "шаг_столбца" in step["journal"])


def test_emulator_row_shift_left():
    """Эмулятор действия 16 — сдвиг строк влево."""
    r = emulator_row_shift_left_action(7)
    lifted = r["steps"][-1]["right"]

    N = 9
    c = stirling_unsigned_first(N)
    for row in range(8):
        for col in range(8):
            if row + col <= N and row + col < 8 and c[row + col][col] > 0:
                check(f"emulator shift_left [{row}][{col}]", lifted.get((row, col), 0), c[row + col][col])

    check_true("emulator shift_left has steps", len(r["steps"]) > 0)


def test_emulator_full_roundtrip():
    """Полный round-trip через эмуляторы: 13 → 15 → 16 → 14."""
    r_lift = emulator_column_lift_action(7)
    lifted = r_lift["steps"][-1]["right"]

    r_shift_right = emulator_row_shift_right_action(7)
    tri = r_shift_right["steps"][-1]["right"]

    r_shift_left = emulator_row_shift_left_action(7)
    lifted_back = r_shift_left["steps"][-1]["right"]

    r_lower = emulator_column_lower_action(7)
    lowered = r_lower["steps"][-1]["right"]

    # Проверяем несколько ключевых значений
    N = 9
    c = stirling_unsigned_first(N)
    for n in range(8):
        for k in range(8):
            if k <= n and c[n][k] > 0:
                check(f"emulator full round-trip c({n},{k})", lowered.get((n, k), 0), c[n][k])


# ============================================================
# Property-based тесты
# ============================================================

def test_property_no_negative():
    """Все значения во всех таблицах неотрицательны."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    tri = shift_rows_right(lifted, size)
    lowered = lower_columns(lifted, size, N)

    for name, table in [("stirling", c), ("lifted", lifted), ("triangular", tri), ("lowered", lowered)]:
        for r in range(len(table)):
            for col in range(len(table[r])):
                check_true(f"{name}[{r}][{col}] >= 0", table[r][col] >= 0)


def test_property_triangular_upper():
    """Верхнетреугольная матрица: нули ниже диагонали."""
    N = 10
    c = stirling_unsigned_first(N)
    size = 10
    lifted = lift_columns(c, size, N)
    tri = shift_rows_right(lifted, size)

    for r in range(size):
        for col in range(size):
            if col < r:
                check(f"tri below diag [{r}][{col}]", tri[r][col], 0)


def test_property_lift_identity_row0():
    """Строка 0 поднятой таблицы = все единицы (c(k,k) = 1)."""
    N = 10
    c = stirling_unsigned_first(N)
    lifted = lift_columns(c, 10, N)
    check("lift row0 = [1]*10", lifted[0], [1]*10)


def test_property_journal_steps():
    """Журнал каждого шага содержит обязательные поля."""
    actions = [
        emulator_column_lift_action(5),
        emulator_column_lower_action(5),
        emulator_row_shift_right_action(5),
        emulator_row_shift_left_action(5),
    ]
    for i, r in enumerate(actions):
        for step in r["steps"]:
            if "journal" in step:
                j = step["journal"]
                check_true(f"action {i} journal has 'этап'", "этап" in j)
                check_true(f"action {i} journal has 'шаг_строки'", "шаг_строки" in j)
                check_true(f"action {i} journal has 'шаг_столбца'", "шаг_столбца" in j)


# ============================================================
# Запуск
# ============================================================

def run_all_tests():
    print("=" * 60)
    print("Юнит-тесты юпаны")
    print("=" * 60)

    test_groups = [
        ("yupana_core — числа Стирлинга", [
            test_stirling_table,
            test_stirling_second_kind,
        ]),
        ("yupana_core — преобразования", [
            test_lift_columns,
            test_lower_columns,
            test_roundtrip_lift_lower,
            test_shift_rows_right,
            test_shift_rows_left,
            test_full_roundtrip,
        ]),
        ("yupana_core — формулы", [
            test_stirling_diagonal,
            test_stirling_diagonal_components,
            test_a391838,
        ]),
        ("yupana_core — журнал", [
            test_transformation_journal,
        ]),
        ("yupana_lattice — умножение", [
            test_lattice_multiply,
            test_inca_multiply,
        ]),
        ("yupana_lattice — действия 11-12", [
            test_emulator_diagonal,
            test_emulator_a391838,
        ]),
        ("yupana_lattice — действия 13-16", [
            test_emulator_column_lift,
            test_emulator_column_lower,
            test_emulator_row_shift_right,
            test_emulator_row_shift_left,
            test_emulator_full_roundtrip,
        ]),
        ("Property-based тесты", [
            test_property_no_negative,
            test_property_triangular_upper,
            test_property_lift_identity_row0,
            test_property_journal_steps,
        ]),
    ]

    for group_name, tests in test_groups:
        print(f"\n--- {group_name} ---")
        for test in tests:
            test()

    print("\n" + "=" * 60)
    print(f"ИТОГО: {_tests_passed}/{_tests_total} passed")
    if _tests_passed == _tests_total:
        print("ВСЕ ТЕСТЫ ЗЕЛЁНЫЕ ✓")
    else:
        print(f"ПРОВАЛЕНО: {_tests_total - _tests_passed}")
        for f in _tests_failed:
            print(f"  {f}")
    print("=" * 60)
    return _tests_passed == _tests_total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
