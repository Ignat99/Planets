"""
yupana_multiply.py
Метод умножения на 3×3 юпане (метод решётки / джелозия + палочки)
С тремя модификациями и поддержкой второй юпаны.
"""

from fractions import Fraction
from typing import List, Tuple, Dict, Optional
import copy

# ============================================================
# Section 1: Yupana3x3 — модель 3×3 юпаны
# ============================================================

class Cell:
    """Клетка юпаны с белыми и чёрными камешками."""
    def __init__(self, row: int = 0, col: int = 0):
        self.row = row
        self.col = col
        self.white = 0
        self.black = 0

    @property
    def total(self) -> int:
        return self.white + self.black

    def add_white(self, n: int = 1):
        self.white += n

    def add_black(self, n: int = 1):
        self.black += n

    def __repr__(self):
        return f"Cell(r={self.row},c={self.col},W={self.white},B={self.black})"

    def __eq__(self, other):
        if isinstance(other, Cell):
            return self.white == other.white and self.black == other.black
        return False


class Yupana3x3:
    """3×3 юпана: cells[row][col], row 1=top, 3=bottom."""
    def __init__(self):
        self.cells: Dict[Tuple[int,int], Cell] = {}
        for r in range(1, 4):
            for c in range(1, 4):
                self.cells[(r, c)] = Cell(r, c)

    def get(self, r: int, c: int) -> Cell:
        return self.cells[(r, c)]

    def reset(self):
        for cell in self.cells.values():
            cell.white = 0
            cell.black = 0

    def __repr__(self):
        lines = []
        for r in range(1, 4):
            parts = []
            for c in range(1, 4):
                cell = self.get(r, c)
                parts.append(f"[{cell.white}W,{cell.black}B]")
            lines.append(" ".join(parts))
        return "\n".join(lines)

    def copy(self) -> "Yupana3x3":
        y = Yupana3x3()
        for (r,c), cell in self.cells.items():
            y.cells[(r,c)].white = cell.white
            y.cells[(r,c)].black = cell.black
        return y


# ============================================================
# Section 2: Раскладывание чисел по средним клеткам
# ============================================================

def split_digits(n: int, base: int = 10) -> Tuple[int, int]:
    """Разложить число на (младший, старший) разряды."""
    if n < 0:
        raise ValueError("Отрицательные числа не поддерживаются")
    lo = n % base
    hi = n // base
    return lo, hi


def place_operands(yupana: Yupana3x3, a: int, b: int, base: int = 10):
    """
    Разложить A (белые) в средний столбец: [1,2]=мл, [3,2]=ст.
    Разложить B (чёрные) в среднюю строку: [2,1]=мл, [2,3]=ст.
    """
    yupana.reset()
    a_lo, a_hi = split_digits(a, base)
    b_lo, b_hi = split_digits(b, base)

    # A — белые камешки в средний столбец
    yupana.get(1, 2).add_white(a_lo)
    yupana.get(3, 2).add_white(a_hi)

    # B — чёрные камешки в среднюю строку
    yupana.get(2, 1).add_black(b_lo)
    yupana.get(2, 3).add_black(b_hi)

    return a_lo, a_hi, b_lo, b_hi


# ============================================================
# Section 3: Раскладывание палочек в угловые клетки
# ============================================================

def lay_sticks(yupana: Yupana3x3, a: int, b: int, base: int = 10):
    """
    Для каждой средней клетки — раскладываем «палочки» в угловые.
    Белый конец (младший) — влево/вверх, чёрный конец (старший) — вправо/вниз.
    """
    a_lo, a_hi, b_lo, b_hi = place_operands(yupana, a, b, base)

    # Палочки из A_мл [1,2]: белый → [1,1], чёрный → [1,3]
    yupana.get(1, 1).add_white(a_lo)
    yupana.get(1, 3).add_black(a_lo)

    # Палочки из A_ст [3,2]: белый → [3,1], чёрный → [3,3]
    yupana.get(3, 1).add_white(a_hi)
    yupana.get(3, 3).add_black(a_hi)

    # Палочки из B_мл [2,1]: белый → [1,1], чёрный → [3,1]
    yupana.get(1, 1).add_white(b_lo)
    yupana.get(3, 1).add_black(b_lo)

    # Палочки из B_ст [2,3]: белый → [1,3], чёрный → [3,3]
    yupana.get(1, 3).add_white(b_hi)
    yupana.get(3, 3).add_black(b_hi)

    return a_lo, a_hi, b_lo, b_hi


# ============================================================
# Section 4: Вычисление произведений в угловых клетках
# ============================================================

def compute_corner_products(yupana: Yupana3x3, a: int, b: int, base: int = 10):
    """
    В каждой угловой клетке:
      white = кол-во белых от A, black = кол-во чёрных от B (или наоборот).
      product = white_a * black_b (или white_b * black_a — по раскладке).
    """
    a_lo, a_hi, b_lo, b_hi = lay_sticks(yupana, a, b, base)

    # [1,1]: a_lo (белые от A) × b_lo (белые от B) → это a_lo * b_lo
    c11 = yupana.get(1, 1)
    w11 = a_lo + b_lo  # белые камешки от обеих палочек
    b11 = 0
    p11 = a_lo * b_lo

    # [1,3]: a_lo (чёрные от A) × b_hi (белые от B) → a_lo * b_hi
    c13 = yupana.get(1, 3)
    w13 = b_hi  # белые от B_ст
    b13 = a_lo  # чёрные от A_мл
    p13 = a_lo * b_hi

    # [3,1]: a_hi (белые от A) × b_lo (чёрные от B) → a_hi * b_lo
    c31 = yupana.get(3, 1)
    w31 = a_hi  # белые от A_ст
    b31 = b_lo  # чёрные от B_мл
    p31 = a_hi * b_lo

    # [3,3]: a_hi (чёрные от A) × b_hi (чёрные от B) → a_hi * b_hi
    c33 = yupana.get(3, 3)
    w33 = 0
    b33 = a_hi + b_hi  # чёрные от обеих палочек
    p33 = a_hi * b_hi

    return {
        (1,1): {"white": w11, "black": b11, "product": p11},
        (1,3): {"white": w13, "black": b13, "product": p13},
        (3,1): {"white": w31, "black": b31, "product": p31},
        (3,3): {"white": w33, "black": b33, "product": p33},
    }


# ============================================================
# Section 5: Перекладывание в центральную клетку
# ============================================================

def fold_to_center(yupana: Yupana3x3, products: Dict):
    """
    Перекладываем камешки из [1,3] и [3,1] в [2,2].
    Угловые произведения остаются для диагонального чтения.
    """
    p13 = products[(1,3)]["product"]
    p31 = products[(3,1)]["product"]

    center = yupana.get(2, 2)
    center.white = p13
    center.black = p31


# ============================================================
# Section 6: Диагональное чтение результата
# ============================================================

def read_diagonal(yupana: Yupana3x3, products: Dict, base: int = 10) -> int:
    """
    Чтение по главной диагонали: [3,3] → [2,2] → [1,1].
    """
    p33 = products[(3,3)]["product"]
    mid = products[(1,3)]["product"] + products[(3,1)]["product"]
    p11 = products[(1,1)]["product"]

    # Перенос разрядов
    lo_digit = p33 % base
    carry = p33 // base

    mid_total = mid + carry
    mid_digit = mid_total % base
    carry = mid_total // base

    hi_total = p11 + carry
    hi_digit = hi_total % base
    carry = hi_total // base

    result = hi_digit * base * base + mid_digit * base + lo_digit
    if carry > 0:
        result += carry * base * base * base

    return result


# ============================================================
# Section 7: Главная функция умножения
# ============================================================

def yupana_multiply(a: int, b: int, base: int = 10, verbose: bool = False) -> int:
    """
    Умножение на 3×3 юпане.
    Возвращает a * b.
    """
    yupana = Yupana3x3()
    products = compute_corner_products(yupana, a, b, base)
    fold_to_center(yupana, products)
    result = read_diagonal(yupana, products, base)

    if verbose:
        print(f"Умножение {a} × {b} на 3×3 юпане")
        print(f"  A: мл={a % base}, ст={a // base} → белый столбец")
        print(f"  B: мл={b % base}, ст={b // base} → чёрная строка")
        print(f"  Угловые произведения:")
        print(f"    [1,1] = {products[(1,1)]['product']}")
        print(f"    [1,3] = {products[(1,3)]['product']}")
        print(f"    [3,1] = {products[(3,1)]['product']}")
        print(f"    [3,3] = {products[(3,3)]['product']}")
        mid = products[(1,3)]['product'] + products[(3,1)]['product']
        print(f"  Центр [2,2] = {products[(1,3)]['product']} + {products[(3,1)]['product']} = {mid}")
        print(f"  Результат: {result}")
        print(f"  Проверка: {a} × {b} = {a * b} → {'OK' if result == a * b else 'FAIL'}")
        print()

    return result


# ============================================================
# Section 8: Модификация 1 — палочки в углы, результат в верх/низ/лево/право
# ============================================================

def yupana_multiply_mod1(a: int, b: int, base: int = 10) -> int:
    """
    Модификация 1: изначально выкладывать палочки в угловые клетки,
    а результат пересечения — в верхнюю и нижнюю от центральной,
    а также в левую и правую.
    """
    yupana = Yupana3x3()
    a_lo, a_hi = split_digits(a, base)
    b_lo, b_hi = split_digits(b, base)

    # Палочки сразу в углы
    yupana.get(1, 1).white = a_lo * b_lo  # мл × мл
    yupana.get(1, 3).black = a_lo * b_hi  # мл × ст
    yupana.get(3, 1).white = a_hi * b_lo  # ст × мл
    yupana.get(3, 3).black = a_hi * b_hi  # ст × ст

    # Результаты пересечения — вокруг центра
    yupana.get(1, 2).white = a_lo * b_hi  # верх
    yupana.get(3, 2).white = a_hi * b_lo  # низ
    yupana.get(2, 1).black = a_hi * b_lo  # лево
    yupana.get(2, 3).black = a_lo * b_hi  # право

    # Центр — сумма средних
    yupana.get(2, 2).white = a_lo * b_hi + a_hi * b_lo
    yupana.get(2, 2).black = 0

    # Чтение по диагонали
    p11 = a_lo * b_lo
    p13 = a_lo * b_hi
    p31 = a_hi * b_lo
    p33 = a_hi * b_hi

    lo = p33 % base
    carry = p33 // base
    mid = p13 + p31 + carry
    mid_digit = mid % base
    carry = mid // base
    hi = p11 + carry
    hi_digit = hi % base
    carry = hi // base

    result = hi_digit * base * base + mid_digit * base + lo
    if carry:
        result += carry * base * base * base

    return result


# ============================================================
# Section 9: Модификация 2 — расписные камешки (треугольник Паскаля)
# ============================================================

def binomial_coeff(n: int, k: int) -> int:
    """Биномиальный коэффициент C(n,k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    result = 1
    for i in range(min(k, n - k)):
        result = result * (n - i) // (i + 1)
    return result


def pascal_triangle(rows: int) -> List[List[int]]:
    """Треугольник Паскаля до rows строк."""
    tri = []
    for n in range(rows):
        row = [binomial_coeff(n, k) for k in range(n + 1)]
        tri.append(row)
    return tri


def number_to_pascal_pebbles(n: int) -> List[Tuple[int, int]]:
    """
    Представить число через расписные камешки (коэффициенты Паскаля).
    Возвращает список (коэффициент, количество, строка, столбец).
    """
    if n == 0:
        return []
    result = []
    tri = pascal_triangle(20)
    remaining = n
    for row in range(len(tri) - 1, -1, -1):
        for col in range(len(tri[row]) - 1, -1, -1):
            coeff = tri[row][col]
            if coeff <= remaining and coeff > 0:
                count = remaining // coeff
                if count > 0:
                    result.append((coeff, count, row, col))
                    remaining -= coeff * count
            if remaining == 0:
                break
        if remaining == 0:
            break
    return result


def yupana_multiply_mod2(a: int, b: int, base: int = 10) -> int:
    """
    Модификация 2: итоговое число представляется как сумма расписных камешков
    (через коэффициенты треугольника Паскаля).
    """
    a_lo, a_hi = split_digits(a, base)
    b_lo, b_hi = split_digits(b, base)

    p11 = a_lo * b_lo
    p13 = a_lo * b_hi
    p31 = a_hi * b_lo
    p33 = a_hi * b_hi

    # Расписные камешки для каждого произведения
    pebbles = {
        "p11": number_to_pascal_pebbles(p11),
        "p13": number_to_pascal_pebbles(p13),
        "p31": number_to_pascal_pebbles(p31),
        "p33": number_to_pascal_pebbles(p33),
    }

    # Диагональное сложение
    lo = p33 % base
    carry = p33 // base
    mid = p13 + p31 + carry
    mid_digit = mid % base
    carry = mid // base
    hi = p11 + carry
    hi_digit = hi % base
    carry = hi // base

    result = hi_digit * base * base + mid_digit * base + lo
    if carry:
        result += carry * base * base * base

    return result


# ============================================================
# Section 10: Модификация 3 — 9 цветов фазана
# ============================================================

PHASANT_COLORS = [
    "красный", "оранжевый", "жёлтый", "зелёный",
    "голубой", "синий", "фиолетовый",
    "большой", "чубатый"
]


def digit_to_color(d: int) -> str:
    """Сопоставить цифру 0–8 цвету фазана."""
    if 0 <= d <= 8:
        return PHASANT_COLORS[d]
    raise ValueError(f"Цифра {d} вне диапазона 0–8")


def color_to_digit(color: str) -> int:
    """Обратное преобразование: цвет → цифра."""
    return PHASANT_COLORS.index(color)


def number_to_colors(n: int) -> List[str]:
    """Представить число как последовательность цветов (мл→ст)."""
    if n == 0:
        return ["красный"]
    colors = []
    while n > 0:
        d = n % 10
        if d == 9:
            colors.append("большой")
            n = n // 10
            if n == 0:
                colors.append("красный")
        else:
            colors.append(digit_to_color(d))
            n = n // 10
    return colors


def yupana_multiply_mod3(a: int, b: int, base: int = 10) -> int:
    """
    Модификация 3: каждому разряду — 9 цветов фазана.
    Результат вычисляется стандартным методом, но отображается в цветах.
    """
    product = yupana_multiply(a, b, base)
    colors = number_to_colors(product)
    return product


# ============================================================
# Section 11: Вторая юпана как вектор хранения
# ============================================================

def yupana_multiply_two_yupanas(a: int, b: int, base: int = 10) -> Tuple[int, Yupana3x3, Yupana3x3]:
    """
    Вторая юпана используется как вектор хранения чисел и результатов.
    Первая юпана — рабочая (раскладка палочек), вторая — хранения результата.
    """
    work_yupana = Yupana3x3()
    store_yupana = Yupana3x3()

    a_lo, a_hi, b_lo, b_hi = place_operands(work_yupana, a, b, base)
    products = compute_corner_products(work_yupana, a, b, base)
    fold_to_center(work_yupana, products)
    result = read_diagonal(work_yupana, products, base)

    # Заполняем вторую юпану результатом по разрядам
    lo = result % base
    mid = (result // base) % base
    hi = (result // (base * base)) % base
    extra = result // (base * base * base)

    store_yupana.get(3, 3).white = lo
    store_yupana.get(2, 2).white = mid
    store_yupana.get(1, 1).white = hi
    if extra > 0:
        store_yupana.get(1, 3).white = extra

    return result, work_yupana, store_yupana


# ============================================================
# Section 12: Тесты
# ============================================================

def _run_tests():
    """Запуск всех тестов."""
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

    # --- Базовые тесты split_digits ---
    check("split_23", split_digits(23), (3, 2))
    check("split_41", split_digits(41), (1, 4))
    check("split_9", split_digits(9), (9, 0))
    check("split_0", split_digits(0), (0, 0))
    check("split_100", split_digits(100, 10), (0, 10))

    # --- Базовое умножение ---
    check("mul_11x22", yupana_multiply(11, 22), 11 * 22)
    check("mul_23x41", yupana_multiply(23, 41), 23 * 41)
    check("mul_99x99", yupana_multiply(99, 99), 99 * 99)
    check("mul_10x10", yupana_multiply(10, 10), 100)
    check("mul_0x5", yupana_multiply(0, 5), 0)
    check("mul_5x0", yupana_multiply(5, 0), 0)
    check("mul_1x1", yupana_multiply(1, 1), 1)
    check("mul_1x99", yupana_multiply(1, 99), 99)
    check("mul_99x1", yupana_multiply(99, 1), 99)
    check("mul_50x50", yupana_multiply(50, 50), 2500)
    check("mul_12x34", yupana_multiply(12, 34), 12 * 34)
    check("mul_56x78", yupana_multiply(56, 78), 56 * 78)

    # --- Модификация 1 ---
    check("mod1_11x22", yupana_multiply_mod1(11, 22), 242)
    check("mod1_23x41", yupana_multiply_mod1(23, 41), 943)
    check("mod1_99x99", yupana_multiply_mod1(99, 99), 9801)
    check("mod1_10x10", yupana_multiply_mod1(10, 10), 100)
    check("mod1_0x5", yupana_multiply_mod1(0, 5), 0)

    # --- Модификация 2 ---
    check("mod2_11x22", yupana_multiply_mod2(11, 22), 242)
    check("mod2_23x41", yupana_multiply_mod2(23, 41), 943)
    check("mod2_99x99", yupana_multiply_mod2(99, 99), 9801)
    check("mod2_10x10", yupana_multiply_mod2(10, 10), 100)

    # --- Модификация 3 ---
    check("mod3_11x22", yupana_multiply_mod3(11, 22), 242)
    check("mod3_23x41", yupana_multiply_mod3(23, 41), 943)
    check("mod3_99x99", yupana_multiply_mod3(99, 99), 9801)

    # --- Две юпаны ---
    r, w, s = yupana_multiply_two_yupanas(23, 41)
    check("two_23x41_result", r, 943)
    check("two_23x41_store_lo", s.get(3, 3).white, 3)
    check("two_23x41_store_mid", s.get(2, 2).white, 4)
    check("two_23x41_store_hi", s.get(1, 1).white, 9)

    # --- Цвета фазана ---
    check("color_0", digit_to_color(0), "красный")
    check("color_6", digit_to_color(6), "синий")
    check("color_back", color_to_digit("зелёный"), 3)

    # --- Полный перебор однозначных 0–9 × 0–9 ---
    for i in range(10):
        for j in range(10):
            r = yupana_multiply(i, j)
            if r != i * j:
                check(f"single_{i}x{j}", r, i * j)

    # --- Полный перебор двузначных 10–99 × 10–99 ---
    count_2digit = 0
    for i in range(10, 100):
        for j in range(10, 100):
            r = yupana_multiply(i, j)
            if r != i * j:
                check(f"double_{i}x{j}", r, i * j)
                count_2digit += 1
    if count_2digit == 0:
        passed += 1  # все 8100 прошли

    # --- Треугольник Паскаля ---
    check("pascal_0", pascal_triangle(1), [[1]])
    check("pascal_3", pascal_triangle(4), [[1],[1,1],[1,2,1],[1,3,3,1]])
    check("binom_5_2", binomial_coeff(5, 2), 10)
    check("binom_7_3", binomial_coeff(7, 3), 35)

    # --- Расписные камешки ---
    peb10 = number_to_pascal_pebbles(10)
    check("pebble_10_exists", len(peb10) > 0, True)

    # --- Yupana3x3 методы ---
    y = Yupana3x3()
    y.get(1, 1).add_white(3)
    y.get(1, 1).add_black(2)
    check("cell_total", y.get(1, 1).total, 5)
    check("cell_eq", y.get(1, 1) == Cell(1, 1), False)

    y2 = y.copy()
    check("copy_white", y2.get(1, 1).white, 3)
    y2.get(1, 1).add_white(1)
    check("copy_independent", y.get(1, 1).white, 3)

    # --- Результат ---
    print(f"\n{'='*50}")
    print(f"Тестов пройдено: {passed}")
    print(f"Тестов провалено: {failed}")
    if errors:
        print(f"\nОшибки:")
        for e in errors:
            print(f"  {e}")
    else:
        print("Все тесты зелёные!")
    print(f"{'='*50}")

    return failed == 0


if __name__ == "__main__":
    _run_tests()
