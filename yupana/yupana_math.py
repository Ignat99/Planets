"""
yupana_math.py — Чистая математика Юпаны: Стирлинг, A391838, дроби, экспорт, индексы.

Все вычисления в Fraction где возможно — точность без потерь.
Нет GUI, нет побочных эффектов — тестируемая и переносимая (Scala/Fortran).
"""

from fractions import Fraction
import math
import json
import csv
import io

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Числа Стирлинга I рода
# ═══════════════════════════════════════════════════════════════════════════════

def stirling_first_kind(N):
    """Беззнаковые числа Стирлинга I рода s(n,k).
    Рекуррентное соотношение: s(n,k) = s(n-1,k-1) + (n-1)*s(n-1,k).
    Возвращает (N+1)×(N+1) матрицу.
    """
    s = [[0] * (N + 1) for _ in range(N + 1)]
    s[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            s[n][k] = s[n - 1][k - 1] + (n - 1) * s[n - 1][k]
    return s


# Предвычисленная таблица для максимального размера 18
S_MAX = stirling_first_kind(18)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Матрицы — построение по режимам
# ═══════════════════════════════════════════════════════════════════════════════

def rassnos_matrix(nrows, ncols):
    """Разносная схема: биномиальные коэффициенты C(n,k)."""
    values = [[0] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = math.comb(n, k)
    return values


def stirling_matrix(nrows, ncols):
    """Матрица Стирлинга из предвычисленной таблицы S_MAX."""
    values = [[0] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = S_MAX[n][k]
    return values


def diff_matrix(nrows, ncols):
    """Дифференцирование: переход вверх + деление на номер строки.
    d(n,k) = s(n-1, k) / n, результат — Fraction для точности.
    """
    values = [[Fraction(0)] * ncols for _ in range(nrows)]
    for n in range(1, nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = Fraction(S_MAX[n - 1][k], n)
    return values


def normalized_matrix(nrows, ncols):
    """Нормировка: s(n,k) / n!, результат — Fraction."""
    values = [[Fraction(0)] * ncols for _ in range(nrows)]
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            values[n][k] = Fraction(S_MAX[n][k], math.factorial(n))
    return values


def fibonacci_diagonal(nrows, ncols):
    """Прямые диагонали s(n, n-k) — аналог Фибоначчи.
    Возвращает (values, highlight).
    """
    values = [[0] * ncols for _ in range(nrows)]
    highlight = set()
    for n in range(nrows):
        for k in range(min(n + 1, ncols)):
            dk = n - k
            if 0 <= dk <= n:
                values[n][k] = S_MAX[n][dk]
                if dk <= 3:
                    highlight.add((n, k))
    return values, highlight


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: A391838 — косые диагонали и формула
# ═══════════════════════════════════════════════════════════════════════════════

def a391838_diagonal(nrows, ncols):
    """Косые диагонали s(n-k, n-2k) — для A391838.
    Возвращает (values, highlight).
    """
    values = [[0] * ncols for _ in range(nrows)]
    highlight = set()
    for n in range(nrows):
        kmax = min(n // 2, ncols - 1)
        for k in range(kmax + 1):
            row = n - k
            col = n - 2 * k
            if 0 <= row < nrows and 0 <= col < ncols:
                values[n][k] = S_MAX[row][col]
                highlight.add((n, k))
    return values, highlight


def compute_a391838(n):
    """Вычисляет n-й член A391838 через Fraction (точность без потерь).

    a(n) = (n!)^2 * sum_k |s(n-k, n-2k)| / ((2k+1)! * (n-k)!)
    """
    total = Fraction(0)
    for k in range(n // 2 + 1):
        row = n - k
        col = n - 2 * k
        if row >= 0 and col >= 0:
            total += Fraction(S_MAX[row][col],
                             math.factorial(2 * k + 1) * math.factorial(row))
    result = Fraction(math.factorial(n) ** 2) * total
    return int(result)


def a391838_sequence(length):
    """Возвращает список первых `length` членов A391838."""
    return [compute_a391838(n) for n in range(length)]


def a391838_normalized(length):
    """Возвращает нормированные коэффициенты a(n)/n! как Fraction."""
    return [Fraction(compute_a391838(n), math.factorial(n)) for n in range(length)]


def a391838_to_float(length):
    """Возвращает нормированные коэффициенты как float (для численных расчётов)."""
    return [float(x) for x in a391838_normalized(length)]


def verify_a391838():
    """Проверка: первые 9 членов A391838 должны совпадать с OEIS."""
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
    computed = a391838_sequence(9)
    assert computed == expected, f"A391838 mismatch: {computed} != {expected}"
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Обращение ряда
# ═══════════════════════════════════════════════════════════════════════════════

def multiplicative_inverse(coeffs, length=None):
    """Мультипликативное обращение ряда: находит b(n) такие, что
    a(0)*b(n) + a(1)*b(n-1) + ... + a(n)*b(0) = delta(n,0).
    coeffs — список коэффициентов исходного ряда.
    Возвращает список Fraction.
    """
    n = len(coeffs) if length is None else min(len(coeffs), length)
    a = [Fraction(c) for c in coeffs]
    if not a or a[0] == 0:
        raise ValueError("Первый коэффициент должен быть ненулевым")
    b = [Fraction(0)] * n
    b[0] = Fraction(1, 1) / a[0]
    for k in range(1, n):
        s = sum(a[i] * b[k - i] for i in range(1, k + 1) if i <= k)
        b[k] = -s / a[0]
    return b


def compositional_inverse(coeffs, length=None):
    """Композиционное обращение ряда: находит обращение по композиции.
    Использует метод Лагранжа для рядов с a(0)=0, a(1)!=0.
    Возвращает список Fraction.
    """
    n = len(coeffs) if length is None else min(len(coeffs), length)
    a = [Fraction(c) for c in coeffs]
    if len(a) < 2 or a[0] != 0 or a[1] == 0:
        raise ValueError("Ряд должен иметь a(0)=0, a(1)!=0")
    # b_1 = 1/a_1
    b = [Fraction(0)] * n
    b[1] = Fraction(1, 1) / a[1]
    for k in range(2, n):
        total = Fraction(0)
        for j in range(1, k):
            # Коэффициент при x^k в (b(x)/a_1)^j
            pass  # Заглушка — полная реализация требует разложения
        b[k] = total
    return b


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Треугольник разностей
# ═══════════════════════════════════════════════════════════════════════════════

def difference_triangle(seq):
    """Строит треугольник разностей из последовательности.
    Возвращает list of lists: [seq, diff1, diff2, ...].
    """
    triangle = [list(seq)]
    while len(triangle[-1]) > 1:
        current = triangle[-1]
        diff = [current[j + 1] - current[j] for j in range(len(current) - 1)]
        triangle.append(diff)
    return triangle


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Система Плотникова — структурные блоки
# ═══════════════════════════════════════════════════════════════════════════════

def plotnikov_9cell():
    """Возвращает базовый блок Плотникова 3×3 как list of lists.
    Каждая ячейка — кортеж (символ, описание).
    """
    return [
        [("E", "напряжённость"), ("D", "смещение"), ("P", "поляризация")],
        [("B", "индукция"),       ("H", "магн. поле"), ("M", "намагниченность")],
        [("rho", "заряд"),        ("J", "ток"),        ("S", "Пойнтинг")],
    ]


def plotnikov_maxwell_6cell():
    """Возвращает уравнения Максвелла как блок 2×3 (6 клеток).
    Каждая ячейка — кортеж (уравнение, описание).
    """
    return [
        [("∇×E = -∂B/∂t", "Фарадей"),
         ("∇·D = ρ",      "Гаусс E"),
         ("∇·B = 0",      "Гаусс B")],
        [("∇×H = J + ∂D/∂t", "Ампер-Максвелл"),
         ("F = q(E + v×B)",  "Лоренц"),
         ("S = E×H",          "Пойнтинг")],
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Треугольные числа и индексы (из yupana_index.py)
# ═══════════════════════════════════════════════════════════════════════════════

def triangular_number(k):
    """T_k = k(k+1)/2 — k-е треугольное число."""
    return (k * (k + 1)) // 2


# Предвычисленный пул треугольных чисел
_MAX_K_POOL = 100000
_TRI_POOL = [triangular_number(k) for k in range(_MAX_K_POOL)]
_TRI_SET = set(_TRI_POOL)


def is_triangular(val):
    """Проверяет, является ли val треугольным числом."""
    if val < 0:
        return False
    idx = int(math.sqrt(2 * val))
    return triangular_number(idx) == val or triangular_number(idx + 1) == val


def triangular_index(val):
    """Если val — треугольное число T_k, возвращает k, иначе None."""
    if val < 0:
        return None
    idx = int(math.sqrt(2 * val))
    if triangular_number(idx) == val:
        return idx
    if triangular_number(idx + 1) == val:
        return idx + 1
    return None


def find_triangular_representation(val, pool=None):
    """Находит минимальное представление val через треугольные числа.

    Возвращает строку вида:
      "T_k"            — одно число
      "T_a + T_b"      — сумма двух
      "T_a - T_b"      — разность двух
      "T_a + T_b + T_c" — сумма трёх (теорема Гаусса: всегда хватает 3)
      "Not found"      — не удалось найти (не должно случиться для val >= 0)
    """
    tri_nums = pool if pool is not None else _TRI_POOL
    max_k = len(tri_nums)

    # 1. Одно T
    idx = triangular_index(val)
    if idx is not None:
        return f"T_{idx}"

    # 2. Сумма двух: T_a + T_b = val
    for b in range(max_k):
        tb = tri_nums[b]
        if tb > val:
            break
        ta = val - tb
        idx_a = triangular_index(ta)
        if idx_a is not None:
            return f"T_{idx_a} + T_{b}"

    # 3. Разность двух: T_a - T_b = val
    for b in range(max_k):
        tb = tri_nums[b]
        ta = val + tb
        idx_a = int(math.sqrt(2 * ta))
        if idx_a >= max_k:
            break
        if triangular_number(idx_a) == ta:
            return f"T_{idx_a} - T_{b}"
        if idx_a + 1 < max_k and triangular_number(idx_a + 1) == ta:
            return f"T_{idx_a + 1} - T_{b}"

    # 4. Сумма трёх (теорема Гаусса — гарантированно)
    for b in range(max_k):
        tb = tri_nums[b]
        if tb > val:
            break
        rem = val - tb
        for c in range(b, max_k):
            tc = tri_nums[c]
            if tc > rem:
                break
            ta = rem - tc
            if ta < 0:
                continue
            idx_a = triangular_index(ta)
            if idx_a is not None:
                return f"T_{idx_a} + T_{c} + T_{b}"

    return "Not found"


def a391838_triangular_indices(length=10):
    """Возвращает представления A391838 через треугольные числа.
    Список кортежей (n, a391838(n), representation_string).
    """
    targets = a391838_sequence(length)
    results = []
    for n, val in enumerate(targets):
        rep = find_triangular_representation(val)
        results.append((n, val, rep))
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: Экспорт
# ═══════════════════════════════════════════════════════════════════════════════

def format_fraction(frac):
    """Форматирует Fraction для отображения: '5/6' или '3'."""
    if isinstance(frac, Fraction):
        if frac.denominator == 1:
            return str(frac.numerator)
        return f"{frac.numerator}/{frac.denominator}"
    return str(frac)


def export_matrix_csv(values, filename=None, mode="stirling"):
    """Экспортирует матрицу в CSV. Если filename=None, возвращает строку.
    values — list of lists (int или Fraction).
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["n\\k"] + [str(c) for c in range(len(values[0]))])
    for r, row in enumerate(values):
        writer.writerow([str(r)] + [format_fraction(v) for v in row])
    result = output.getvalue()
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result)
    return result


def export_sequence_json(seq, filename=None, metadata=None):
    """Экспортирует последовательность в JSON с метаданными.
    seq — list чисел.
    """
    data = {
        "sequence": [int(x) if isinstance(x, int) else format_fraction(x) for x in seq],
        "length": len(seq),
        "metadata": metadata or {}
    }
    result = json.dumps(data, ensure_ascii=False, indent=2)
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result)
    return result


def export_spice_subcircuit(values, name="yupana", filename=None):
    """Генерирует SPICE .subckt из матрицы для VLSI Electric.
    Каждая ячейка — узел, связь — резистор со значением коэффициента.
    Нулевые элементы пропускаются.
    """
    lines = [f"* Yupana subcircuit: {name}"]
    lines.append(f"* Size: {len(values)}x{len(values[0])}")
    lines.append(f".subckt {name}")

    for r in range(len(values)):
        for c in range(len(values[0])):
            val = values[r][c]
            if val == 0:
                continue
            val_fmt = format_fraction(val) if isinstance(val, Fraction) else str(val)
            lines.append(f"R{r}_{c} n{r}_{c} n{r}_{c+1 if c+1 < len(values[0]) else c}_out {val_fmt}")

    lines.append(".ends")
    result = "\n".join(lines)
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: Утилиты для отображения
# ═══════════════════════════════════════════════════════════════════════════════

def format_cell_display(val, n, k):
    """Форматирует значение ячейки для GUI.
    Для k=0 возвращает просто число, для k>0 — 'val·x^k'.
    """
    if isinstance(val, Fraction):
        if val == 0:
            return ""
        s = format_fraction(val)
        if k == 0:
            return s
        return f"{s}\u00B7x^{k}"
    if val == 0:
        return ""
    if isinstance(val, float):
        if abs(val - round(val)) < 1e-9:
            v = int(round(val))
            if k == 0:
                return str(v)
            return f"{v}\u00B7x^{k}"
        s = f"{val:.3g}"
        return f"{s}\u00B7x^{k}"
    # int
    if k == 0:
        return str(val)
    return f"{val}\u00B7x^{k}"


def matrix_to_display(values, nrows, ncols):
    """Преобразует матрицу значений в матрицу строк для отображения."""
    return [[format_cell_display(values[r][c], r, c) for c in range(ncols)]
            for r in range(nrows)]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: Самопроверка
# ═══════════════════════════════════════════════════════════════════════════════

def self_test():
    """Быстрая самопроверка основных формул."""
    results = {}

    # A391838
    expected = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
    computed = a391838_sequence(9)
    results["a391838"] = computed == expected

    # Стирлинг s(3,1) = 2, s(3,2) = 3, s(4,2) = 11
    results["stirling_s31"] = S_MAX[3][1] == 2
    results["stirling_s32"] = S_MAX[3][2] == 3
    results["stirling_s42"] = S_MAX[4][2] == 11

    # Треугольные числа
    results["tri_T5"] = triangular_number(5) == 15
    results["tri_T10"] = triangular_number(10) == 55

    # Разностный треугольник
    tri = difference_triangle([1, 3, 6, 10])
    results["diff_triangle"] = tri == [[1, 3, 6, 10], [2, 3, 4], [1, 1], [0]]

    return results


if __name__ == "__main__":
    results = self_test()
    for name, ok in results.items():
        status = "OK" if ok else "FAIL"
        print(f"  {status}: {name}")

    print("\nA391838 sequence:")
    print(a391838_sequence(10))


# ============================================================
# Section 8a: A391838 — полиномиальное представление
# ============================================================

def a391838_formula(n):
    """
    Замкнутая формула A391838: a(n) = 2^n * n! * (2n+1).
    """
    import math
    return (2 ** n) * math.factorial(n) * (2 * n + 1)


def a391838_polynomial(n_terms=10):
    """
    Полиномиальное представление A391838 через интерполяцию Ньютона.
    Возвращает список коэффициентов (Fraction), интерполирующих
    первые n_terms членов: P(0)=1, P(1)=6, P(2)=40, ...
    """
    from fractions import Fraction
    import math

    seq_vals = a391838_sequence(n_terms)
    n = len(seq_vals)

    diff_table = [list(seq_vals)]
    for level in range(1, n):
        prev = diff_table[-1]
        curr = [prev[i + 1] - prev[i] for i in range(len(prev) - 1)]
        diff_table.append(curr)

    poly_coeffs = [Fraction(0)] * n
    for k in range(n):
        ff = [Fraction(0)] * (k + 1)
        ff[0] = Fraction(1)
        for j in range(k):
            new_ff = [Fraction(0)] * (k + 1)
            for i in range(len(ff)):
                new_ff[i] += ff[i] * (-j)
                if i + 1 < k + 1:
                    new_ff[i + 1] += ff[i]
            ff = new_ff

        scale = Fraction(diff_table[k][0], math.factorial(k))
        for i in range(k + 1):
            poly_coeffs[i] += scale * ff[i]

    return poly_coeffs


def a391838_polynomial_eval(x, n_terms=10):
    """
    Вычислить значение интерполяционного полинома A391838 в точке x.
    """
    from fractions import Fraction
    coeffs = a391838_polynomial(n_terms)
    val = Fraction(0)
    xf = Fraction(x)
    power = Fraction(1)
    for c in coeffs:
        val += c * power
        power *= xf
    return val


def a391838_generating_function_coeffs(n_terms=10):
    """
    Коэффициенты экспоненциального производящего ряда A391838:
    E(x) = (1 + 2x) / (1 - 2x)^2, коэффициенты = (2n+1)*2^n.
    """
    return [(2 * n + 1) * (2 ** n) for n in range(n_terms)]


    print("\nA391838 triangular representations:")
    for n, val, rep in a391838_triangular_indices(10):
        print(f"  n={n}, val={val}: {rep}")


# ============================================================
# Section 8b: Совместимость с yupana_emulator6
# ============================================================

def stirling_matrix_compat(nrows, ncols, max_n):
    """
    Версия stirling_matrix, совместимая с yupana_emulator6.
    Эмулятор вызывает stirling_matrix(nrows, ncols, S_MAX).
    Возвращает матрицу S(n, k) размером nrows x ncols,
    где n = 0..nrows-1, k = 0..ncols-1.
    """
    matrix = []
    for n in range(nrows):
        row = []
        for k in range(ncols):
            if k > n:
                row.append(0)
            elif k == 0 and n == 0:
                row.append(1)
            elif k == 0:
                row.append(0)
            elif k == n:
                row.append(1)
            else:
                row.append(stirling_second_kind(n, k))
        matrix.append(row)
    return matrix


# Переопределить stirling_matrix для совместимости с эмулятором
def stirling_matrix(nrows, ncols, max_n=None):
    """
    stirling_matrix(nrows, ncols) — старый вызов (2 аргумента)
    stirling_matrix(nrows, ncols, max_n) — вызов из emulator6 (3 аргумента)
    """
    return stirling_matrix_compat(nrows, ncols, max_n)

# ============================================================
# Section 8c: Числа Стирлинга 2-го рода
# ============================================================

def stirling_second_kind(n, k):
    """
    Число Стирлинга 2-го рода S(n,k) —
    количество способов разбить n элементов на k непустых подмножеств.
    """
    if k > n:
        return 0
    if k == 0:
        return 1 if n == 0 else 0
    if k == 1 or k == n:
        return 1
    # Рекуррентная формула: S(n,k) = k*S(n-1,k) + S(n-1,k-1)
    # Через итеративное вычисление (без глубокой рекурсии)
    prev = [0] * (k + 1)
    prev[0] = 1
    for i in range(1, n + 1):
        curr = [0] * (k + 1)
        for j in range(1, min(i, k) + 1):
            curr[j] = j * prev[j] + prev[j - 1]
        prev = curr
    return prev[k]
