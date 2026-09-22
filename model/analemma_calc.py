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
#from datetime import datetime, timedelta

from analemma_array import (
    PLANET_EPHEM_MAP,
    analemma_state
)

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
show_allH = 1  # флаг «показать все часы»
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
#    observer.lat = str(lat_deg / deg_per_rad)
#    observer.lon = str(lon_deg / deg_per_rad)
    observer.lat = str(lat_deg)
    observer.lon = str(lon_deg)

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
    print(astro_body.alt, astro_body.az)
    x = deg_per_rad * float(astro_body.az)
    y = deg_per_rad * float(astro_body.alt)
    return (x, y)

# ------------------------------------------------------------------------------
# РАСЧЁТ Одной точки
# ------------------------------------------------------------------------------


def compute_analemma_for_time(dt, use_cable=False):
    """
    Вычисляет одну точку аналеммы для заданного момента времени.

    Параметры:
        dt — объект datetime.datetime (точное время с минутами/секундами)
        use_cable — True: использовать фазовые поправки

    Возвращает:
        (azimuth, altitude) — координаты в градусах
    """
    date_str = dt.strftime('%Y/%m/%d %H:%M:%S')
    return analemma_xy(date_str)



# ------------------------------------------------------------------------------
# Отрисовка графика
# ------------------------------------------------------------------------------

def drawAnalemma(planet_name, ax, year=None):
    # --- Глобальные переменные из analemma_calc.py, необходимые для работы: ---
    #   my_year       — строка текущего года
    #   includeH      — массив из 25 элементов (0/1)
    #   show_allH     — флаг (1 = все часы)
    #   includeD      — массив из 32 элементов (0/1)
    #   show_allD     — флаг (1 = все дни)
    #   deg_per_rad   — коэффициент радианы → градусы
    #   observer      — объект ephem.Observer
    #   astro_str     — строка с названием тела
    #   analemma_xy   — функция расчёта
    #   is_valid_date — функция проверки даты
    #   set_body      — функция выбора тела
    #
    # --- Из analemma_array.py: ---
    #   PLANET_EPHEM_MAP — словарь русских → английских имён
    #   analemma_state   — хранилище состояний окон
    # ------------------------------------------------------------------------

    global my_year

    if year is not None:
        my_year = str(year)

    eng_name = PLANET_EPHEM_MAP.get(planet_name)
    if eng_name is None:
        return
    set_body(eng_name)

    if planet_name not in analemma_state:
        analemma_state[planet_name] = {
            'win':            ax.figure.canvas.get_tk_widget().winfo_toplevel(),
            'fig':            ax.figure,
            'ax':             ax,
            'canvas':         ax.figure.canvas,
            'hourly_data':    [None] * 25,
            'cached_year':    -1,
            'last_update_ms': 0,
        }

    state = analemma_state[planet_name]

    # Сбор данных — как в оригинале: data[h] = [(x, y), ...]
    data = []
    for i in range(25):
        data.append([])

    for m in range(1, 13):
        for d in range(1, len(includeD)):
            if includeD[d] == 1 or show_allD == 1:
                if is_valid_date(int(my_year), m, d):
                    for h in range(len(includeH)):
                        if includeH[h] == 1 or show_allH == 1:
                            date = '{0:s}/{1:d}/{2:d} {3:d}:00'.format(my_year, m, d, h)
                            data[h].append(analemma_xy(date))

    # Сохраняем готовые кривые как списки кортежей [(x, y), ...] или None
    for h in range(25):
        if len(data[h]) > 0:
            state['hourly_data'][h] = data[h]
        else:
            state['hourly_data'][h] = None

    state['cached_year'] = int(my_year)

    # Маркер — вычисляем один раз при открытии, дальше не трогаем
    now = datetime.datetime.now()
    state['marker_dt'] = now
    state['marker_pos'] = analemma_xy(now.strftime('%Y/%m/%d %H:%M:%S'))


    # Очистка графика
    ax.clear()
    ax.set_facecolor('#f8f9fa')

    # Рисуем точки — как в оригинале: yellow если выше горизонта, blue если ниже
    for h in range(len(includeH)):
        if includeH[h] == 1 or show_allH == 1:
            if state['hourly_data'][h] is None:
                continue
            for j in range(len(state['hourly_data'][h])):
                x, y = state['hourly_data'][h][j]
                if y > 0:
                    ax.plot(x, y, 'o', markersize=1.5, color='gold', alpha=0.8)
                else:
                    ax.plot(x, y, 'o', markersize=1.5, color='blue', alpha=0.8)

    # Сетка — как в оригинале
    ax.axvline(90,  color='black', linewidth=1)
    ax.axvline(180, color='black', linewidth=1)
    ax.axvline(270, color='black', linewidth=1)
    ax.axhline(45,  color='black', linewidth=1)
    ax.axhline(0,   color='black', linewidth=2)
    ax.axhline(-45, color='black', linewidth=1)

    # Диапазоны
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_yticks([-90, -45, 0, 45, 90])

    # Подписи — как в оригинале
    mylon = deg_per_rad * float(observer.lon)
    mylat = deg_per_rad * float(observer.lat)
    my_ns = "N" if mylat > 0 else "S"
    my_we = "W" if mylon < 0 else "E"
    mytitle = "{0:s} Analemma Plot for  {1:.3f}{2:s}  {3:.3f}{4:s}".format(
        my_year, abs(mylat), my_ns, abs(mylon), my_we
    )
    xDesc = "Direction [N=0, E=90, S=180, W=270] [Yellow = {0:s} above horizon, Blue = {0:s} below horizon]".format(astro_str)

    ax.set_title(mytitle, fontsize=10)
    ax.set_xlabel(xDesc)
    ax.set_ylabel("Elevation")
    ax.grid(True, alpha=0.3)
    ax.set_aspect('auto')
