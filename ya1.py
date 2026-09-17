"""
Сравнение моделей прецессии с NASA DE422.
Ревизия 5: все замечания из обеих рецензий учтены.

Модели:
  DE422_minus_VSOP:  dϖ/dt(DE422) − dϖ/dt(VSOP87E)            — диагностическая разность
  P0:                K / a₀^(5/2)                              — без e-поправки
  P_GR:              K / (a₀^(5/2) * (1-e₀²))                  — стандартная GR
  P_391838:          (K + L*(A391838(e₀)-1)) / a₀^(5/2)        — A391838, постоянные a₀, e₀
  P_A391838_hybrid:  (K + L*(A391838(e(t))-1)) / a(t)^(5/2)    — ГИБРИД: кинематика DE422 + модельная прецессия A391838

Ключевые исправления (rev5):
  1. real_helio_long — прямой вектор body−Sun, без observe()
  2. Earth — planets[3] (EMB) для согласованности с VSOP87E (VSOP87.emb)
  3. P_A391838_hybrid — M(t) из эфемериды; a(t) оскулирующая; dω интегрируется трапециями
  4. Прямое сравнение dϖ/dt: наблюдение vs модели
  5. varpi(t) — проекционная долгота вектора эксцентриситета (не 3D Ω+ω)
  6. GR_obs переименован в DE422_minus_VSOP (диагностическая разность, не GR-наблюдение)
  7. Угловая разность с wrap-around для dvarpi_de422
  8. Окна регрессии: полный интервал, центральный, скользящее окно
  9. compute_gr_component() удалён
 10. P_391838_et переименован в P_A391838_hybrid с комментарием о гибридности
 11. Newtonian Марса помечен как ориентировочный
 12. Оскулирующие элементы помечены как Sun-only двухтельные

Требования: pip install skyfield numpy matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import urllib.request
import os
from skyfield.api import load

# ============================================================
# ОПУБЛИКОВАННЫЕ НЬЮТОНОВСКИЕ ПЛАНЕТНЫЕ ВОЗМУЩЕНИЯ
# arcsec / Julian century
# ============================================================
NEWTONIAN_PLANETARY = {
    'Mercury': 532.3035,   # arcsec/century, хорошо подтверждено
    'Mars':    1598.2,     # ОРИЕНТИРОВОЧНО, требует верификации источника
}

SOLAR_J2_CONTRIBUTION = {
    'Mercury': 0.0286,
    'Mars':    0.00013,
}

# ============================================================
# ЗАГРУЗКА ЭФЕМЕРИДЫ
# ============================================================
print("Загрузка эфемериды DE422...")
planets = load('de422.bsp')
ts = load.timescale()

SUN = planets[10]

# Небесные тела
# ВАЖНО: Earth = planets[3] (EMB) для согласованности с VSOP87E (VSOP87.emb)
# Ранее использовался planets[399] (геоцентр Земли), но VSOP87E не имеет
# отдельного файла для геоцентрической Земли, только для EMB.
BODIES = {
    'Mercury': planets[1],
    'Venus':   planets[2],
    'Earth':   planets[3],    # EMB — согласовано с VSOP87.emb
    'Mars':    planets[4],
    'Jupiter': planets[5],
    'Saturn':  planets[6],
    'Uranus':  planets[7],
    'Neptune': planets[8],
    'Pluto':   planets[9],
}

# Параметры J2000 — для моделей P0, P_GR, P_391838 (постоянные)
PLANETS = {
    'Mercury': {'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456,  'period': 87.969},
    'Venus':   {'a': 0.723332, 'e': 0.006772, 'varpi0': 131.533, 'period': 224.701},
    'Earth':   {'a': 1.000000, 'e': 0.016709, 'varpi0': 102.937, 'period': 365.256},
    'Mars':    {'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040, 'period': 686.98},
}

GM_SUN_AU3_DAY2 = 1.32712440018e20 / (1.495978707e11)**3 * (86400)**2

# ============================================================
# УРАВНЕНИЕ ЦЕНТРА (до e^5)
# ============================================================
def true_anomaly(M, e):
    return (
        M
        + (2*e - e**3/4 + 5*e**5/96) * np.sin(M)
        + (5*e**2/4 - 11*e**4/24) * np.sin(2*M)
        + (13*e**3/12 - 43*e**5/64) * np.sin(3*M)
        + (103*e**4/96) * np.sin(4*M)
        + (1097*e**5/960) * np.sin(5*M)
    ) % (2*np.pi)

def true_to_mean_anomaly(nu, e):
    E = 2 * np.arctan2(
        np.sqrt(1 - e) * np.sin(nu / 2),
        np.sqrt(1 + e) * np.cos(nu / 2)
    )
    E = E % (2 * np.pi)
    M = (E - e * np.sin(E)) % (2 * np.pi)
    return M

# ============================================================
# A391838
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]
A391838_LABELS = ['1', '1', '1', '3/2', '3', '19/3', '55/4', '31', '72']

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

K = 3.8313   # arcsec/century
L = 0.6496

# ============================================================
# СКОРОСТЬ ПРЕЦЕССИИ (arcsec/century)
# ============================================================
def precession_arcsec_per_century(model, a, e):
    if model == 'P0':
        return K / a**2.5
    elif model == 'P_GR':
        return K / (a**2.5 * (1 - e**2))
    elif model in ('P_391838', 'P_A391838_hybrid'):
        return (K + L * (A391838_truncated(e) - 1)) / a**2.5
    else:
        raise ValueError(f"Unknown model: {model}")

def precession_deg_per_day(model, a, e):
    return precession_arcsec_per_century(model, a, e) / 3600.0 / 36525.0

# ============================================================
# ПРЕОБРАЗОВАНИЕ В ЭКЛИПТИЧЕСКУЮ СИСТЕМУ
# ============================================================
OBLIQUITY = np.radians(23.4393)
_COS_EPS = np.cos(OBLIQUITY)
_SIN_EPS = np.sin(OBLIQUITY)

def to_ecliptic(vec):
    """Экваториальная (ICRF) → эклиптическая (J2000)."""
    x, y, z = vec[0], vec[1], vec[2]
    return np.array([
        x,
        y * _COS_EPS + z * _SIN_EPS,
        -y * _SIN_EPS + z * _COS_EPS
    ])

# ============================================================
# УГЛОВАЯ РАЗНОСТЬ (с корректной обработкой перехода 0/360)
# ============================================================
def angular_difference_deg(angle2, angle1):
    """Возвращает кратчайшую угловую разность angle2 - angle1 в градусах."""
    return (angle2 - angle1 + 180.0) % 360.0 - 180.0

# ============================================================
# ГЕЛИОЦЕНТРИЧЕСКАЯ ПОЗИЦИЯ — ПРЯМОЙ ВЕКТОР (без observe)
# ============================================================
def helio_position(name, dt):
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    sun_at = SUN.at(t)
    body_at = body.at(t)

    r_vec = np.array(body_at.position.au, dtype=float) - np.array(sun_at.position.au, dtype=float)
    v_vec = np.array(body_at.velocity.au_per_d, dtype=float) - np.array(sun_at.velocity.au_per_d, dtype=float)

    r_vec = to_ecliptic(r_vec)
    v_vec = to_ecliptic(v_vec)

    return r_vec, v_vec

def real_helio_long(name, dt):
    r_vec, _ = helio_position(name, dt)
    lon_rad = np.arctan2(r_vec[1], r_vec[0])
    lon_deg = np.degrees(lon_rad) % 360.0
    r_au = np.sqrt(np.sum(r_vec**2))
    return lon_deg, r_au

# ============================================================
# VSOP87E: ЗАГРУЗКА И ПАРСИНГ
# ============================================================
VSOP87E_URLS = {
    'Mercury': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.mer',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.mer'
    ],
    'Venus': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.ven',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.ven'
    ],
    'Earth': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.emb',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.emb'
    ],
    'Mars': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.mar',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87.mar'
    ]
}

def download_vsop87e(name):
    filename = f'VSOP87E_{name}.txt'
    if os.path.exists(filename) and os.path.getsize(filename) > 10000:
        print(f"  {filename} уже загружен")
        return filename
    
    urls = VSOP87E_URLS.get(name, [])
    for url in urls:
        print(f"  Попытка загрузки: {url}")
        try:
            urllib.request.urlretrieve(url, filename)
            with open(filename, 'r', encoding='latin1') as f:
                first_line = f.readline()
            if 'VSOP87' in first_line:
                print(f"  Успешно: {filename}")
                return filename
            else:
                if os.path.exists(filename):
                    os.remove(filename)
        except Exception as e:
            print(f"  Ошибка загрузки {url}: {e}")
            if os.path.exists(filename):
                os.remove(filename)
    
    return None

# ============================================================
# ОСКУЛИРУЮЩИЕ ЭЛЕМЕНТЫ (полный набор)
# ============================================================
def osculating_full(name, dt):
    """
    Мгновенные Sun-only оскулирующие элементы двухтельной задачи
    для гелиоцентрического состояния DE422.
    
    Это НЕ канонические элементы VSOP87 и НЕ чисто секулярные
    орбитальные элементы. Включают короткопериодические возмущения
    от других планет, заложенные в DE422.
    
    Возвращает (a_osc, e_osc, varpi_proj_deg, M_rad).
    
    varpi_proj_deg — проекционная долгота вектора эксцентриситета
    на плоскость J2000 ecliptic. Это не полная 3D-долгота перицентра Ω+ω.
    Для Меркурия (i≈7°) и Марса (i≈1.85°) наклонение может давать
    поправки на уровне arcsec/century.
    """
    r_vec, v_vec = helio_position(name, dt)

    r = np.sqrt(np.sum(r_vec**2))
    v = np.sqrt(np.sum(v_vec**2))
    mu = GM_SUN_AU3_DAY2

    energy = 0.5 * v**2 - mu / r
    h_vec = np.cross(r_vec, v_vec)
    h_mag = np.sqrt(np.sum(h_vec**2))

    if energy >= 0:
        a_osc = PLANETS[name]['a']
    else:
        a_osc = -mu / (2 * energy)

    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r
    e_osc = np.sqrt(np.sum(e_vec**2))
    e_osc = min(max(e_osc, 0.0), 0.99)

    # Проекционная долгота вектора эксцентриситета на плоскость J2000 ecliptic.
    # Не полная 3D-долгота перицентра Ω+ω.
    varpi_deg = np.degrees(np.arctan2(e_vec[1], e_vec[0])) % 360.0

    # Истинная аномалия
    nu = np.arccos(np.clip(np.dot(e_vec, r_vec) / (e_osc * r), -1, 1))
    if np.dot(np.cross(e_vec, r_vec), h_vec) < 0:
        nu = 2 * np.pi - nu

    M = true_to_mean_anomaly(nu, e_osc)

    return a_osc, e_osc, varpi_deg, M

# ============================================================
# КУМУЛЯТИВНОЕ ИНТЕГРИРОВАНИЕ (метод трапеций, без SciPy)
# ============================================================
def cumulative_trapezoid_manual(y, x, initial=0.0):
    """
    Кумулятивный интеграл y(x) методом трапеций.
    Возвращает массив той же длины, что и x.
    """
    result = np.empty(len(x))
    result[0] = initial
    for i in range(1, len(x)):
        dx = x[i] - x[i-1]
        result[i] = result[i-1] + 0.5 * (y[i-1] + y[i]) * dx
    return result

# ============================================================
# МОДЕЛЬНАЯ ДОЛГОТА — ПОСТОЯННЫЕ МОДЕЛИ (одиночный вызов)
# ============================================================
def compute_model_long(name, model, start_date, day):
    """
    Вычисляет модельную долготу для постоянных моделей.
    
    Для P_A391838_hybrid и DE422_minus_VSOP используйте
    compute_model_long_array() — там корректно интегрируется переменная скорость.
    """
    p = PLANETS[name]

    if model in ('P_A391838_hybrid', 'DE422_minus_VSOP'):
        raise ValueError(
            f"Модель {model} требует интегрирования. "
            "Используйте compute_model_long_array()."
        )

    # --- Простые модели: постоянные a₀, e₀ ---
    period = p['period']
    e0 = p['e']
    varpi0 = np.radians(p['varpi0'])
    n = 2 * np.pi / period

    domega = precession_deg_per_day(model, p['a'], e0)

    lon_0, _ = real_helio_long(name, start_date)
    nu_0 = (np.radians(lon_0) - varpi0 + np.pi) % (2 * np.pi) - np.pi
    M_0 = true_to_mean_anomaly(nu_0, e0)

    M = M_0 + n * day
    varpi = varpi0 + np.radians(domega) * day
    lon = np.degrees(varpi + true_anomaly(M, e0)) % 360.0
    return lon

# ============================================================
# МОДЕЛЬНАЯ ДОЛГОТА — МАССИВ (с интегрированием для переменных моделей)
# ============================================================
def compute_model_long_array(name, model, start_date, days):
    """
    Вычисляет модельную долготу для массива дней.
    
    Для P_A391838_hybrid: скорость прецессии зависит от a(t), e(t),
    поэтому dω интегрируется кумулятивно трапециями:
        ϖ(t) = ϖ(0) + ∫₀ᵗ dω(τ) dτ
    
    Для DE422_minus_VSOP: GR-поправка = dϖ/dt(DE422) − dϖ/dt(VSOP87E),
    также интегрируется кумулятивно.
    
    ГИБРИДНАЯ МОДЕЛЬ P_A391838_hybrid:
    kinematics (a, e, M) берётся из DE422, заменяется только закон
    изменения перицентра на A391838. Это не самостоятельная
    динамическая модель движения.
    
    days — массив, включающий день 0 (для начального varpi_0).
    """
    if len(days) == 0:
        return np.array([])

    # Начальные элементы
    a0, e0, varpi_0, M_0 = osculating_full(name, start_date)
    varpi_0_rad = np.radians(varpi_0)

    if model == 'P_A391838_hybrid':
        # --- Гибрид: кинематика DE422 + модельная прецессия A391838 ---
        domega_arr = np.empty(len(days))
        M_arr = np.empty(len(days))
        e_arr = np.empty(len(days))

        for i, day in enumerate(days):
            dt = start_date + timedelta(days=int(day))
            a_t, e_t, varpi_real, M_t = osculating_full(name, dt)
            domega_arr[i] = precession_deg_per_day(model, a_t, e_t)
            M_arr[i] = M_t
            e_arr[i] = e_t

        # Интегрируем dω трапециями
        varpi_model_rad = varpi_0_rad + np.radians(
            cumulative_trapezoid_manual(domega_arr, days, initial=0.0)
        )

        lon = np.degrees(varpi_model_rad + true_anomaly(M_arr, e_arr)) % 360.0
        return lon

    elif model == 'DE422_minus_VSOP':
        # --- Диагностическая разность DE422 − VSOP87E ---
        # НЕ является чистым GR-наблюдением. Содержит:
        #   - различия координатных систем
        #   - различия исходных параметров
        #   - различия численного интегрирования
        #   - различия моделей масс и возмущений
        #   - релятивистские эффекты
        #   - численные и интерполяционные ошибки

        dvarpi_de422_arr = np.empty(len(days))
        M_arr = np.empty(len(days))
        e_arr = np.empty(len(days))

        for i, day in enumerate(days):
            dt = start_date + timedelta(days=int(day))
            a_t, e_t, varpi_real, M_t = osculating_full(name, dt)
            M_arr[i] = M_t
            e_arr[i] = e_t

            # VSOP87E производная перигелия
            t_mill = datetime_to_vsop87_t(dt)
            _, _, dvarpi_vsop = vsop87e_compute(vsop_data[name], t_mill)

            # DE422 производная: центральная разность с угловой коррекцией
            if i == 0:
                # Односторонняя вперёд
                dt_next = start_date + timedelta(days=int(days[1]))
                _, _, varpi_next, _ = osculating_full(name, dt_next)
                dvarpi_de422 = angular_difference_deg(varpi_next, varpi_real) / (days[1] - days[0])
            elif i == len(days) - 1:
                # Односторонняя назад
                dt_prev = start_date + timedelta(days=int(days[-2]))
                _, _, varpi_prev, _ = osculating_full(name, dt_prev)
                dvarpi_de422 = angular_difference_deg(varpi_real, varpi_prev) / (days[-1] - days[-2])
            else:
                # Центральная разность
                dt_prev = start_date + timedelta(days=int(days[i-1]))
                dt_next = start_date + timedelta(days=int(days[i+1]))
                _, _, varpi_prev, _ = osculating_full(name, dt_prev)
                _, _, varpi_next, _ = osculating_full(name, dt_next)
                dvarpi_de422 = angular_difference_deg(varpi_next, varpi_prev) / (days[i+1] - days[i-1])

            # GR-поправка = DE422 − VSOP87 (в град/день)
            dvarpi_vsop_deg_day = dvarpi_vsop / 3600.0 / 100.0 / 365.25
            gr_rate = dvarpi_de422 - dvarpi_vsop_deg_day
            dvarpi_de422_arr[i] = gr_rate

        # Интегрируем кумулятивно
        varpi_model_rad = varpi_0_rad + np.radians(
            cumulative_trapezoid_manual(dvarpi_de422_arr, days, initial=0.0)
        )

        lon = np.degrees(varpi_model_rad + true_anomaly(M_arr, e_arr)) % 360.0
        return lon

    else:
        # --- Постоянные модели: можно вызывать поштучно ---
        results = np.empty(len(days))
        for i, day in enumerate(days):
            results[i] = compute_model_long(name, model, start_date, int(day))
        return results

# ============================================================
# СТРУКТУРА
# ============================================================
def print_structure():
    print(f"\n{'='*80}")
    print("Структура деления Сварожьего Круга")
    print(f"{'='*80}")
    print(f"\n  Делители (АХиневич):     16, 9, 9, 72, 760")
    print(f"  Делители (реконструкция): 1, 2, 9, 72, 760")
    print(f"  A391838 (e.g.f.):         1, 1, 2, 9, 72, 760, ...")
    print(f"\n  Совпадение: 2, 9, 72, 760 — четыре делителя подряд")
    total_akh = 16 * 9 * 9 * 72 * 760
    total_recon = 1 * 2 * 9 * 72 * 760
    print(f"\n  Полное деление (АХиневич):      {total_akh}")
    print(f"  Полное деление (реконструкция): {total_recon}")
    print(f"  Точность места (АХиневич):      {360*3600/total_akh:.6f} arcsec")
    print(f"  Точность места (реконструкция): {360*3600/total_recon:.6f} arcsec")
    print(f"\n  Наблюдаемое числовое совпадение — не установленная физическая связь.")

def print_contribution_table():
    print(f"\n{'='*80}")
    print("Вклады коэффициентов A391838 по планетам")
    print(f"{'='*80}")
    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        e = PLANETS[name]['e']
        print(f"\n  {name}  (e={e:.6f}):")
        cumulative = 0.0
        for k in range(len(A391838_norm)):
            c = A391838_norm[k]
            contrib = c * e**k
            cumulative += contrib
            print(f"    k={k}  коэфф={A391838_LABELS[k]:>8}  "
                  f"e^k={e**k:.6e}  вклад={contrib:.6e}  "
                  f"накопл.={cumulative:.6e}")
        a_gr = 1.0 / (1 - e**2)
        print(f"    A(e)-1 = {cumulative-1:.6f}   "
              f"1/(1-e^2)-1 = {a_gr-1:.6f}")

# ============================================================
# ОКНА РЕГРЕССИИ (пункт 8 второй рецензии)
# ============================================================
def regression_windows(years_arr, varpi_unwrapped, name):
    """
    Вычисляет секулярную скорость прецессии несколькими методами:
    1. Полный интервал (как раньше)
    2. Центральный интервал (отбрасываем по 10% с краёв)
    3. Скользящее окно 500 лет
    4. Среднее по сглаженной кривой
    
    Возвращает словарь с результатами.
    """
    results = {}
    
    # 1. Полный интервал
    coef_full = np.polyfit(years_arr, varpi_unwrapped, 1)
    results['full'] = coef_full[0] * 3600 * 100  # arcsec/century
    
    # 2. Центральный интервал (отбрасываем по 10% с краёв)
    n = len(years_arr)
    lo = int(n * 0.1)
    hi = int(n * 0.9)
    coef_central = np.polyfit(years_arr[lo:hi], varpi_unwrapped[lo:hi], 1)
    results['central'] = coef_central[0] * 3600 * 100
    
    # 3. Скользящее окно 500 лет
    window = 500  # лет
    window_indices = []
    window_rates = []
    i = 0
    while i < n:
        j = i
        while j < n and years_arr[j] - years_arr[i] < window:
            j += 1
        if j - i > 10:  # минимум точек
            coef_w = np.polyfit(years_arr[i:j], varpi_unwrapped[i:j], 1)
            window_indices.append(years_arr[i])
            window_rates.append(coef_w[0] * 3600 * 100)
        i = j
    results['window_years'] = np.array(window_indices)
    results['window_rates'] = np.array(window_rates)
    
    # 4. Среднее по сглаженной кривой (скользящее среднее, окно ~100 лет)
    smooth_window = max(int(n * 100 / (years_arr[-1] - years_arr[0])), 5)
    varpi_smoothed = np.convolve(varpi_unwrapped, np.ones(smooth_window)/smooth_window, mode='valid')
    years_smoothed = years_arr[smooth_window-1:]
    coef_smooth = np.polyfit(years_smoothed, varpi_smoothed, 1)
    results['smoothed'] = coef_smooth[0] * 3600 * 100
    
    return results

# ============================================================
# ПРЯМОЕ СРАВНЕНИЕ СКОРОСТЕЙ ПРЕЦЕССИИ
# ============================================================
def run_precession_comparison(years=1980, step_days=30):
    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    days = np.arange(0, total_days + 1, step_days)
    years_arr = days / 365.25

    MODELS = ['Newtonian_residual', 'P0', 'P_GR', 'P_391838', 'P_A391838_hybrid']

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Сбор dϖ/dt для {name}...")
        varpi_arr = []
        e_arr = []
        a_arr = []
        dvarpi_vsop_arr = []

        for d in days:
            dt = start_dt + timedelta(days=int(d))
            a_osc, e_osc, varpi, _ = osculating_full(name, dt)
            varpi_arr.append(varpi)
            e_arr.append(e_osc)
            a_arr.append(a_osc)

            t_mill = datetime_to_vsop87_t(dt)
            _, _, dvarpi_vsop = vsop87e_compute(vsop_data[name], t_mill)
            dvarpi_vsop_arr.append(dvarpi_vsop)

        varpi_arr = np.array(varpi_arr)
        e_arr = np.array(e_arr)
        a_arr = np.array(a_arr)
        dvarpi_vsop_arr = np.array(dvarpi_vsop_arr)

        # Unwrap varpi
        varpi_unwrapped = np.copy(varpi_arr)
        for i in range(1, len(varpi_unwrapped)):
            while varpi_unwrapped[i] - varpi_unwrapped[i-1] > 180:
                varpi_unwrapped[i] -= 360
            while varpi_unwrapped[i] - varpi_unwrapped[i-1] < -180:
                varpi_unwrapped[i] += 360

        # --- Секулярная скорость: несколько методов ---
        reg_results = regression_windows(years_arr, varpi_unwrapped, name)
        secular_prec = reg_results['full']
        secular_central = reg_results['central']
        secular_smoothed = reg_results['smoothed']

        # --- Мгновенная скорость ---
        step_years = step_days / 365.25
        dvarpi = np.gradient(varpi_unwrapped, step_years)
        prec_obs_instant = dvarpi * 3600 * 100  # arcsec/century

        # --- Newtonian residual ---
        newtonian_val = NEWTONIAN_PLANETARY[name]
        newtonian_residual_arr = prec_obs_instant - newtonian_val

        # --- VSOP difference (диагностика, НЕ GR) ---
        vsop_diff_arr = prec_obs_instant - dvarpi_vsop_arr

        # --- Модельные скорости ---
        prec_models = {}
        for model in MODELS:
            if model == 'Newtonian_residual':
                prec_models[model] = newtonian_residual_arr
                continue
            if model == 'P_A391838_hybrid':
                prec = np.array([
                    precession_arcsec_per_century(model, a_arr[i], e_arr[i])
                    for i in range(len(days))
                ])
            else:
                a0 = PLANETS[name]['a']
                e0 = PLANETS[name]['e']
                prec = np.full(len(days),
                    precession_arcsec_per_century(model, a0, e0))
            prec_models[model] = prec

        results[name] = {
            'days': days,
            'years': years_arr,
            'e': e_arr,
            'a': a_arr,
            'varpi': varpi_unwrapped,
            'prec_obs': prec_obs_instant,
            'secular_prec': secular_prec,
            'secular_central': secular_central,
            'secular_smoothed': secular_smoothed,
            'reg_windows': reg_results,
            'newtonian_planetary': np.full(len(days), newtonian_val),
            'residual_after_newtonian': newtonian_residual_arr,
            'prec_models': prec_models,
            'vsop_difference': vsop_diff_arr,
            'dvarpi_vsop': dvarpi_vsop_arr,
        }

    return results

# ============================================================
# ДЛИННЫЙ РАСЧЁТ (долготы)
# ============================================================
def run_long_comparison(years=1980, step_days=30):
    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    days = np.arange(0, total_days + 1, step_days)

    MODELS = ['DE422_minus_VSOP', 'P0', 'P_GR', 'P_391838', 'P_A391838_hybrid']
    MODEL_LABELS = {
        'DE422_minus_VSOP':    'DE422 \u2212 VSOP87E (диагн.)',
        'P0':                  'P\u2080 (без e-поправки)',
        'P_GR':                'P_GR (1/(1\u2212e\u00b2))',
        'P_391838':            'P_A391838 (e\u2080)',
        'P_A391838_hybrid':    'P_A391838 (гибрид DE422)',
    }

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Расчёт {name} на {years} лет (1010\u2013{1010+years})...")
        
        # Предвычисляем реальные долготы для всех дней (включая 0)
        real_lons = np.empty(len(days))
        for i, day in enumerate(days):
            dt = start_dt + timedelta(days=int(day))
            lon_real, _ = real_helio_long(name, dt)
            real_lons[i] = lon_real
        
        results[name] = {}
        for model in MODELS:
            model_lons = compute_model_long_array(name, model, start_dt, days)
            
            # Ошибки: начинаем с дня 1 (индекс 1)
            errors = []
            for i in range(1, len(days)):
                d = (model_lons[i] - real_lons[i] + 180) % 360 - 180
                if i > 1:
                    while d - errors[-1] > 180: d -= 360
                    while d - errors[-1] < -180: d += 360
                errors.append(d)
            results[name][model] = np.array(errors)

    return days[1:], results, MODEL_LABELS, MODELS

# ============================================================
# VSOP87E ПАРСИНГ
# ============================================================
def parse_vsop87e(filename):
    series = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    
    current_var = None
    current_power = 0
    
    with open(filename, 'r', encoding='latin1') as f:
        for line in f:
            if 'VARIABLE' in line and '*T**' in line:
                parts = line.split()
                try:
                    var_idx = parts.index('VARIABLE')
                    current_var = int(parts[var_idx + 1])
                    t_part = [p for p in parts if '*T**' in p][0]
                    current_power = int(t_part.split('*T**')[1])
                except (ValueError, IndexError):
                    continue
                continue
            
            parts = line.split()
            if len(parts) >= 5 and current_var in series:
                try:
                    A = float(parts[-3])
                    B = float(parts[-2])
                    C = float(parts[-1])
                    series[current_var].append((current_power, A, B, C))
                except ValueError:
                    continue

    if len(series[3]) < 5 or len(series[4]) < 5:
        raise ValueError(f"Не удалось извлечь достаточное количество членов рядов h и k из {filename}")
        
    return series

# ============================================================
# VSOP87E: ВЫЧИСЛЕНИЕ ϖ, e, dϖ/dt
# ============================================================
def vsop87e_compute(series, t_mill):
    k = 0.0
    for power, A, B, C in series[3]:
        k += A * t_mill**power * np.cos(B + C * t_mill)
        
    h = 0.0
    for power, A, B, C in series[4]:
        h += A * t_mill**power * np.cos(B + C * t_mill)
        
    e = np.sqrt(h**2 + k**2)
    varpi = np.arctan2(h, k)
    varpi_deg = np.degrees(varpi) % 360.0
    
    dk = 0.0
    for power, A, B, C in series[3]:
        if power > 0:
            dk += A * power * t_mill**(power - 1) * np.cos(B + C * t_mill)
        dk += A * t_mill**power * (-C) * np.sin(B + C * t_mill)
        
    dh = 0.0
    for power, A, B, C in series[4]:
        if power > 0:
            dh += A * power * t_mill**(power - 1) * np.cos(B + C * t_mill)
        dh += A * t_mill**power * (-C) * np.sin(B + C * t_mill)
        
    e2 = h**2 + k**2
    if e2 < 1e-30:
        dvarpi = 0.0
    else:
        dvarpi = (k * dh - h * dk) / e2
        
    dvarpi_arcsec_cent = dvarpi * (180.0 / np.pi) * 3600.0 / 10.0
    
    return varpi_deg, e, dvarpi_arcsec_cent

# ============================================================
# ВРЕМЯ: datetime ↔ VSOP87
# ============================================================
def datetime_to_vsop87_t(dt):
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    jd = t.tt
    return (jd - 2451545.0) / 365250.0

# ============================================================
# КООРДИНАТЫ СВАРОЖЬЕГО КРУГА
# ============================================================
def calculate_chertog(lon_deg):
    deg = (lon_deg - 130.0) % 360.0
    STEP_CHERTOG = 22.5
    STEP_ZAL = STEP_CHERTOG / 9
    STEP_STOL = STEP_ZAL / 9
    STEP_LAVKA = STEP_STOL / 72
    STEP_MESTO = STEP_LAVKA / 760
    chertog = int(deg // STEP_CHERTOG)
    rem = deg % STEP_CHERTOG
    zal = int(rem // STEP_ZAL)
    rem = rem % STEP_ZAL
    stol = int(rem // STEP_STOL)
    rem = rem % STEP_STOL
    lavka = int(rem // STEP_LAVKA)
    rem = rem % STEP_LAVKA
    mesto = int(rem // STEP_MESTO)
    return chertog, zal, stol, lavka, mesto

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':

    # Загрузка VSOP87E данных
    vsop_data = {}
    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        filename = download_vsop87e(name)
        if filename:
            vsop_data[name] = parse_vsop87e(filename)

    print_structure()
    print_contribution_table()

    # --- Короткий тест (81 день) ---
    print(f"\n{'='*80}")
    print("Короткий тест: 81 день от 2026-09-16")
    print(f"{'='*80}")

    start_dt = datetime(2026, 9, 16, 1, 0, 0)
    NUM_DAYS = 81
    MODELS = ['DE422_minus_VSOP', 'P0', 'P_GR', 'P_391838', 'P_A391838_hybrid']

    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        print(f"\n  {name}:")
        # Предвычисляем реальные долготы
        test_days = np.arange(0, NUM_DAYS + 1)
        real_lons = np.empty(len(test_days))
        for i, day in enumerate(test_days):
            dt = start_dt + timedelta(days=int(day))
            lon_real, _ = real_helio_long(name, dt)
            real_lons[i] = lon_real
        
        for model in MODELS:
            model_lons = compute_model_long_array(name, model, start_dt, test_days)
            rms_list = []
            for i in range(1, len(test_days)):
                d = (model_lons[i] - real_lons[i] + 180) % 360 - 180
                rms_list.append(d**2)
            rms = np.sqrt(np.mean(rms_list))
            print(f"    {model:22s}  RMS = {rms:.6f}\u00b0")

    # --- Чертоги ---
    print(f"\n{'='*80}")
    print("Координаты Сварожьего Круга (2026-09-16 07:21 UTC)")
    print(f"{'='*80}")

    test_dt = datetime(2026, 9, 16, 7, 21, 0)
    for name in ['Mercury', 'Venus', 'Earth', 'Mars',
                 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']:
        lon_deg, r_au = real_helio_long(name, test_dt)
        ch, za, st, la, me = calculate_chertog(lon_deg)
        print(f"  {name:10s}  \u03bb={lon_deg:8.4f}\u00b0  "
              f"\u0427\u0435\u0440\u0442\u043e\u0433 {ch:2d} \u2014 "
              f"\u0417\u0430\u043b {za} \u2014 \u0421\u0442\u043e\u043b {st} \u2014 "
              f"\u041b\u0430\u0432\u043a\u0430 {la:3d} \u2014 "
              f"\u041c\u0435\u0441\u0442\u043e {me:5d}  "
              f"r={r_au:.4f} \u0430.\u0435.")

    # --- Оскулирующие элементы ---
    print(f"\n{'='*80}")
    print("Оскулирующие элементы для Меркурия (проверка)")
    print("  (Sun-only оскулирующие элементы из DE422 state vector)")
    print(f"{'='*80}")
    for day in [0, 20, 40, 60, 80]:
        dt = datetime(2026, 9, 16) + timedelta(days=day)
        a_osc, e_osc, varpi, M = osculating_full('Mercury', dt)
        print(f"  День {day:3d}:  a={a_osc:.8f}  e={e_osc:.8f}  "
              f"\u03c0={varpi:.4f}\u00b0  M={np.degrees(M):.4f}\u00b0")

    # --- Прямое сравнение скоростей прецессии ---
    print(f"\n{'='*80}")
    print("Прямое сравнение d\u03c0/dt (1980 лет, шаг 30 дней)")
    print(f"{'='*80}")

    try:
        prec_results = run_precession_comparison(years=1980, step_days=30)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        prec_results = {}

    for name in ['Mercury', 'Mars']:
        if name not in prec_results:
            continue
        r = prec_results[name]
        secular = r['secular_prec']
        secular_central = r['secular_central']
        secular_smoothed = r['secular_smoothed']
        newtonian = NEWTONIAN_PLANETARY[name]
        residual_secular = secular - newtonian
        residual_central = secular_central - newtonian
        residual_smoothed = secular_smoothed - newtonian

        print(f"\n  {name}:")
        print(f"             {'Модель':>25s}  {'Среднее':>20s}  {'Секулярная':>20s}")
        print(f"  {'-'*70}")
        print(f"  {'DE422 мгновенная (d\u03c0/dt)':>25s}  {np.mean(r['prec_obs']):>20.4f}  {secular:>20.4f}")
        print(f"  {'Секулярная (центр. 10-90%)':>25s}  {'—':>20s}  {secular_central:>20.4f}")
        print(f"  {'Секулярная (сглаженная)':>25s}  {'—':>20s}  {secular_smoothed:>20.4f}")
        newt_label = 'Newtonian (опубл.)' if name == 'Mercury' else 'Newtonian (ориент.)'
        print(f"  {newt_label:>25s}  {newtonian:>20.4f}  {newtonian:>20.4f}")
        print(f"  {'Residual (DE422\u2212Newt.)':>25s}  {np.mean(r['residual_after_newtonian']):>20.4f}  {residual_secular:>20.4f}")
        print(f"  {'Residual (центр.)':>25s}  {'—':>20s}  {residual_central:>20.4f}")
        print(f"  {'Residual (сглаж.)':>25s}  {'—':>20s}  {residual_smoothed:>20.4f}")
        print(f"  {'DE422\u2212VSOP87E (диагн.)':>25s}  {np.mean(r['vsop_difference']):>20.4f}  {'—':>20s}")
        print()

        for model in ['P0', 'P_GR', 'P_391838', 'P_A391838_hybrid']:
            val = np.mean(r['prec_models'][model])
            print(f"  {model:>25s}  {val:>20.4f}")

        print()
        print(f"  Секулярный остаток vs GR:      {residual_secular:.4f} vs {np.mean(r['prec_models']['P_GR']):.4f}")
        print(f"  Центр. остаток vs GR:         {residual_central:.4f} vs {np.mean(r['prec_models']['P_GR']):.4f}")
        print(f"  Сглаж. остаток vs GR:         {residual_smoothed:.4f} vs {np.mean(r['prec_models']['P_GR']):.4f}")
        print(f"  Секулярный остаток vs A391838: {residual_secular:.4f} vs {np.mean(r['prec_models']['P_391838']):.4f}")

    # --- Длинный расчёт долготы ---
    print(f"\n{'='*80}")
    print("Длинный расчёт: 1980 лет, шаг 30 дней")
    print(f"{'='*80}")

    days_arr, long_results, model_labels, model_list = run_long_comparison(
        years=1980, step_days=30)

    # --- График 1: расхождение с эфемеридой ---
    fig1, axes1 = plt.subplots(1, 2, figsize=(18, 8))
    colors = {
        'DE422_minus_VSOP':    '#9b59b6',
        'P0':                  '#95a5a6',
        'P_GR':                '#3498db',
        'P_391838':            '#e74c3c',
        'P_A391838_hybrid':    '#2ecc71',
    }

    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes1[idx]
        for model in model_list:
            err = long_results[name][model]
            err_calibrated = err - err[0]
            years = days_arr / 365.25
            ax.plot(years, err_calibrated * 3600,
                    color=colors[model], lw=1.2,
                    label=model_labels[model], alpha=0.85)
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.set_title(f'{name}', fontweight='bold', fontsize=13)
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('\u0394\u03bb (arcsec)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    fig1.suptitle(
        '\u0420\u0430\u0441\u0445\u043e\u0436\u0434\u0435\u043d\u0438\u0435 '
        '\u043c\u043e\u0434\u0435\u043b\u0435\u0439 \u0441 NASA DE422 '
        '(1010\u20132990)',
        fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('long_comparison_2000yr.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 2: разница между моделями ---
    fig2, axes2 = plt.subplots(1, 2, figsize=(18, 8))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes2[idx]
        e = PLANETS[name]['e']

        d_gr_p0 = long_results[name]['P_GR'] - long_results[name]['P0']
        d_a39_p0 = long_results[name]['P_391838'] - long_results[name]['P0']
        d_a39_gr = long_results[name]['P_391838'] - long_results[name]['P_GR']
        d_hybrid_gr = long_results[name]['P_A391838_hybrid'] - long_results[name]['P_GR']

        years = days_arr / 365.25
        ax.plot(years, d_gr_p0 * 3600, 'b-', lw=1.5,
                label='P_GR \u2212 P\u2080', alpha=0.8)
        ax.plot(years, d_a39_p0 * 3600, 'r-', lw=1.5,
                label='P_A391838(e\u2080) \u2212 P\u2080', alpha=0.8)
        ax.plot(years, d_a39_gr * 3600, 'g--', lw=1.5,
                label='P_A391838(e\u2080) \u2212 P_GR', alpha=0.8)
        ax.plot(years, d_hybrid_gr * 3600, 'm:', lw=1.5,
                label='P_A391838(\u0433\u0438\u0431\u0440\u0438\u0434) \u2212 P_GR', alpha=0.8)
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.set_title(f'{name}  (e={e:.4f})', fontweight='bold')
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('\u0394\u03bb (arcsec)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    fig2.suptitle(
        '\u0420\u0430\u0437\u043d\u0438\u0446\u0430 \u043c\u0435\u0436\u0434\u0443 '
        '\u043c\u043e\u0434\u0435\u043b\u044f\u043c\u0438 '
        '\u043f\u0440\u0435\u0446\u0435\u0441\u0441\u0438\u0438 \u0437\u0430 1980 \u043b\u0435\u0442',
        fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('model_differences_2000yr.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 3: dϖ/dt — наблюдение vs модели ---
    fig3, axes3 = plt.subplots(2, 1, figsize=(18, 10))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes3[idx]
        r = prec_results[name]
        yrs = r['years']

        ax.plot(yrs, r['prec_obs'], 'k-', lw=0.3, alpha=0.3,
                label='\u041d\u0430\u0431\u043b\u044e\u0434\u0435\u043d\u0438\u0435 (d\u03c0/dt)')
        for model in ['P0', 'P_GR', 'P_391838', 'P_A391838_hybrid']:
            label = model_labels.get(model, model)
            ax.plot(yrs, r['prec_models'][model], lw=0.8, alpha=0.8,
                    color=colors[model], label=label)
        ax.set_title(f'{name}: \u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c '
                     '\u043f\u0440\u0435\u0446\u0435\u0441\u0441\u0438\u0438 '
                     '(arcsec/\u0432\u0435\u043a)',
                     fontweight='bold', fontsize=13)
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('arcsec/\u0432\u0435\u043a')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    fig3.suptitle(
        '\u041d\u0430\u0431\u043b\u044e\u0434\u0430\u0435\u043c\u0430\u044f '
        '\u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u043f\u0440\u0435\u0446\u0435\u0441\u0441\u0438\u0438 '
        'vs \u043c\u043e\u0434\u0435\u043b\u0438',
        fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('precession_rate_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 4: a(t) и e(t) ---
    fig4, axes4 = plt.subplots(2, 2, figsize=(18, 10))
    for idx, name in enumerate(['Mercury', 'Mars']):
        r = prec_results[name]
        yrs = r['years']

        ax_e = axes4[0][idx]
        ax_e.plot(yrs, r['e'], 'b-', lw=0.3, alpha=0.5)
        ax_e.set_title(f'{name}: e(t)', fontweight='bold')
        ax_e.set_xlabel('\u0413\u043e\u0434\u044b')
        ax_e.set_ylabel('e')
        ax_e.grid(True, alpha=0.2)

        ax_a = axes4[1][idx]
        ax_a.plot(yrs, r['a'], 'r-', lw=0.3, alpha=0.5)
        ax_a.set_title(f'{name}: a(t)', fontweight='bold')
        ax_a.set_xlabel('\u0413\u043e\u0434\u044b')
        ax_a.set_ylabel('a (\u0430.\u0435.)')
        ax_a.grid(True, alpha=0.2)

    fig4.suptitle('\u041e\u0441\u043a\u0443\u043b\u0438\u0440\u0443\u044e\u0449\u0438\u0435 '
                  '\u044d\u043b\u0435\u043c\u0435\u043d\u0442\u044b (DE422, Sun-only)',
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('osculating_elements.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 5: долгота ---
    fig5, ax5 = plt.subplots(1, 1, figsize=(16, 6))
    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        lons = []
        sample_days = np.arange(0, int(1980 * 365.25), 365)
        for d in sample_days:
            dt = datetime(1010, 1, 1) + timedelta(days=int(d))
            lon, _ = real_helio_long(name, dt)
            lons.append(lon)
        years = sample_days / 365.25
        ax5.plot(years, lons, lw=0.8, label=name, alpha=0.7)
    ax5.set_title('\u0413\u0435\u043b\u0438\u043e\u0446\u0435\u043d\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u044f '
                  '\u0434\u043e\u043b\u0433\u043e\u0442\u0430 (DE422, 1010\u20132990)',
                  fontweight='bold')
    ax5.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
    ax5.set_ylabel('\u03bb (\u0433\u0440\u0430\u0434)')
    ax5.legend()
    ax5.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('heliocentric_longitude_2000yr.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 6: бюджет прецессии ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes[idx]
        r = prec_results[name]
        yrs = r['years']

        ax.plot(yrs, r['prec_obs'], 'k-', lw=0.3, alpha=0.25,
                label='DE422 total (\u043c\u0433\u043d\u043e\u0432\u0435\u043d\u043d\u0430\u044f)')

        newt_label = 'Newtonian (\u043e\u043f\u0443\u0431\u043b.)' if name == 'Mercury' else 'Newtonian (\u043e\u0440\u0438\u0435\u043d\u0442.)'
        ax.axhline(NEWTONIAN_PLANETARY[name], color='gray', ls='--',
                   lw=1.5, label=newt_label)

        ax.plot(yrs, r['residual_after_newtonian'], color='red',
                lw=0.8, alpha=0.5, label='DE422 \u2212 Newtonian')

        ax.plot(yrs, r['prec_models']['P_GR'], color='blue',
                lw=1.5, label='P_GR (\u0442\u0435\u043e\u0440\u0438\u044f)')

        ax.plot(yrs, r['prec_models']['P_391838'], color='green',
                lw=1.5, label='P_391838 (\u0442\u0435\u043e\u0440\u0438\u044f)')

        # Секулярные скорости — три метода
        ax.axhline(r['secular_prec'], color='black', ls=':',
                   lw=1, label=f'\u0421\u0435\u043a.: {r["secular_prec"]:.2f}')
        ax.axhline(r['secular_central'], color='orange', ls=':',
                   lw=1, label=f'\u0426\u0435\u043d\u0442\u0440.: {r["secular_central"]:.2f}')

        ax.set_title(name, fontsize=13)
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('arcsec / \u0432\u0435\u043a')
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=7, loc='upper right')

    plt.tight_layout()
    plt.savefig('newtonian_residual_vs_gr.png', dpi=150, bbox_inches='tight')
    plt.close()

    # --- График 7: скользящее окно регрессии ---
    fig7, axes7 = plt.subplots(1, 2, figsize=(16, 6))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes7[idx]
        r = prec_results[name]
        rw = r['reg_windows']
        
        ax.plot(rw['window_years'], rw['window_rates'], 'b-', lw=1.5,
                label='\u0421\u043a\u043e\u043b\u044c\u0437. \u043e\u043a\u043d\u043e 500 \u043b\u0435\u0442')
        ax.axhline(rw['full'], color='red', ls='--', lw=1.5,
                   label=f'\u041f\u043e\u043b\u043d.: {rw["full"]:.2f}')
        ax.axhline(rw['central'], color='green', ls=':', lw=1.5,
                   label=f'\u0426\u0435\u043d\u0442\u0440.: {rw["central"]:.2f}')
        ax.axhline(rw['smoothed'], color='orange', ls='-.', lw=1.5,
                   label=f'\u0421\u0433\u043b\u0430\u0436.: {rw["smoothed"]:.2f}')
        
        ax.set_title(f'{name}: \u0441\u0435\u043a\u0443\u043b\u044f\u0440\u043d\u0430\u044f '
                     '\u0441\u043a\u043e\u0440\u043e\u0441\u0442\u044c \u043f\u0440\u0435\u0446\u0435\u0441\u0441\u0438\u0438',
                     fontweight='bold')
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('arcsec / \u0432\u0435\u043a')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig('regression_windows.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\n{'='*80}")
    print("\u0413\u0440\u0430\u0444\u0438\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b:")
    print("  long_comparison_2000yr.png")
    print("  model_differences_2000yr.png")
    print("  precession_rate_comparison.png")
    print("  osculating_elements.png")
    print("  heliocentric_longitude_2000yr.png")
    print("  newtonian_residual_vs_gr.png")
    print("  regression_windows.png")
    print(f"{'='*80}")
