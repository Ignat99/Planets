"""
yupana_lattice_hook.py
Чистый хук для встраивания умножения методом решётки в эмулятор юпаны.

Стандарт встраивания (как для oscillator_to_yupana_bottom_row):

    from yupana_lattice_hook import lattice_to_yupana, lattice_to_bottom_row

    # Полная интеграция: левая таблица — раскладка, правая — результат
    left_row, right_row, result, info = lattice_to_yupana(23, 41)

    # Упрощённая: только результат в нижнюю строку
    bottom = lattice_to_bottom_row(23, 41)
"""

from yupana_lattice import lattice_multiply


def lattice_to_yupana(a: int, b: int, base: int = 10):
    """
    Умножение методом решётки для эмулятора юпаны.

    Возвращает:
        left_row  — 4 значения для левой таблицы (раскладка 2x2 решётки)
        right_row — значения для правой таблицы (результат по разрядам)
        result    — int, произведение a * b
        info      — dict с метаданными
    """
    result = lattice_multiply(a, b, base)

    a_lo = a % base
    a_hi = a // base
    b_lo = b % base
    b_hi = b // base

    p11 = a_lo * b_lo
    p12 = a_lo * b_hi
    p21 = a_hi * b_lo
    p22 = a_hi * b_hi

    left_row = [
        (p22 // base) * base + (p22 % base),
        (p12 // base) * base + (p12 % base),
        (p21 // base) * base + (p21 % base),
        (p11 // base) * base + (p11 % base),
    ]

    digits = []
    r = result
    while r > 0 or not digits:
        digits.append(r % base)
        r //= base
    digits.reverse()

    right_row = digits

    info = {
        "action": "lattice_multiply",
        "a": a,
        "b": b,
        "result": result,
        "a_lo": a_lo, "a_hi": a_hi,
        "b_lo": b_lo, "b_hi": b_hi,
        "products": {
            "ml*ml": p11,
            "ml*st": p12,
            "st*ml": p21,
            "st*st": p22,
        },
    }

    return left_row, right_row, result, info


def lattice_to_bottom_row(a: int, b: int, base: int = 10):
    """
    Упрощённый хук — результат в нижнюю строку юпаны.
    Аналог oscillator_to_yupana_bottom_row.
    """
    result = lattice_multiply(a, b, base)

    digits = []
    r = result
    while r > 0 or not digits:
        digits.append(r % base)
        r //= base

    while len(digits) < 5:
        digits.append(0)

    return digits[:5]
