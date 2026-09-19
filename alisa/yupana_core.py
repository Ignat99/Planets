"""
yupana_core.py
Чистая математика для юпаны: числа Стирлинга, преобразования таблиц, диагональная формула.
Никаких словарей координат, никакого GUI. Только числа и Fraction.
"""

import math
from fractions import Fraction
from typing import List


def stirling_unsigned_first(N: int) -> List[List[int]]:
    """Таблица беззнаковых чисел Стирлинга I рода c(n,k) для n,k = 0..N."""
    c = [[0] * (N + 1) for _ in range(N + 1)]
    c[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            c[n][k] = c[n - 1][k - 1] + (n - 1) * c[n - 1][k]
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
# Косые диагонали n-2k=x → столбцы
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
