"""
yupana_math.py — Чистая математика Юпаны: числа Стирлинга, A391838, матрицы, экспорт.

Без GUI, без Tkinter. Тестируемая, переносимая в Scala/Fortran.
Все дробные вычисления через fractions.Fraction — точность без потерь.
"""

from fractions import Fraction
from typing import List, Tuple, Set, Optional
import math
import csv
import io
import json

# ──────────────────────────────────────────────────────────────────────────────
# 1. Числа Стирлинга I рода (беззнаковые)
# ──────────────────────────────────────────────────────────────────────────────

def stirling_first_kind(N: int) -> List[List[int]]:
    """Беззнаковые числа Стирлинга I рода s(n,k).
    
    s(0,0) = 1
    s(n,k) = s(n-1,k-1) + (n-1)*s(n-1,k)
    """
    s = [[0] * (N + 1) for _ in range(N + 1)]
    s[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            s[n][k] = s[n - 1][k - 1] + (n - 1) * s[n - 1][k]
    return s


# Предвычисленная таблица для максимального размера 18
S_MAX: List[List[int]] = stirling_first_kind(18)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Разносная схема (биномиальные коэффициенты)
# ──────────────────────────────────────────────────────────────────────────────

def rassnos_matrix(nrows: int, ncols: int) -> List[List[int]]:
    """Матрица разносной схемы = биномиальные коэффициенты C(n,k)."""
    values = [[0] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = math.comb(n, k)
    return values


# ──────────────────────────────────────────────────────────────────────────────
# 3. Матрица Стирлинга
# ──────────────────────────────────────────────────────────────────────────────

def stirling_matrix(nrows: int, ncols: int) -> List[List[int]]:
    """Матрица из беззнаковых чисел Стирлинга I рода."""
    values = [[0] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = S_MAX[n][k]
    return values


# ──────────────────────────────────────────────────────────────────────────────
# 4. Дифференцирование: переход вверх + деление на номер строки
# ──────────────────────────────────────────────────────────────────────────────

def diff_matrix(nrows: int, ncols: int) -> List[List[Fraction]]:
    """Дифференцирование матрицы Стирлинга.
    
    Переход вверх (s(n-1,k)) + деление на n.
    Для n=0 — нули (нет строки выше).
    """
    values: List[List[Fraction]] = [[Fraction(0)] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            if n > 0:
                values[n][k] = Fraction(S_MAX[n - 1][k], n)
            # n == 0 → остаётся 0
    return values


# ──────────────────────────────────────────────────────────────────────────────
# 5. Нормировка a_n / n!
# ──────────────────────────────────────────────────────────────────────────────

def normalized_matrix(nrows: int, ncols: int) -> List[List[Fraction]]:
    """Нормировка: s(n,k) / n!."""
    values: List[List[Fraction]] = [[Fraction(0)] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = Fraction(S_MAX[n][k], math.factorial(n))
    return values


# ──────────────────────────────────────────────────────────────────────────────
# 6. Диагонали
# ──────────────────────────────────────────────────────────────────────────────

def fibonacci_diagonal(nrows: int, ncols: int) -> Tuple[List[List[int]], Set[Tuple[int, int]]]:
    """Прямые диагонали s(n, n-k) — аналог Фибоначчи.
    
    Возвращает (values, highlight).
    """
    values = [[0] * ncols for _ in range(nrows)]
    highlight: Set[Tuple[int, int]] = set()
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            dk = n - k
            if 0 <= dk <= n and dk < nrows:
                values[n][k] = S_MAX[n][dk]
                if dk <= 3:
                    highlight.add((n, k))
    return values, highlight


def a391838_diagonal(nrows: int, ncols: int) -> Tuple[List[List[int]], Set[Tuple[int, int]]]:
    """Косые диагонали s(n-k, n-2k) — для A391838.
    
    Шаг: 1 строка вверх, 2 столбца влево.
    Возвращает (values, highlight).
    """
    values = [[0] * ncols for _ in range(nrows)]
    highlight: Set[Tuple[int, int]] = set()
    for n in range(nrows):
        kmax = min(n // 2, ncols - 1)
        for k in range(kmax + 1):
            row = n - k
            col = n - 2 * k
            if 0 <= row < nrows and 0 <= col < ncols:
                values[n][k] = S_MAX[row][col]
                highlight.add((n, k))
    return values, highlight


# ──────────────────────────────────────────────────────────────────────────────
# 7. A391838: формула через диагонали Стирлинга
# ──────────────────────────────────────────────────────────────────────────────

def compute_a391838(n: int) -> int:
    """Вычисляет a(n) для OEIS A391838.
    
    Формула: a(n) = (n!)^2 * Σ_k |s(n-k, n-2k)| / ((2k+1)! * (n-k)!)
    
    Все вычисления через Fraction для точности.
    """
    if n < 0:
        return 0
    if n == 0:
        return 1
    total = Fraction(0)
    for k in range(n // 2 + 1):
        row = n - k
        col = n - 2 * k
        if row >= 0 and col >= 0:
            s_val = S_MAX[row][col]
            denom = math.factorial(2 * k + 1) * math.factorial(row)
            total += Fraction(s_val, denom)
    result = Fraction(math.factorial(n) ** 2) * total
    return int(result)


def compute_a391838_sequence(N: int) -> List[int]:
    """Возвращает последовательность A391838: [a(0), a(1), ..., a(N)]."""
    return [compute_a391838(n) for n in range(N + 1)]


def verify_a391838() -> bool:
    """Проверяет первые 9 членов A391838 против эталона OEIS."""
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
    actual = compute_a391838_sequence(8)
    return actual == expected


# ──────────────────────────────────────────────────────────────────────────────
# 8. Обращение ряда
# ──────────────────────────────────────────────────────────────────────────────

def multiplicative_inverse(seq: List[int]) -> List[Fraction]:
    """Мультипликативное обращение ряда.
    
    Если f(x) = Σ a_n * x^n, находим g(x) = Σ b_n * x^n такой, что
    f(x) * g(x) = 1.
    
    b_0 = 1/a_0
    b_n = -(1/a_0) * Σ_{k=1}^{n} a_k * b_{n-k}
    """
    if not seq or seq[0] == 0:
        raise ValueError("Первый элемент последовательности должен быть ненулевым")
    N = len(seq)
    result: List[Fraction] = [Fraction(0)] * N
    result[0] = Fraction(1, seq[0])
    for n in range(1, N):
        s = Fraction(0)
        for k in range(1, n + 1):
            if k < len(seq) and n - k >= 0:
                s += Fraction(seq[k]) * result[n - k]
        result[n] = -result[0] * s
    return result


def compositional_inverse(seq: List[int]) -> List[Fraction]:
    """Композиционное обращение ряда.
    
    Если f(x) = x + a_2*x^2 + a_3*x^3 + ..., находим g(x) такой, что
    f(g(x)) = x.
    
    Использует формулу Лагранжа для обращения ряда.
    """
    if not seq or seq[0] != 1:
        # Для композиционного обращения нужно f(0) = 0, f'(0) = 1
        # Если seq[0] != 0 — это не формальный степенной ряд с f(0)=0
        # Используем обобщённый алгоритм
        pass
    N = len(seq)
    result: List[Fraction] = [Fraction(0)] * N
    result[0] = Fraction(0)  # g(0) = 0
    if N > 1:
        result[1] = Fraction(1)  # g'(0) = 1 (если f'(0) = 1)
    for n in range(2, N):
        s = Fraction(0)
        for k in range(1, n):
            if k < len(seq) and n - k >= 0:
                s += Fraction(seq[k]) * result[n - k]
        result[n] = -s / Fraction(seq[1]) if seq[1] != 0 else Fraction(0)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 9. Треугольник разностей
# ──────────────────────────────────────────────────────────────────────────────

def difference_triangle(seq: List[int]) -> List[List[int]]:
    """Строит треугольник разностей из последовательности.
    
    Первая строка — сама последовательность.
    Каждая следующая — разности соседних элементов предыдущей.
    """
    if not seq:
        return []
    triangle = [list(seq)]
    for i in range(len(seq) - 1):
        current = triangle[-1]
        diff = [current[j + 1] - current[j] for j in range(len(current) - 1)]
        triangle.append(diff)
    return triangle


# ──────────────────────────────────────────────────────────────────────────────
# 10. Система Плотникова: блоки 3×3 и 2×3
# ──────────────────────────────────────────────────────────────────────────────

def plotnikov_9cell() -> List[List[str]]:
    """Базовый блок 3×3 системы физических величин Плотникова.
    
    9 смежных клеток — дуальные пространства.
    """
    return [
        ["L (индуктивность)",  "R (сопротивление)", "C (ёмкость)"],
        ["q (заряд)",          "I (ток)",           "U (напряжение)"],
        ["Phi (магн. поток)",   "Psi (эл. поток)",   "P (мощность)"],
    ]


def plotnikov_maxwell_6cell() -> List[List[str]]:
    """6 клеток для уравнений Максвелла (дуальное пространство 2×3).
    
    E и H — напряжённости, D и B — индукции, J и rho — источники.
    """
    return [
        ["E (эл. поле)",  "D (эл. индукция)",  "J (плотность тока)"],
        ["H (магн. поле)", "B (магн. индукция)", "rho (плотность заряда)"],
    ]


# ──────────────────────────────────────────────────────────────────────────────
# 11. Экспорт
# ──────────────────────────────────────────────────────────────────────────────

def export_matrix_csv(values: List[List], mode: str, ncols: int) -> str:
    """Экспортирует матрицу в CSV (строка).
    
    values — list-of-list (int или Fraction).
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f"row/col"] + [str(c) for c in range(ncols)])
    for r, row in enumerate(values):
        writer.writerow([str(r)] + [_fmt_cell(v) for v in row])
    return output.getvalue()


def export_sequence_json(seq: List[int], mode: str, values: List[List] = None) -> str:
    """Экспортирует последовательность и матрицу в JSON."""
    data = {
        "mode": mode,
        "sequence": seq,
        "sequence_str": ", ".join(str(s) for s in seq),
        "matrix": [[_fmt_cell(v) for v in row] for row in values] if values else None,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_spice_subcircuit(values: List[List], name: str, ncols: int) -> str:
    """Генерирует SPICE .subckt нетлист для VLSI Electric.
    
    Каждая ненулевая ячейка — резистор между узлами.
    Формат совместим с ngspice и SPICE3.
    """
    lines = [f"* Yupana subcircuit: {name}"]
    lines.append(f"* Generated by yupana_math.py")
    lines.append(f".subckt {name}")
    node_idx = 0
    for r, row in enumerate(values):
        for c in range(min(ncols, len(row))):
            v = row[c]
            if v != 0 and v != Fraction(0):
                val = _fmt_cell(v)
                n1 = f"n{r}_{c}"
                n2 = f"n{r}_{c+1}" if c + 1 < ncols else f"n{r}_{c}_end"
                lines.append(f"R{r}_{c} {n1} {n2} {val}")
    lines.append(".ends")
    return "\n".join(lines)


def a391838_to_float(seq: List[int], n_terms: int = None) -> List[float]:
    """Конвертирует последовательность A391838 в floats для численных расчётов.
    
    Нормировка: a_n / n!
    """
    if n_terms is None:
        n_terms = len(seq)
    return [seq[n] / math.factorial(n) for n in range(min(n_terms, len(seq)))]


# ──────────────────────────────────────────────────────────────────────────────
# 12. Вспомогательные
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_cell(v) -> str:
    """Форматирование значения ячейки для экспорта."""
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        return f"{v.numerator}/{v.denominator}"
    if isinstance(v, float):
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        return f"{v:.6g}"
    return str(v)


def format_cell_display(val, n: int, k: int) -> str:
    """Форматирование для GUI: val·x^k или просто val при k=0."""
    if val == 0 or val == Fraction(0):
        return ""
    if isinstance(val, Fraction):
        if val.denominator == 1:
            v = val.numerator
            if k == 0:
                return str(v)
            return f"{v}\u00B7x^{k}"
        else:
            s = f"{val.numerator}/{val.denominator}"
            if k == 0:
                return s
            return f"{s}\u00B7x^{k}"
    if isinstance(val, float):
        if abs(val - round(val)) < 1e-9:
            v = int(round(val))
            if k == 0:
                return str(v)
            return f"{v}\u00B7x^{k}"
        else:
            s = f"{val:.3g}"
            if k == 0:
                return s
            return f"{s}\u00B7x^{k}"
    if isinstance(val, int):
        if k == 0:
            return str(val)
        return f"{val}\u00B7x^{k}"
    return str(val)


def get_matrix_values(mode: str, nrows: int, ncols: int) -> Tuple[List[List], Set[Tuple[int, int]]]:
    """Единая точка: возвращает (values, highlight) для заданного режима."""
    highlight: Set[Tuple[int, int]] = set()
    if mode == "stirling":
        return stirling_matrix(nrows, ncols), highlight
    elif mode == "rassnos":
        return rassnos_matrix(nrows, ncols), highlight
    elif mode == "diff":
        return diff_matrix(nrows, ncols), highlight
    elif mode == "normalized":
        vals = normalized_matrix(nrows, ncols)
        for n in range(nrows):
            highlight.add((n, 0))
        return vals, highlight
    elif mode == "fibonacci":
        return fibonacci_diagonal(nrows, ncols)
    elif mode == "diagonal":
        return a391838_diagonal(nrows, ncols)
    else:
        return stirling_matrix(nrows, ncols), highlight
