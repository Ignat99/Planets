"""
yupana_lattice.py
Реализация алгоритмов умножения и преобразований таблицы Стирлинга для Юпаны.
Содержит функции-эмуляторы для действий 8-16.
"""

import math
import json
from fractions import Fraction

#from yupana_core import stirling_unsigned_first


# ============================================================
# Вспомогательная функция: таблица Стирлинга I рода
# ============================================================

def _build_stirling_table(N, with_steps=False):
    """
    Строит таблицу беззнаковых чисел Стирлинга I рода c(n,k) размера (N+1)x(N+1).

    Обозначения:
        n — номер строки (всегда первый/верхний индекс в паре (n, k))
        k — номер столбца (всегда второй/правый индекс в паре (n, k))

    Рекуррентная формула:
        c(n, k) = c(n-1, k-1) + (n-1) * c(n-1, k)

    Базовый случай:
        c(0, 0) = 1
        c(n, 0) = 0  при n > 0
        c(0, k) = 0  при k > 0

    Смысл формулы (на примере типичной ячейки c(4, 2)):
        c(4, 2) = c(3, 1) + 3 * c(3, 2)
                = 2      + 3 * 3
                = 2      + 9
                = 11

    Пошаговое объяснение для c(4, 2):
        Шаг 1: Берём значение слева-сверху — c(n-1, k-1) = c(3, 1) = 2.
               Это «восходящий» член: перестановки, где элемент n
               образует цикл длины 1 (фиксированная точка).

        Шаг 2: Берём значение сверху — c(n-1, k) = c(3, 2) = 3.
               Умножаем на (n-1) = 3.
               Это «боковой» член: элемент n вставляется в один из
               (n-1) существующих циклов.

        Шаг 3: Складываем: 2 + 3*3 = 2 + 9 = 11.
               Итог: c(4, 2) = 11 — число перестановок 4 элементов
               ровно в 2 цикла.

    Если with_steps=True, возвращает также steps_history
    с пошаговой анимацией заполнения таблицы.
    """
    c = [[0] * (N + 1) for _ in range(N + 1)]
    c[0][0] = 1

    steps_history = []

    if with_steps:
        steps_history.append({
            "left": {},
            "right": {(0, 0): 1},
            "text": (
                "Шаг 0: Базовый случай. c(0,0) = 1.\n"
                "  n=0 — строка 0, k=0 — столбец 0.\n"
                "  Единственная перестановка нуля элементов — пустая,\n"
                "  содержащая 0 циклов. Поэтому c(0,0)=1.\n"
                "  Все остальные ячейки нулевой строки и нулевого столбца = 0."
            )
        })

    for n in range(1, N + 1):
        for k in range(1, n + 1):
            # --- Расчёт ячейки c(n, k) ---

            # Член 1: c(n-1, k-1) — значение по диагонали слева-сверху
            # Это перестановки, где элемент n образует собственный цикл
            term_1 = c[n - 1][k - 1]

            # Член 2: (n-1) * c(n-1, k) — значение сверху, умноженное на (n-1)
            # Элемент n вставляется в один из (n-1) существующих циклов
            term_2 = (n - 1) * c[n - 1][k]

            # Сумма двух членов
            c[n][k] = term_1 + term_2

            if with_steps:
                # Снимок текущего состояния таблицы (проекция 8x8)
                snapshot = {}
                for r in range(min(8, N + 1)):
                    for col in range(min(8, N + 1)):
                        if c[r][col] > 0:
                            snapshot[(r, col)] = c[r][col]

                steps_history.append({
                    "left": dict(snapshot),
                    "right": {(n, k): c[n][k]},
                    "text": (
                        f"Ячейка c({n},{k}):\n"
                        f"  n={n} (строка {n}), k={k} (столбец {k})\n"
                        f"  Член 1: c(n-1, k-1) = c({n-1}, {k-1}) = {term_1}\n"
                        f"    — элемент {n} образует собственный цикл\n"
                        f"  Член 2: (n-1) * c(n-1, k) = {n-1} * c({n-1}, {k}) = {n-1} * {c[n-1][k]} = {term_2}\n"
                        f"    — элемент {n} вставляется в один из {n-1} существующих циклов\n"
                        f"  Сумма: {term_1} + {term_2} = {c[n][k]}\n"
                        f"  Итог: c({n},{k}) = {c[n][k]}"
                    )
                })

    if with_steps:
        # Финальный шаг: полная таблица
        final_snapshot = {}
        for r in range(min(8, N + 1)):
            for col in range(min(8, N + 1)):
                if c[r][col] > 0:
                    final_snapshot[(r, col)] = c[r][col]

        steps_history.append({
            "left": dict(final_snapshot),
            "right": {},
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


# ============================================================
# Действие 8: Умножение методом решётки (старая версия)
# ============================================================

def emulator_lattice_action_old(a: int, b: int) -> dict:
    str_a = str(a)
    str_b = str(b)

    left_yupana = {}
    right_yupana = {}

    for i, digit_a in enumerate(reversed(str_a)):
        for j, digit_b in enumerate(reversed(str_b)):
            prod = int(digit_a) * int(digit_b)
            left_yupana[(i, j)] = prod

    result = a * b
    str_res = str(result)
    for idx, digit in enumerate(reversed(str_res)):
        right_yupana[(0, idx)] = int(digit)

    viz = []
    viz.append(f"   {'   '.join(list(str_a))}")
    viz.append(" +" + "---+" * len(str_a))
    for j, db in enumerate(str_b):
        row_str = f"{db}|"
        for i, da in enumerate(str_a):
            p = int(da) * int(db)
            row_str += f"{p:02d}|"
        viz.append(row_str)
        viz.append(" +" + "---+" * len(str_a))

    return {
        "left_yupana": left_yupana,
        "right_yupana": right_yupana,
        "result": result,
        "lattice_str": "\n".join(viz)
    }


# ============================================================
# Действие 8 (новая): Умножение на 9 клетках
# ============================================================

def emulator_lattice_action(a: int, b: int) -> dict:
    a_low = a % 10
    a_high = (a // 10) % 10
    b_low = b % 10
    b_high = (b // 10) % 10

    left_yupana = {}
    right_yupana = {}

    left_yupana[(0, 1)] = a_low
    left_yupana[(2, 1)] = a_high
    left_yupana[(1, 0)] = b_low
    left_yupana[(1, 2)] = b_high

    val_00 = a_low * b_low
    val_02 = a_low * b_high
    val_20 = a_high * b_low
    val_22 = a_high * b_high

    left_yupana[(0, 0)] = val_00
    left_yupana[(0, 2)] = val_02
    left_yupana[(2, 0)] = val_20
    left_yupana[(2, 2)] = val_22

    val_center = val_02 + val_20
    left_yupana[(1, 1)] = val_center

    res_low = val_00 % 10
    carry_1 = val_00 // 10
    total_mid = val_center + carry_1
    res_mid = total_mid % 10
    carry_2 = total_mid // 10
    total_high = val_22 + carry_2
    res_high = total_high % 10
    carry_3 = total_high // 10
    res_thousands = carry_3

    right_yupana[(0, 0)] = res_low
    right_yupana[(0, 1)] = res_mid
    right_yupana[(0, 2)] = res_high
    if res_thousands > 0:
        right_yupana[(0, 3)] = res_thousands

    result = a * b
    viz = [
        "=== Алгоритм умножения инков (9 клеток) ===",
        f"Умножение: {a} x {b}",
        f"Результат: {result}",
    ]

    return {
        "left_yupana": left_yupana,
        "right_yupana": right_yupana,
        "result": result,
        "lattice_str": "\n".join(viz)
    }


# ============================================================
# Действие 10: Умножение инков с анимацией
# ============================================================

def emulator_inca_lattice_action(a: int, b: int) -> dict:
    a_low = a % 10
    a_high = (a // 10) % 10
    b_low = b % 10
    b_high = (b // 10) % 10

    steps_history = []

    steps_history.append({
        "left": {}, "right": {},
        "text": "Шаг 0: Подготовка счётной доски юпана."
    })

    left_1 = {(0, 1): a_low, (2, 1): a_high, (1, 0): b_low, (1, 2): b_high}
    steps_history.append({
        "left": left_1, "right": {},
        "text": f"Шаг 1: Выкладываем числа. A ({a_high} и {a_low}), B ({b_high} и {b_low})."
    })

    val_00 = a_low * b_low
    val_02 = a_low * b_high
    val_20 = a_high * b_low
    val_22 = a_high * b_high

    left_2 = dict(left_1)
    left_2.update({(0, 0): val_00, (0, 2): val_02, (2, 0): val_20, (2, 2): val_22})
    steps_history.append({
        "left": left_2, "right": {},
        "text": f"Шаг 2: Промежуточные произведения в углах:\n {val_20} и {val_22} вверху, {val_00} и {val_02} внизу."
    })

    val_center = val_02 + val_20
    left_3 = dict(left_2)
    left_3[(0, 2)] = 0
    left_3[(2, 0)] = 0
    left_3[(1, 1)] = val_center
    steps_history.append({
        "left": left_3, "right": {},
        "text": f"Шаг 3: Нить-перенос. {val_02} + {val_20} = {val_center}."
    })

    res_low = val_00 % 10
    carry_1 = val_00 // 10
    total_mid = val_center + carry_1
    res_mid = total_mid % 10
    carry_2 = total_mid // 10
    total_high = val_22 + carry_2
    res_high = total_high % 10
    carry_3 = total_high // 10
    res_thousands = carry_3

    right_4 = {(0, 0): res_low, (0, 1): res_mid, (0, 2): res_high}
    if res_thousands > 0:
        right_4[(0, 3)] = res_thousands

    steps_history.append({
        "left": dict(left_3),
        "right": right_4,
        "text": f"Шаг 4: Считывание: {res_low}, {res_mid}, {res_high}" + (f", {res_thousands}" if res_thousands > 0 else "")
    })

    result = a * b
    viz = [f"=== Пошаговое умножение инков ===", f"Результат: {result}"]

    return {
        "steps": steps_history,
        "result": result,
        "lattice_str": "\n".join(viz)
    }


# ============================================================
# Действие 11: Косая диагональ Стирлинга
# ============================================================

def emulator_stirling_diagonal_action(n_target: int) -> dict:
    if n_target < 0:
        raise ValueError("n_target должен быть >= 0")

    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    factorial_n_sq = math.factorial(n_target) ** 2
    k_max = n_target // 2

    steps_history = []

    left_start = {}
    for r in range(min(8, N + 1)):
        for col in range(min(8, N + 1)):
            if stirling[r][col] > 0:
                left_start[(r, col)] = stirling[r][col]

    steps_history.append({
        "left": dict(left_start),
        "use_accumulation": True,
        "temporary_right": {},
        "highlight": [],
        "text": f"Шаг 0: Таблица Стирлинга I рода c(n,k).\nНачинаем расчёт для n = {n_target}."
    })

    total = Fraction(0)
    selected = []
    components = []

    for k in range(k_max + 1):
        s_row = n_target - k
        s_col = n_target - 2 * k
        s_val = stirling[s_row][s_col]

        denom = math.factorial(2 * k + 1) * math.factorial(n_target - k)
        component = Fraction(s_val, denom) * factorial_n_sq
        total += component
        selected.append((s_row, s_col, s_val))
        components.append(component)

        step_right = {}
        for idx, (sr, sc, sv) in enumerate(selected):
            display_row = min(sr, 7)
            display_col = min(sc, 7)
            step_right[(display_row, display_col)] = sv

        steps_history.append({
            "left": dict(left_start),
            "use_accumulation": True,
            "temporary_right": dict(step_right),
            "highlight": [(min(sr, 7), min(sc, 7)) for sr, sc, _ in selected],
            "text": f"Шаг {k + 1}: k={k}, c({s_row},{s_col}) = {s_val}\n"
                    f" Слагаемое: {s_val} / {denom} * {factorial_n_sq} = {component}"
        })

    if total.denominator != 1:
        raise ArithmeticError(f"Результат не целый для n={n_target}: {total}")
    final_result = total.numerator

    final_right = {}
    for idx, comp in enumerate(components):
        display_row = min(idx, 7)
        final_right[(display_row, 0)] = int(comp)

    steps_history.append({
        "left": dict(left_start),
        "use_accumulation": False,
        "temporary_right": dict(final_right),
        "highlight": [],
        "text": f"Финал: " + " + ".join(str(int(c)) for c in components) + f" = {final_result}"
    })

    return {
        "steps": steps_history,
        "result": final_result,
        "lattice_str": f"=== Косая диагональ Стирлинга ===\na({n_target}) = {final_result}"
    }


# ============================================================
# Действие 12: A391838 через строку Стирлинга
# ============================================================

def emulator_a391838_action(n_target: int) -> dict:
    if n_target < 0:
        raise ValueError("n_target должен быть >= 0")

    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    multiplier = (2 ** n_target) * (2 * n_target + 1)
    factorial_n = math.factorial(n_target)

    steps_history = []

    left_start = {}
    for r in range(min(8, N + 1)):
        for col in range(min(8, N + 1)):
            if stirling[r][col] > 0:
                left_start[(r, col)] = stirling[r][col]

    steps_history.append({
        "left": dict(left_start),
        "use_accumulation": True,
        "temporary_right": {},
        "highlight": [],
        "text": f"Шаг 0: Таблица Стирлинга. Расчёт A391838 для n = {n_target}."
    })

    row_sum = 0
    selected = []

    for k in range(n_target + 1):
        s_val = stirling[n_target][k]
        row_sum += s_val
        selected.append((n_target, k, s_val))

        step_right = {}
        for idx, (sr, sc, sv) in enumerate(selected):
            display_row = min(sr, 7)
            display_col = min(sc, 7)
            step_right[(display_row, display_col)] = sv

        steps_history.append({
            "left": dict(left_start),
            "use_accumulation": True,
            "temporary_right": dict(step_right),
            "highlight": [(min(sr, 7), min(sc, 7)) for sr, sc, _ in selected],
            "text": f"Шаг {k + 1}: c({n_target},{k}) = {s_val}\n Сумма строки: {row_sum}"
        })

    final_result = multiplier * row_sum

    assert final_result == multiplier * math.factorial(n_target), \
        f"Mismatch: {final_result} vs {multiplier * math.factorial(n_target)}"

    final_right = {}
    for idx, (sr, sc, sv) in enumerate(selected):
        comp = sv * multiplier
        display_row = min(idx, 7)
        final_right[(display_row, 0)] = comp

    steps_history.append({
        "left": dict(left_start),
        "use_accumulation": False,
        "temporary_right": dict(final_right),
        "highlight": [],
        "text": f"Финал: множитель = {multiplier}\n Слагаемые: "
               + " + ".join(str(sv * multiplier) for _, _, sv in selected)
               + f" = {final_result}"
    })

    return {
        "steps": steps_history,
        "result": final_result,
        "lattice_str": f"=== A391838 ===\na({n_target}) = {final_result}"
    }


# ============================================================
# Действие 13: Поднятие столбцов
# ============================================================

def emulator_column_lift_action(n_target: int) -> dict:
    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    steps_history = []

    left_start = {}
    for r in range(min(8, N + 1)):
        for col in range(min(8, N + 1)):
            if stirling[r][col] > 0:
                left_start[(r, col)] = stirling[r][col]

    steps_history.append({
        "left": dict(left_start),
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Исходная таблица Стирлинга I рода c(n,k).\n"
                f"Каждый столбец k будет сдвинут вверх на k позиций.\n"
                f"Этап: исходная таблица | Позиция: (n-k, n-2k) | Шаг строки: -1 | Шаг столбца: -2"
    })

    lifted = {}
    for col in range(min(8, N + 1)):
        for r in range(min(8, N + 1)):
            src_n = r + col
            if src_n <= N and stirling[src_n][col] > 0:
                lifted[(r, col)] = stirling[src_n][col]

        right_current = {}
        for (r, k), v in lifted.items():
            right_current[(r, k)] = v

        col_vals = []
        for r in range(min(8, N + 1)):
            src_n = r + col
            if src_n <= N and stirling[src_n][col] > 0:
                col_vals.append(f"c({src_n},{col})={stirling[src_n][col]}")

        steps_history.append({
            "left": dict(left_start),
            "right": dict(right_current),
            "highlight": [(r, col) for r in range(min(8, N + 1)) if (r, col) in lifted],
            "text": f"Шаг {col + 1}: Поднимаем столбец {col} на {col} позиций.\n"
                    f" Значения: {', '.join(col_vals[:6])}\n"
                    f" Этап: поднятие столбцов | Позиция: (k, n-2k) | Шаг строки: +1 | Шаг столбца: -2 | Изменение: первый индекс n-k -> k"
        })

    row1 = [lifted.get((1, k), 0) for k in range(8)]
    tri_check = all(row1[k] == k * (k + 1) // 2 for k in range(min(8, N + 1)))

    steps_history.append({
        "left": dict(left_start),
        "right": dict(lifted),
        "highlight": [],
        "text": f"Готово! Поднятая таблица построена.\n"
                f"Проверка: строка 1 = {row1} — треугольные числа: {tri_check}\n"
                f"Этап: поднятая таблица | Позиция: (k, n-2k) | Шаг строки: +1 | Шаг столбца: -2"
    })

    return {
        "steps": steps_history,
        "result": 0,
        "lattice_str": f"=== Поднятие столбцов ===\nСтрока 1: треугольные числа\nСтолбцы = бывшие косые диагонали"
    }


# ============================================================
# Действие 14: Опускание столбцов
# ============================================================

def emulator_column_lower_action(n_target: int) -> dict:
    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    lifted = {}
    for r in range(min(8, N + 1)):
        for col in range(min(8, N + 1)):
            src_n = r + col
            if src_n <= N and stirling[src_n][col] > 0:
                lifted[(r, col)] = stirling[src_n][col]

    steps_history = []

    left_start = dict(lifted)

    steps_history.append({
        "left": dict(left_start),
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Поднятая таблица Стирлинга.\n"
                f"Каждый столбец k будет опущен на k позиций вниз.\n"
                f"Этап: поднятая таблица | Позиция: (k, n-2k) | Шаг строки: +1 | Шаг столбца: -2"
    })

    lowered = {}
    for col in range(min(8, N + 1)):
        for n in range(min(8, N + 1)):
            r = n - col
            if r >= 0 and (r, col) in lifted:
                val = lifted[(r, col)]
                if val > 0:
                    lowered[(n, col)] = val

        right_current = {}
        for (nn, k), v in lowered.items():
            right_current[(nn, k)] = v

        col_vals = []
        for n in range(min(8, N + 1)):
            r = n - col
            if r >= 0 and (r, col) in lifted:
                col_vals.append(f"c({n},{col})={lifted[(r, col)]}")

        steps_history.append({
            "left": dict(left_start),
            "right": dict(right_current),
            "highlight": [(n, col) for n in range(min(8, N + 1)) if (n, col) in lowered],
            "text": f"Шаг {col + 1}: Опускаем столбец {col} на {col} позиций.\n"
                    f" Значения: {', '.join(col_vals[:6])}\n"
                    f" Этап: опускание столбцов | Позиция: (n, k) | Шаг строки: +1 | Шаг столбца: -2 | Изменение: первый индекс k -> n-k"
        })

    steps_history.append({
        "left": dict(left_start),
        "right": dict(lowered),
        "highlight": [],
        "text": f"Готово! Опущенная таблица = исходная таблица Стирлинга.\n"
                f"Этап: исходная таблица | Позиция: (n-k, n-2k) | Шаг строки: -1 | Шаг столбца: -2"
    })

    return {
        "steps": steps_history,
        "result": 0,
        "lattice_str": f"=== Опускание столбцов ===\nОбратное преобразование: косые диагонали восстановлены"
    }


# ============================================================
# Действие 15: Сдвиг строк вправо (верхнетреугольная матрица)
# ============================================================

def emulator_shift_rows_right_action(n_target: int) -> dict:
    """
    Сдвиг строки r вправо на r позиций.
    lifted[r][c] -> triangular[r][c+r]
    Шаг столбца меняется с -2 на -1.
    Матрица становится верхнетреугольной: triangular[r][c] = c(c, c-r).
    """
    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    # Сначала строим поднятую таблицу
    lifted = {}
    for r in range(min(10, N + 1)):
        for col in range(min(10, N + 1)):
            src_n = r + col
            if src_n <= N and stirling[src_n][col] > 0:
                lifted[(r, col)] = stirling[src_n][col]

    steps_history = []

    # Левая таблица: поднятая таблица (проекция 8x8)
    left_start = {}
    for r in range(8):
        for col in range(8):
            if (r, col) in lifted:
                left_start[(r, col)] = lifted[(r, col)]

    steps_history.append({
        "left": dict(left_start),
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Поднятая таблица Стирлинга.\n"
                f"Каждая строка r будет сдвинута вправо на r позиций.\n"
                f"Этап: поднятая таблица | Позиция: (k, n-2k) | Шаг строки: +1 | Шаг столбца: -2"
    })

    # Пошаговый сдвиг строк
    triangular = {}  # (r, c) -> value
    GRID = 10  # используем 10x10 для вычислений, отображаем 8x8

    for row in range(min(GRID, N + 1)):
        # Сдвигаем строку row вправо на row позиций
        for col in range(GRID):
            if (row, col) in lifted:
                new_col = col + row
                if new_col < GRID:
                    triangular[(row, new_col)] = lifted[(row, col)]

        # Правая таблица: текущее состояние треугольной матрицы (проекция 8x8)
        right_current = {}
        for (r, c), v in triangular.items():
            if r < 8 and c < 8:
                right_current[(r, c)] = v

        # Описание сдвига строки
        row_vals = []
        for col in range(GRID):
            if (row, col) in lifted:
                new_col = col + row
                if new_col < GRID:
                    v15 = lifted[(row,col)]
                    row_vals.append(f"lifted[{row},{col}]={v15} -> tri[{row},{new_col}]")

        steps_history.append({
            "left": dict(left_start),
            "right": dict(right_current),
            "highlight": [(row, c) for c in range(8) if (row, c) in left_start],
            "text": f"Шаг {row + 1}: Сдвигаем строку {row} вправо на {row} позиций.\n"
                    f" Значения: {', '.join(row_vals[:6])}\n"
                    f" Этап: сдвиг строк вправо | Позиция: (r, c+r) | Шаг строки: +1 | Шаг столбца: -1 | Изменение: шаг столбца -2 -> -1"
        })

    # Финальный шаг: проверка треугольной формы
    is_upper_triangular = True
    for r in range(8):
        for c in range(8):
            if c < r and triangular.get((r, c), 0) != 0:
                is_upper_triangular = False
                break

    final_right = {}
    for (r, c), v in triangular.items():
        if r < 8 and c < 8:
            final_right[(r, c)] = v

    steps_history.append({
        "left": dict(left_start),
        "right": dict(final_right),
        "highlight": [],
        "text": f"Готово! Верхнетреугольная матрица построена.\n"
                f"Проверка: верхнетреугольная = {is_upper_triangular}\n"
                f"triangular[r][c] = c(c, c-r)\n"
                f"Этап: треугольная матрица | Позиция: (k, n-k) | Шаг строки: +1 | Шаг столбца: -1"
    })

    return {
        "steps": steps_history,
        "result": 0,
        "lattice_str": f"=== Сдвиг строк вправо ===\nВерхнетреугольная матрица\nШаг столбца: -2 -> -1"
    }


# ============================================================
# Действие 16: Сдвиг строк влево (обратный)
# ============================================================

def emulator_shift_rows_left_action(n_target: int) -> dict:
    """
    Обратный сдвиг: строка r сдвигается влево на r позиций.
    triangular[r][c+r] -> lifted[r][c]
    Шаг столбца меняется с -1 на -2.
    """
    N = max(n_target, 9)
    stirling = _build_stirling_table(N)

    # Строим поднятую таблицу
    lifted = {}
    for r in range(min(10, N + 1)):
        for col in range(min(10, N + 1)):
            src_n = r + col
            if src_n <= N and stirling[src_n][col] > 0:
                lifted[(r, col)] = stirling[src_n][col]

    # Строим треугольную матрицу
    triangular = {}
    GRID = 10
    for r in range(GRID):
        for col in range(GRID):
            if (r, col) in lifted:
                new_col = col + r
                if new_col < GRID:
                    triangular[(r, new_col)] = lifted[(r, col)]

    steps_history = []

    # Левая таблица: треугольная матрица (проекция 8x8)
    left_start = {}
    for (r, c), v in triangular.items():
        if r < 8 and c < 8:
            left_start[(r, c)] = v

    steps_history.append({
        "left": dict(left_start),
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Треугольная матрица.\n"
                f"Каждая строка r будет сдвинута влево на r позиций.\n"
                f"Этап: треугольная матрица | Позиция: (k, n-k) | Шаг строки: +1 | Шаг столбца: -1"
    })

    # Пошаговый сдвиг строк влево
    result_lifted = {}
    for row in range(min(GRID, N + 1)):
        for col in range(GRID):
            new_col = col - row
            if new_col >= 0 and (row, col) in triangular:
                result_lifted[(row, new_col)] = triangular[(row, col)]

        right_current = {}
        for (r, c), v in result_lifted.items():
            if r < 8 and c < 8:
                right_current[(r, c)] = v

        row_vals = []
        for col in range(GRID):
            new_col = col - row
            if new_col >= 0 and (row, col) in triangular:
                row_vals.append(f"tri[{row},{col}] -> lifted[{row},{new_col}]")

        steps_history.append({
            "left": dict(left_start),
            "right": dict(right_current),
            "highlight": [(row, c) for c in range(8) if (row, c) in left_start],
            "text": f"Шаг {row + 1}: Сдвигаем строку {row} влево на {row} позиций.\n"
                    f" Значения: {', '.join(row_vals[:6])}\n"
                    f" Этап: сдвиг строк влево | Позиция: (r, c-r) | Шаг строки: +1 | Шаг столбца: -2 | Изменение: шаг столбца -1 -> -2"
        })

    # Финальный шаг: проверка round-trip
    match = True
    for r in range(8):
        for c in range(8):
            orig = lifted.get((r, c), 0)
            restored = result_lifted.get((r, c), 0)
            if orig != restored:
                match = False

    final_right = {}
    for (r, c), v in result_lifted.items():
        if r < 8 and c < 8:
            final_right[(r, c)] = v

    steps_history.append({
        "left": dict(left_start),
        "right": dict(final_right),
        "highlight": [],
        "text": f"Готово! Поднятая таблица восстановлена.\n"
                f"Проверка round-trip (lift->tri->lift): {match}\n"
                f"Этап: поднятая таблица | Позиция: (k, n-2k) | Шаг строки: +1 | Шаг столбца: -2"
    })

    return {
        "steps": steps_history,
        "result": 0,
        "lattice_str": f"=== Сдвиг строк влево ===\nОбратное преобразование\nШаг столбца: -1 -> -2"
    }


# ============================================================
# Алиасы для совместимости с test_yupana.py
# ============================================================

emulator_row_shift_right_action = emulator_shift_rows_right_action
emulator_row_shift_left_action = emulator_shift_rows_left_action


# ============================================================
# Экспорт журнала преобразований
# ============================================================

def export_journal_json():
    """Экспорт журнала преобразований в JSON строку."""
    journal = [
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
            "шаг_строки": 1,
            "шаг_столбца": -2,
            "описание": "Первый индекс n-k заменяется на k (простой ряд). Шаг столбца остаётся -2."
        },
        {
            "этап": "Действие 15: Сдвиг строк вправо",
            "позиция": "(k, n-k)",
            "шаг_строки": 1,
            "шаг_столбца": -1,
            "описание": "Второй индекс n-2k заменяется на n-k. Шаг столбца меняется с -2 на -1. Матрица становится верхнетреугольной (col >= row)."
        },
        {
            "этап": "Итог: верхнетреугольная матрица",
            "позиция": "(r, c) = (k, n-k)",
            "шаг_строки": 1,
            "шаг_столбца": -1,
            "описание": "triangular[r][c] = c(c, c-r). Условие c >= r эквивалентно n >= 2k."
        }
    ]
    return json.dumps(journal, ensure_ascii=False, indent=2)


def export_journal_text():
    """Экспорт журнала преобразований в текстовую строку."""
    journal = [
        ("Исходная таблица", "(n-k, n-2k)", -1, -2,
         "Косая диагональ в исходной таблице Стирлинга c(n,k)"),
        ("Действие 13: Поднятие столбцов", "(k, n-2k)", 1, -2,
         "Первый индекс n-k заменяется на k (простой ряд). Шаг столбца остаётся -2."),
        ("Действие 15: Сдвиг строк вправо", "(k, n-k)", 1, -1,
         "Второй индекс n-2k заменяется на n-k. Шаг столбца меняется с -2 на -1. Матрица становится верхнетреугольной (col >= row)."),
        ("Итог: верхнетреугольная матрица", "(r, c) = (k, n-k)", 1, -1,
         "triangular[r][c] = c(c, c-r). Условие c >= r эквивалентно n >= 2k."),
    ]
    lines = []
    for этап, позиция, шаг_строки, шаг_столбца, описание in journal:
        lines.append(f"Этап: {этап}")
        lines.append(f"  Позиция: {позиция}")
        lines.append(f"  Шаг строки: {шаг_строки}, Шаг столбца: {шаг_столбца}")
        lines.append(f"  Описание: {описание}")
        lines.append("")
    return "\n".join(lines)


# ============================================================
# Действие 17: (зарезервировано)
# Стандартное имя: emulator_factorial_action_action_17_doom
# Вызывается из execute_action.py через yupana_core.execute_action_refactoring_act17
# ============================================================

def emulator_factorial_action_17_doom(n_target: int) -> dict:
    """
    Действие 17: заглушка со стандартным интерфейсом.
    Возвращает steps_history, result, lattice_str — как все остальные emulator_*_action.
    """
    steps_history = [{
        "left": {},
        "right": {},
        "highlight": [],
        "text": "Действие 17: не определено. Заглушка."
    }]

    return {
        "steps": steps_history,
        "result": 0,
        "lattice_str": "=== Действие 17: заглушка ==="
    }

# ============================================================
# Действие 17: Факториал n!
# Стандартное имя: emulator_factorial_action_action_17
# Вызывается из execute_action.py через yupana_core.execute_action_refactoring_act17
# ============================================================

def emulator_factorial_action_17(n_target: int) -> dict:
    """
    Действие 17: Вычисление факториала n! с пошаговой анимацией.
    Левая юпана: множители 1, 2, 3, ..., n в строке i, столбец 0.
    Правая юпана: i! в строке i, столбцы 0..i — треугольное заполнение.
    """
    import math

    steps_history = []

    steps_history.append({
        "left": {},
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Вычисление {n_target}!"
    })

    accumulated_left = {}
    accumulated_right = {}

    for i in range(n_target):
        factor = i + 1
        fact_i = math.factorial(i)

        accumulated_left[(i, 0)] = factor

        for col in range(i + 1):
            accumulated_right[(i, col)] = fact_i

        highlight = [(i, col) for col in range(i + 1)]

        steps_history.append({
            "left": dict(accumulated_left),
            "right": dict(accumulated_right),
            "highlight": highlight,
            "text": f"Шаг {i + 1}: строка {i}, {i}! = {fact_i}"
        })

    final_result = math.factorial(n_target)

    steps_history.append({
        "left": dict(accumulated_left),
        "right": dict(accumulated_right),
        "highlight": [],
        "text": f"Финал: {n_target}! = {final_result}"
    })

    return {
        "steps": steps_history,
        "result": final_result,
        "lattice_str": f"=== Факториал ===\n{n_target}! = {final_result}"
    }


# ============================================================
# Действие 17: Факториал через Стирлинга I рода
# n! = Σ c(n,k), k=0..n
# Стандартное имя: emulator_factorial_action_17
# ============================================================



def emulator_factorial_action_17_Stirling(n_target: int) -> dict:
    """
    Действие 17: Факториал как сумма строки Стирлинга I рода.
    Показывает распределение n! по n подциклам Стирлинга.
    Возвращает steps_history, result, lattice_str — как все остальные emulator_*_action.
    """
    if n_target < 0:
        raise ValueError("n_target должен быть >= 0")

    N = max(n_target, 7)
#    stirling = stirling_unsigned_first(N)

    steps_history = []

    left_start = {}
    for r in range(min(8, N + 1)):
        for col in range(min(8, N + 1)):
            if stirling[r][col] > 0:
#                left_start[(r, col)] = stirling[r][col]
                pass

    steps_history.append({
        "left": dict(left_start),
        "right": {},
        "highlight": [],
        "text": f"Шаг 0: Таблица Стирлинга I рода c(n,k).\n"
                f"Расчёт факториала n={n_target} как суммы строки."
    })

    row_sum = 0
    selected = []

    for k in range(n_target + 1):
        s_val = stirling[n_target][k]
        row_sum += s_val
        selected.append((n_target, k, s_val))

        step_right = {}
        for idx, (sr, sc, sv) in enumerate(selected):
            display_row = min(sr, 7)
            display_col = min(sc, 7)
            step_right[(display_row, display_col)] = sv

        steps_history.append({
            "left": dict(left_start),
            "right": dict(step_right),
            "highlight": [(min(sr, 7), min(sc, 7)) for sr, sc, _ in selected],
            "text": f"Шаг {k + 1}: c({n_target},{k}) = {s_val}\n"
                    f" Накопленная сумма: {row_sum}"
        })

    final_result = math.factorial(n_target)

    assert row_sum == final_result, \
        f"Несовпадение: сумма строки {row_sum} vs {n_target}! = {final_result}"

    final_right = {}
    for idx, (sr, sc, sv) in enumerate(selected):
        display_row = min(idx, 7)
        final_right[(display_row, 0)] = sv

    steps_history.append({
        "left": dict(left_start),
        "right": dict(final_right),
        "highlight": [],
        "text": f"Финал: " + " + ".join(str(sv) for _, _, sv in selected) +
                f" = {final_result}\n"
                f"{n_target}! = {final_result} = сумма строки {n_target} таблицы Стирлинга"
    })

    return {
        "steps": steps_history,
        "result": final_result,
        "lattice_str": f"=== Факториал через Стирлинга I рода ===\n"
                       f"{n_target}! = {final_result}"
    }



# ============================================================
# Тесты
# ============================================================

def _run_tests():
    tests_passed = 0
    tests_total = 0

    def check(name, actual, expected):
        nonlocal tests_passed, tests_total
        tests_total += 1
        if actual == expected:
            tests_passed += 1
        else:
            print(f"  FAIL: {name}: expected {expected}, got {actual}")

    N = 9
    c = _build_stirling_table(N)

    # Тесты Стирлинга
    check("c(0,0)", c[0][0], 1)
    check("c(1,1)", c[1][1], 1)
    check("c(2,1)", c[2][1], 1)
    check("c(3,1)", c[3][1], 2)
    check("c(3,2)", c[3][2], 3)
    check("c(4,2)", c[4][2], 11)
    check("c(5,3)", c[5][3], 35)
    check("c(7,4)", c[7][4], 735)

    # Тесты умножения
    r = emulator_lattice_action(23, 41)
    check("mult 23x41", r["result"], 943)

    r = emulator_inca_lattice_action(12, 34)
    check("inca 12x34", r["result"], 408)
    check("inca steps", len(r["steps"]), 5)

    # Тесты диагонали
    expected_diag = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040, 61943616]
    for n in range(10):
        r = emulator_stirling_diagonal_action(n)
        check(f"diag n={n}", r["result"], expected_diag[n])

    # Тесты A391838
    expected_a391838 = [1, 6, 40, 336, 3456, 42240, 599040, 9676800]
    for n in range(8):
        r = emulator_a391838_action(n)
        check(f"A391838 n={n}", r["result"], expected_a391838[n])

    # Тесты поднятия столбцов
    r = emulator_column_lift_action(7)
    lifted = r["steps"][-1]["right"]
    row1 = [lifted.get((1, k), 0) for k in range(8)]
    check("lift row1 = triangular", row1, [0, 1, 3, 6, 10, 15, 21, 28])

    # Тесты опускания
    r = emulator_column_lower_action(7)
    lowered = r["steps"][-1]["right"]
    check("lower[3][2]", lowered.get((3, 2), 0), 3)
    check("lower[4][2]", lowered.get((4, 2), 0), 11)

    # Тесты сдвига строк вправо
    r = emulator_shift_rows_right_action(7)
    tri = r["steps"][-1]["right"]
    # triangular[r][c] = c(c, c-r)
    check("tri[0][0]", tri.get((0, 0), 0), 1)
    check("tri[0][1]", tri.get((0, 1), 0), 1)
    check("tri[1][2]", tri.get((1, 2), 0), 1)
    check("tri[1][3]", tri.get((1, 3), 0), 3)
    check("tri[2][3]", tri.get((2, 3), 0), 2)
    check("tri[2][4]", tri.get((2, 4), 0), 11)
    check("tri[3][4]", tri.get((3, 4), 0), 6)
    # Проверка верхнетреугольности
    is_upper = all(tri.get((r, c), 0) == 0 for r in range(8) for c in range(8) if c < r)
    check("upper triangular", is_upper, True)

    # Тесты сдвига строк влево (round-trip)
    r2 = emulator_shift_rows_left_action(7)
    restored = r2["steps"][-1]["right"]
    # Проверяем round-trip: lift -> tri -> lift = lift
    for r_idx in range(8):
        for c_idx in range(8):
            orig = lifted.get((r_idx, c_idx), 0)
            got = restored.get((r_idx, c_idx), 0)
            if orig != got:
                check(f"round-trip ({r_idx},{c_idx})", got, orig)

    # Дополнительная проверка: triangular[r][c] = c(c, c-r)
    c_table = _build_stirling_table(9)
    for r in range(8):
        for col in range(8):
            if col >= r:
                expected_val = c_table[col][col - r]
                actual_val = tri.get((r, col), 0)
                if expected_val > 0 or actual_val > 0:
                    check(f"tri[{r}][{col}]=c({col},{col-r})", actual_val, expected_val)

    print(f"\nТесты: {tests_passed}/{tests_total} passed")
    if tests_passed == tests_total:
        print("ВСЕ ТЕСТЫ ЗЕЛЁНЫЕ")
    else:
        print(f"ПРОВАЛЕНО: {tests_total - tests_passed}")
    return tests_passed == tests_total


if __name__ == "__main__":
    _run_tests()
