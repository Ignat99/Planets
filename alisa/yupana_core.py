"""
yupana_core.py
Чистая математика для юпаны: числа Стирлинга, преобразования таблиц, диагональная формула.
Никаких словарей координат, никакого GUI. Только числа и Fraction.
"""

import math
from fractions import Fraction
from typing import List

try:
    from yupana_math import (
        stirling_second_kind, format_cell_display, compute_a391838_sequence
    )
except ImportError:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_math: {e}")
    yupana_math = None

# ============================================================
# Необходимые импорты (добавить в начало yupana_core.py
# после существующего импорта yupana_math)
# ============================================================

try:
    from yupana_lattice import (
        emulator_lattice_action_old,
        emulator_inca_lattice_action,
        emulator_stirling_diagonal_action,
        emulator_a391838_action,
        emulator_column_lift_action,
        emulator_column_lower_action,
        emulator_shift_rows_right_action,
        emulator_shift_rows_left_action,
    )
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_lattice: {e}")

try:
    from yupana_oscillator import generate_sine_on_triangular_grid
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_oscillator: {e}")



def stirling_unsigned_first(N: int, with_steps: bool = False):
    """
    Таблица беззнаковых чисел Стирлинга I рода c(n,k) для n,k = 0..N.

    Обозначения:
        n — номер строки (первый/верхний индекс в паре (n, k))
        k — номер столбца (второй/правый индекс в паре (n, k))

    Рекуррентная формула:
        c(n, k) = c(n-1, k-1) + (n-1) * c(n-1, k)

    Базовый случай:
        c(0, 0) = 1
        c(n, 0) = 0  при n > 0
        c(0, k) = 0  при k > 0

    Смысл формулы (на примере c(4, 2)):
        c(4, 2) = c(3, 1) + 3 * c(3, 2)
                = 2      + 3 * 3
                = 11

    Пошаговое объяснение для c(4, 2):
        Член 1: c(n-1, k-1) = c(3, 1) = 2
            Элемент n=4 образует собственный цикл (фиксированную точку).
            Берём число перестановок n-1 элементов в k-1 циклов.

        Член 2: (n-1) * c(n-1, k) = 3 * c(3, 2) = 3 * 3 = 9
            Элемент n=4 вставляется в один из (n-1)=3 существующих
            циклов перестановки n-1 элементов в k циклов.

        Сумма: 2 + 9 = 11 — число перестановок 4 элементов ровно в 2 цикла.

    Если with_steps=True, возвращает кортеж (table, steps_history),
    где steps_history — список словарей с полями:
        step, n, k, term_1, term_2, result, text
    """
    c = [[0] * (N + 1) for _ in range(N + 1)]
    c[0][0] = 1

    steps_history = []

    if with_steps:
        steps_history.append({
            "step": 0,
            "n": 0,
            "k": 0,
            "term_1": None,
            "term_2": None,
            "result": 1,
            "text": (
                "Базовый случай: c(0,0) = 1.\n"
                "  n=0 — строка 0, k=0 — столбец 0.\n"
                "  Единственная перестановка нуля элементов — пустая,\n"
                "  содержащая 0 циклов. Поэтому c(0,0)=1.\n"
                "  Все остальные ячейки нулевой строки и нулевого столбца = 0."
            )
        })

    step_idx = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            # Член 1: c(n-1, k-1) — по диагонали слева-сверху
            # Элемент n образует собственный цикл длины 1
            term_1 = c[n - 1][k - 1]

            # Член 2: (n-1) * c(n-1, k) — сверху, умноженное на (n-1)
            # Элемент n вставляется в один из (n-1) существующих циклов
            term_2 = (n - 1) * c[n - 1][k]

            c[n][k] = term_1 + term_2

            if with_steps:
                steps_history.append({
                    "step": step_idx,
                    "n": n,
                    "k": k,
                    "term_1": term_1,
                    "term_2": term_2,
                    "result": c[n][k],
                    "text": (
                        f"c({n},{k}):\n"
                        f"  n={n} (строка {n}), k={k} (столбец {k})\n"
                        f"  Член 1: c(n-1, k-1) = c({n-1}, {k-1}) = {term_1}\n"
                        f"    — элемент {n} образует собственный цикл\n"
                        f"  Член 2: (n-1) * c(n-1, k) = {n-1} * c({n-1}, {k}) = {n-1} * {c[n-1][k]} = {term_2}\n"
                        f"    — элемент {n} вставляется в один из {n-1} существующих циклов\n"
                        f"  Сумма: {term_1} + {term_2} = {c[n][k]}\n"
                        f"  Итог: c({n},{k}) = {c[n][k]}"
                    )
                })
                step_idx += 1

    if with_steps:
        steps_history.append({
            "step": step_idx,
            "n": None,
            "k": None,
            "term_1": None,
            "term_2": None,
            "result": None,
            "text": (
                f"Таблица Стирлинга I рода построена для N={N}.\n"
                f"Размер: {N+1}x{N+1}.\n"
                f"Обозначения: n (строка) — первый индекс, k (столбец) — второй.\n"
                f"Формула: c(n,k) = c(n-1,k-1) + (n-1)*c(n-1,k)\n"
                f"Контрольные значения:\n"
                f"  c(1,1)={c[1][1]}, c(2,1)={c[2][1]}, c(3,2)={c[3][2]}, "
                f"c(4,2)={c[4][2]}, c(5,3)={c[5][3]}, c(7,4)={c[7][4]}"
            )
        })
        return c, steps_history

    return c



def stirling_second_kind_val(n: int, k: int) -> int:
    """Число Стирлинга II рода S(n,k)."""
    if n == 0 and k == 0:
        return 1
    if k == 0 or k > n:
        return 0
    dp = [0] * (k + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        new_dp = [0] * (k + 1)
        for j in range(1, k + 1):
            new_dp[j] = j * dp[j] + dp[j - 1]
        dp = new_dp
    return dp[k]


# ============================================================
# Действие 13: Поднятие столбцов
# lifted[r][k] = c(r+k, k)
# Косые диагонали n-2k=x -> столбцы
# ============================================================

def lift_columns(table: List[List[int]], size: int, N: int) -> List[List[int]]:
    """
    Сдвиг столбца k вверх на k позиций.
    Журнал: этап='lift', позиция=(r,k), шаг строки +1, шаг столбца 0.
    Косая диагональ n-2k=x становится столбцом x.
    """
    lifted = [[0] * size for _ in range(size)]
    for r in range(size):
        for k in range(size):
            if r + k <= N:
                lifted[r][k] = table[r + k][k]
    return lifted


# ============================================================
# Действие 14: Опускание столбцов (обратное к 13)
# original[n][k] = lifted[n-k][k]
# ============================================================

def lower_columns(lifted: List[List[int]], size: int, N: int) -> List[List[int]]:
    """
    Сдвиг столбца k вниз на k позиций.
    Журнал: этап='lower', позиция=(n,k), шаг строки -1, шаг столбца 0.
    """
    original = [[0] * size for _ in range(size)]
    for n in range(size):
        for k in range(size):
            r = n - k
            if r >= 0 and r < size and r + k <= N:
                original[n][k] = lifted[r][k]
    return original


# ============================================================
# Действие 15: Сдвиг строк вправо
# triangular[r][c] = lifted[r][c-r] при c >= r, иначе 0
# Верхнетреугольная матрица, прочерки исчезают
# ============================================================

def shift_rows_right(lifted: List[List[int]], size: int) -> List[List[int]]:
    """
    Сдвиг строки r вправо на r позиций.
    Журнал: этап='shift_right', позиция=(r,c), шаг строки 0, шаг столбца меняется с 2 на 1.
    Условие col >= row (верхнетреугольная).
    """
    tri = [[0] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if c >= r:
                src = c - r
                if src < size:
                    tri[r][c] = lifted[r][src]
    return tri


# ============================================================
# Действие 16: Сдвиг строк влево (обратное к 15)
# lifted[r][c] = triangular[r][c+r] при c+r < size, иначе 0
# ============================================================

def shift_rows_left(tri: List[List[int]], size: int) -> List[List[int]]:
    """
    Сдвиг строки r влево на r позиций.
    Журнал: этап='shift_left', позиция=(r,c), шаг строки 0, шаг столбца меняется с 1 на 2.
    """
    lifted = [[0] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            src = c + r
            if src < size:
                lifted[r][c] = tri[r][src]
    return lifted


# ============================================================
# Действие 11: Косая диагональ Стирлинга — диагональная формула
# a(n) = (n!)^2 * sum_{k=0}^{floor(n/2)} c(n-k, n-2k) / ((2k+1)! * (n-k)!)
# ============================================================

def stirling_diagonal(n: int, table: List[List[int]] = None, N: int = None) -> int:
    """Вычисляет a(n) по диагональной формуле через числа Стирлинга I рода."""
    if n < 0:
        raise ValueError("n должен быть >= 0")
    if table is None:
        N = max(n, 7)
        table = stirling_unsigned_first(N)
    elif N is None:
        N = len(table) - 1

    total = Fraction(0)
    factorial_n_sq = math.factorial(n) ** 2
    for k in range(n // 2 + 1):
        s = table[n - k][n - 2 * k]
        denom = math.factorial(2 * k + 1) * math.factorial(n - k)
        total += Fraction(s, denom) * factorial_n_sq
    if total.denominator != 1:
        raise ArithmeticError(f"Результат не целый для n={n}: {total}")
    return total.numerator


def stirling_diagonal_components(n: int, table: List[List[int]] = None, N: int = None):
    """Возвращает список слагаемых (k, c(n-k,n-2k), component) для диагональной формулы."""
    if table is None:
        N = max(n, 7)
        table = stirling_unsigned_first(N)
    elif N is None:
        N = len(table) - 1

    factorial_n_sq = math.factorial(n) ** 2
    components = []
    for k in range(n // 2 + 1):
        s = table[n - k][n - 2 * k]
        denom = math.factorial(2 * k + 1) * math.factorial(n - k)
        comp = Fraction(s, denom) * factorial_n_sq
        components.append((k, s, comp))
    return components


# ============================================================
# Действие 12: A391838 через строку Стирлинга
# a(n) = 2^n * (2n+1) * n!
# (сумма строки n таблицы Стирлинга = n!)
# ============================================================

def a391838_row(n: int) -> int:
    """A391838 = 2^n * (2n+1) * n!"""
    if n < 0:
        raise ValueError("n должен быть >= 0")
    return (2 ** n) * (2 * n + 1) * math.factorial(n)


def compute_a391838_sequence(count: int) -> List[int]:
    """Последовательность A391838 для n = 0..count-1."""
    return [a391838_row(n) for n in range(count)]


# ============================================================
# Журнал преобразований — описывает, что меняется на каждом этапе
# ============================================================

def transformation_journal() -> list:
    """
    Возвращает описание всех четырёх преобразований с указанием:
    - этап
    - позиция мультипликатора c(n-k, n-2k)
    - шаг строки
    - шаг столбца
    """
    return [
        {
            "этап": "Исходная таблица",
            "позиция": "(n-k, n-2k)",
            "шаг_строки": -1,
            "шаг_столбца": -2,
            "описание": "Косая диагональ в исходной таблице Стирлинга c(n,k)"
        },
        {
            "этап": "Действие 13: Поднятие столбцов",
            "позиция": "(k, n-2k)",
            "шаг_строки": +1,
            "шаг_столбца": -2,
            "описание": "Первый индекс n-k заменяется на k (простой ряд). Шаг столбца остаётся -2."
        },
        {
            "этап": "Действие 15: Сдвиг строк вправо",
            "позиция": "(k, n-k)",
            "шаг_строки": +1,
            "шаг_столбца": -1,
            "описание": "Второй индекс n-2k заменяется на n-k. Шаг столбца меняется с -2 на -1. Матрица становится верхнетреугольной (col >= row)."
        },
        {
            "этап": "Итог: верхнетреугольная матрица",
            "позиция": "(r, c) = (k, n-k)",
            "шаг_строки": +1,
            "шаг_столбца": -1,
            "описание": "triangular[r][c] = c(c, c-r). Условие c >= r эквивалентно n >= 2k."
        }
    ]


# ============================================================
# Рефакторинг: Действие 0 (compute_a391838_sequence)
# ============================================================

def execute_action_refactoring_act0(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 0: a391838_sequence.
    Чистая математика: вычисляет последовательность и возвращает её.
    Не трогает model — только читает cols для размера.
    Возвращает {"seq": [...]}.
    """

    # Начало блока Действие 0
    if action_id == 0:
        seq = compute_a391838_sequence(model_b.cols)
        return {"seq": seq}
    # Конец блока Действие 0

    raise NotImplementedError(f"Действие {action_id} не реализовано в act0")


# ============================================================
# Рефакторинг: Действие 1 (беззнаковые числа Стирлинга 1 рода)
# ============================================================

#def execute_action_refactoring_act1(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 1: беззнаковые числа Стирлинга I рода c(n,k).
    Чистая математика: строит таблицу c(n,k) для n,k = 0..N.
    Возвращает {"table": [[...]], "n": n}.
    """

    # Начало блока Действие 1
#    if action_id == 1:
#        n = params.get("n", 5)
#        table = stirling_unsigned_first(n)
#        return {"table": table, "n": n}
    # Конец блока Действие 1


def execute_action_refactoring_act1(action_id, model_a, model_b, params):
    """
    Действие 1: таблица беззнаковых чисел Стирлинга I рода.
    Возвращает table, n и core-формат steps_history.
    """
    from yupana_core import stirling_unsigned_first

    n = params.get("n", 5)
    N = max(n, 7)

    table, core_steps = stirling_unsigned_first(N, with_steps=True)

    return {
        "table": table,
        "n": n,
        "N": N,
        "core_steps": core_steps
    }


    raise NotImplementedError(f"Действие {action_id} не реализовано в act1")


# ============================================================
# Рефакторинг: Действие 2 (Сложение — умножение на 2)
# ============================================================

def execute_action_refactoring_act2(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 2: умножение камешков по строкам на 2.
    """
    if action_id == 2:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, j) * 2)
        model_b.metadata = {"action": "add"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act2")


# ============================================================
# Рефакторинг: Действие 3 (Вычитание — обнуление)
# ============================================================

def execute_action_refactoring_act3(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 3: вычитание камешков (обнуление).
    """
    if action_id == 3:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "sub"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act3")


# ============================================================
# Рефакторинг: Действие 4 (Сдвиг вправо)
# ============================================================

def execute_action_refactoring_act4(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 4: сдвиг камешков вправо на 1 позицию.
    """
    if action_id == 4:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j > 0:
                    model_b.set_cell(i, j, model_a.get_cell(i, j - 1))
                else:
                    model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "shift"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act4")


# ============================================================
# Рефакторинг: Действие 5 (Зеркало)
# ============================================================

def execute_action_refactoring_act5(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 5: зеркальное отражение матрицы по горизонтали.
    """
    if action_id == 5:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, model_a.cols - 1 - j))
        model_b.metadata = {"action": "mirror"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act5")


# ============================================================
# Рефакторинг: Действие 6 (Транспонирование)
# ============================================================

def execute_action_refactoring_act6(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 6: транспонирование матрицы.
    """
    if action_id == 6:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j < model_b.rows and i < model_b.cols:
                    model_b.set_cell(j, i, model_a.get_cell(i, j))
        model_b.metadata = {"action": "transpose"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act6")


# ============================================================
# Рефакторинг: Действие 7 (Обращение)
# ============================================================

def execute_action_refactoring_act7(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 7: обращение последовательности (поворот на 180°).
    """
    if action_id == 7:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(model_a.rows - 1 - i, model_a.cols - 1 - j, model_a.get_cell(i, j))
        model_b.metadata = {"action": "inverse"}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act7")


# ============================================================
# Рефакторинг: Действие 8 (Умножение решёткой)
# ============================================================

def execute_action_refactoring_act8(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 8: умножение методом решётки (jelozia).
    Вызывает emulator_lattice_action_old из yupana_lattice.
    """
    if action_id == 8:
        a = params.get("a", 23)
        b = params.get("b", 41)
        try:
            state = emulator_lattice_action_old(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.set_bottom(0, result)
            model_b.metadata = {
                "action": "lattice_multiply", "a": a, "b": b, "result": result,
                "lattice_viz": state.get("lattice_str", "Сетка решётки построена успешно.")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "lattice_multiply", "a": a, "b": b, "result": result, "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act8")


# ============================================================
# Рефакторинг: Действие 9 (Синус NCO)
# ============================================================

def execute_action_refactoring_act9(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 9: генерация синуса на треугольной сетке.
    Вызывает generate_sine_on_triangular_grid из yupana_oscillator.
    """
    if action_id == 9:
        steps = params.get("steps", 9)
        amplitude = params.get("amplitude", 100000)
        shift_bit = params.get("shift_bit", 6)
        try:
            results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
            sine_values = [r[2] for r in results]
            model_b.set_bottom_row(sine_values[:model_b.cols])
            model_b.metadata = {"action": "sine_nco", "steps": steps, "amplitude": amplitude, "sine_values": sine_values}
        except Exception as e:
            model_b.metadata = {"action": "sine_nco", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act9")


# ============================================================
# Рефакторинг: Действие 10 (Умножение инков)
# ============================================================

def execute_action_refactoring_act10(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 10: поклеточное умножение на 9 клетках.
    Вызывает emulator_inca_lattice_action из yupana_lattice.
    """
    if action_id == 10:
        a = params.get("a", 11)
        b = params.get("b", 22)
        try:
            state = emulator_inca_lattice_action(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.metadata = {
                "action": "inca_multiply",
                "a": a, "b": b,
                "result": state.get("result", a * b),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "inca_multiply", "a": a, "b": b, "result": result, "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act10")


# ============================================================
# Рефакторинг: Действие 11 (Косая диагональ Стирлинга)
# ============================================================

def execute_action_refactoring_act11(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 11: косые диагонали Стирлинга I рода.
    Вызывает emulator_stirling_diagonal_action из yupana_lattice.
    """
    if action_id == 11:
        n_val = params.get("a", 3)
        try:
            state = emulator_stirling_diagonal_action(n_val)
            model_b.metadata = {
                "action": "stirling_diagonal",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "stirling_diagonal", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act11")


# ============================================================
# Рефакторинг: Действие 12 (A391838 через строку Стирлинга)
# ============================================================

def execute_action_refactoring_act12(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 12: A391838 = 2^n * (2n+1) * n!.
    Вызывает emulator_a391838_action из yupana_lattice.
    """
    if action_id == 12:
        n_val = params.get("a", 3)
        try:
            state = emulator_a391838_action(n_val)
            model_b.metadata = {
                "action": "a391838_row",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "a391838_row", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act12")


# ============================================================
# Рефакторинг: Действие 13 (Поднятие столбцов)
# ============================================================

def execute_action_refactoring_act13(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 13: сдвиг столбца k вверх на k позиций.
    Вызывает emulator_column_lift_action из yupana_lattice.
    """
    if action_id == 13:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lift_action(n_val)
            model_b.metadata = {
                "action": "column_lift",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lift", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act13")


# ============================================================
# Рефакторинг: Действие 14 (Опускание столбцов)
# ============================================================

def execute_action_refactoring_act14(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 14: сдвиг столбца k вниз на k позиций.
    Вызывает emulator_column_lower_action из yupana_lattice.
    """
    if action_id == 14:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lower_action(n_val)
            model_b.metadata = {
                "action": "column_lower",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lower", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act14")


# ============================================================
# Рефакторинг: Действие 15 (Сдвиг строк вправо)
# ============================================================

def execute_action_refactoring_act15(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 15: сдвиг строки r вправо на r позиций.
    Вызывает emulator_shift_rows_right_action из yupana_lattice.
    """
    if action_id == 15:
        n_val = params.get("a", 7)
        try:
            state = emulator_shift_rows_right_action(n_val)
            model_b.metadata = {
                "action": "shift_rows_right",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "shift_rows_right", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act15")


# ============================================================
# Рефакторинг: Действие 16 (Сдвиг строк влево)
# ============================================================

def execute_action_refactoring_act16(action_id, model_a, model_b, params=None):
    """
    Рефакторинг Действия 16: сдвиг строки r влево на r позиций.
    Вызывает emulator_shift_rows_left_action из yupana_lattice.
    """
    if action_id == 16:
        n_val = params.get("a", 7)
        try:
            state = emulator_shift_rows_left_action(n_val)
            model_b.metadata = {
                "action": "shift_rows_left",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "shift_rows_left", "error": str(e)}
        return model_a, model_b
    raise NotImplementedError(f"Действие {action_id} не реализовано в act16")


