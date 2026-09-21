# analemma_calc.py
# ==============================================================================
# НАЗНАЧЕНИЕ:
#   Расчёт координат аналеммы (азимут, высота) для небесных тел.
#   Модуль предназначен для импорта в main.py — не запускается отдельно.
#
# КЛЮЧЕВАЯ ОСОБЕННОСТЬ:
#   Функция analemma_xy_cable учитывает фазу измерения (минуты/секунды),
#   что позволяет демонстрировать завал фронта волны на аналемме
#   при анимации с течением времени и сезона.
#
# ЗАВИСИМОСТИ:
#   pip install ephem
# ==============================================================================

import math
import ephem
import datetime

# ------------------------------------------------------------------------------
# ГЛОБАЛЬНЫЕ НАСТРОЙКИ НАБЛЮДАТЕЛЯ И НЕБЕСНОГО ТЕЛА
# ------------------------------------------------------------------------------
# Тело по умолчанию — Солнце
astro_str = "Sun"
astro_body = ephem.Sun()

# Наблюдатель по умолчанию — Москва
observer = ephem.Observer()
observer.name = "Moscow"
observer.lon = '37.6173'
observer.lat = '55.7558'

# Текущий год (используется при расчёте аналеммы по умолчанию)
my_year = str(datetime.datetime.now().year)

# Массивы выбора часов и дней (1 — включено, 0 — выключено)
# По умолчанию: полдень (12:00) и дни 1, 11, 21 каждого месяца
includeH = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
show_allH = 0  # флаг «показать все часы»
includeD = [0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0]
show_allD = 0  # флаг «показать все дни»

deg_per_rad = 57.2957795  # коэффициент перевода радиан в градусы

# ------------------------------------------------------------------------------
# СЛОВАРЬ ДОСТУПНЫХ НЕБЕСНЫХ ТЕЛ
# ------------------------------------------------------------------------------
BODY_MAP = {
    "Sun":     ephem.Sun,
    "Moon":    ephem.Moon,
    "Mercury": ephem.Mercury,
    "Venus":   ephem.Venus,
    "Mars":    ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn":  ephem.Saturn,
    "Neptune": ephem.Neptune,
}

# ------------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПРОВЕРКИ ВВОДА
# ------------------------------------------------------------------------------
def is_int(s):
    """Проверяет, является ли строка целым числом."""
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    """Проверяет, является ли строка числом с плавающей точкой."""
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_valid_date(y, m, d):
    """Проверяет корректность даты (год, месяц, день)."""
    try:
        datetime.datetime(y, m, d)
        return True
    except ValueError:
        return False

# ------------------------------------------------------------------------------
# НАСТРОЙКА НАБЛЮДАТЕЛЯ И ТЕЛА
# ------------------------------------------------------------------------------
def set_observer(lat_deg, lon_deg, name="Custom"):
    """
    Устанавливает координаты наблюдателя.
    lat_deg, lon_deg — в градусах (десятичные).
    """
    global observer
    observer.name = name
    observer.lat = str(lat_deg / deg_per_rad)
    observer.lon = str(lon_deg / deg_per_rad)

def set_body(body_name):
    """
    Устанавливает небесное тело по имени.
    Доступные имена см. в BODY_MAP.
    """
    global astro_body, astro_str
    if body_name in BODY_MAP and astro_str != body_name:
        astro_str = body_name
        astro_body = BODY_MAP[body_name]()

# ------------------------------------------------------------------------------
# РАСЧЁТ КООРДИНАТ АНАЛЕММЫ
# ------------------------------------------------------------------------------
def analemma_xy(date):
    """
    Стандартный расчёт азимута и высоты небесного тела в градусах.

    Параметры:
        date — строка или объект ephem.date (например, '2025/06/15 12:00')

    Возвращает:
        (azimuth, altitude) — кортеж углов в градусах
    """
    # Корректировка времени на долготу наблюдателя (перевод в местное солнечное время)
    adjtime = ephem.date(ephem.date(date) - float(observer.lon) * (12.0 / math.pi) * ephem.hour)
    observer.date = adjtime
    astro_body.compute(observer)
    x = deg_per_rad * float(astro_body.az)
    y = deg_per_rad * float(astro_body.alt)
    return (x, y)

def analemma_xy_cable(date):
    """
    Расчёт координат с эвристическими фазовыми поправками.

    Ключевая функция для анимации: учитывает фазу (минуты/секунды),
    добавляет стоячие волны, имитирующие:
      — годовое сжатие (wave_core) — пико-мезонный резонанс
      — коронарный джет (wave_jet) — высокочастотная модуляция

    Это позволяет демонстрировать «завал фронта» на аналемме
    при изменении времени суток и сезона.

    Параметры:
        date — строка или объект ephem.date

    Возвращает:
        (mod_azimuth, mod_altitude) — модифицированные координаты в градусах
    """
    # 1. Базовый астрономический расчёт (азимут + высота)
    adjtime = ephem.date(ephem.date(date) - float(observer.lon) * (12.0 / math.pi) * ephem.hour)
    observer.date = adjtime
    astro_body.compute(observer)

    base_x = deg_per_rad * float(astro_body.az)
    base_y = deg_per_rad * float(astro_body.alt)

    # 2. Перевод даты в условную фазу для вычисления пульсаций
    t = float(ephem.date(date))

    # Стоячая волна: годовое сжатие конденсатора (период — 365.25 дня)
    wave_core = math.sin(t * 2 * math.pi / 365.25) * 5.0

    # Высокочастотная модуляция: коронарный джет (12 гармоник)
    wave_jet = math.sin(t * 2 * math.pi * 12.0) * math.cos(t * 2 * math.pi) * 2.0

    # 3. Модификация координат (эффект шахматного разворота)
    mod_x = base_x + wave_core
    mod_y = base_y + wave_jet

    return (mod_x, mod_y)

# ------------------------------------------------------------------------------
# СБОР ДАННЫХ АНАЛЕММЫ ДЛЯ MATPLOTLIB
# ------------------------------------------------------------------------------
def compute_analemma(year=None, hours=None, days=None,
                     use_cable=False, above_horizon_only=True):
    """
    Вычисляет массив точек аналеммы для построения графика в matplotlib.

    Параметры:
        year  — строка года (по умолчанию my_year)
        hours — список часов [0..23] или None (использует includeH / show_allH)
        days  — список дней [1..31] или None (использует includeD / show_allD)
        use_cable — True: использовать analemma_xy_cable (с фазовыми поправками)
                    False: использовать обычный analemma_xy
        above_horizon_only — True: вернуть только точки над горизонтом (alt > 0)

    Возвращает:
        Список кортежей: [(hour, [(x, y), ...]), ...]
        где hour — номер часа, x — азимут в градусах, y — высота в градусах.
    """
    global my_year
    if year is not None:
        my_year = str(year)

    # Определение активных часов
    if hours is not None:
        active_hours = hours
    elif show_allH:
        active_hours = list(range(24))
    else:
        active_hours = [h for h in range(len(includeH)) if includeH[h] == 1]

    # Определение активных дней
    if days is not None:
        active_days = days
    elif show_allD:
        active_days = list(range(1, 32))
    else:
        active_days = [d for d in range(1, len(includeD)) if includeD[d] == 1]

    # Выбор функции расчёта
    calc_func = analemma_xy_cable if use_cable else analemma_xy

    # Сбор данных
    result = []
    for h in active_hours:
        points = []
        for m in range(1, 13):
            for d in active_days:
                if is_valid_date(int(my_year), m, d):
                    date_str = '{0:s}/{1:d}/{2:d} {3:d}:00'.format(my_year, m, d, h)
                    x, y = calc_func(date_str)
                    if above_horizon_only and y <= 0:
                        continue
                    points.append((x, y))
        if points:
            result.append((h, points))

    return result

def compute_analemma_for_time(dt, use_cable=False):
    """
    Вычисляет одну точку аналеммы для заданного момента времени.

    Параметры:
        dt — объект datetime.datetime (точное время с минутами/секундами)
        use_cable — True: использовать фазовые поправки

    Возвращает:
        (azimuth, altitude) — координаты в градусах
    """
    # Преобразование datetime в строку формата ephem
    date_str = dt.strftime('%Y/%m/%d %H:%M:%S')
    if use_cable:
        return analemma_xy_cable(date_str)
    else:
        return analemma_xy(date_str)
