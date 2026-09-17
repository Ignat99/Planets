"""
Сравнение моделей прецессии с NASA DE422.
Ревизия 5: интегрирование domega(t), угловая разность, переименование GR_obs.

Модели:
  DE422_minus_VSOP:  dϖ/dt(DE422) − dϖ/dt(VSOP87E)               — диагностическая разность
  P0:                 K / a₀^(5/2)                                — без e-поправки
  P_GR:               K / (a₀^(5/2) * (1-e₀²))                    — стандартная GR
  P_391838:           (K + L*(A391838(e₀)-1)) / a₀^(5/2)          — A391838, постоянные a₀, e₀
  P_391838_et:        (K + L*(A391838(e(t))-1)) / a(t)^(5/2)      — A391838, оскулирующие a(t), e(t)

Ключевые исправления (от rev.4 к rev.5):
  1. P_391838_et и DE422_minus_VSOP — кумулятивное интегрирование domega(t)
     вместо domega(t)*day (трапецеидальное суммирование)
  2. dvarpi_de422 — угловая разность через angular_difference_deg()
     для корректной обработки перехода через 0/360°
  3. GR_obs → DE422_minus_VSOP — диагностическая разность, а не «наблюдаемая GR-поправка»
  4. compute_gr_component() удалена (содержала логическую ошибку)
  5. varpi — проекционная долгота вектора эксцентриситета (не 3D Ω+ω)
  6. osculating_full — Sun-only оскулирующие элементы из DE422
  7. Earth: DE422 planets[399] vs VSOP87E EMB — несогласованность отмечена
  8. Mars Newtonian 1598.2 — помечен как ориентировочная оценка

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
# Mercury: Park et al. (2017), Wikipedia "Tests of general relativity"
# Mars:    приближённое значение, требует отдельной верификации
#          GR для Марса = 1.351 (Iorio 2005)
#          Полная из DE422 ≈ 1599.5 → Newtonian ≈ 1598.2
NEWTONIAN_PLANETARY = {
    'Mercury': 532.3035,   # arcsec/century, хорошо подтверждено
    'Mars':    1598.2,     # ОРИЕНТИРОВОЧНО, требует верификации источника
}

# Солнечный J2 (малый вклад, для справки)
SOLAR_J2_CONTRIBUTION = {
    'Mercury': 0.0286,
    'Mars':    0.00013,   # значительно меньше
}

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def angular_difference_deg(angle2, angle1):
    """Угловая разность в градусах с корректной обработкой перехода через 0/360°."""
    return (angle2 - angle1 + 180.0) % 360.0 - 180.0

def cumulative_trapezoid_manual(y, x):
    """Кумулятивное трапецеидальное интегрирование без SciPy.
    Возвращает массив той же длины, что и вход, с initial=0.
    """
    result = np.zeros(len(y))
    for i in range(1, len(y)):
        result[i] = result[i - 1] + 0.5 * (y[i] + y[i - 1]) * (x[i] - x[i - 1])
    return result


# ============================================================
# ЗАГРУЗКА ЭФЕМЕРИДЫ
# ============================================================
print("Загрузка эфемериды DE422...")
planets = load('de422.bsp')
ts = load.timescale()

SUN = planets[10]

# Небесные тела — геоцентр Земли (399), не EMB (3)
# ВНИМАНИЕ: VSOP87E для Земли загружается из VSOP87.emb (барицентр Земля-Луна),
# что создаёт несогласованность DE422 Earth vs VSOP87E EMB.
# Для строгого сравнения нужно либо EMB vs EMB, либо исключить Землю из прецессионного анализа.
BODIES = {
    'Mercury': planets[1],
    'Venus':   planets[2],
    'Earth':   planets[399],   # геоцентр Земли, не EMB
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
    elif model in ('P_391838', 'P_391838_et'):
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
# ГЕЛИОЦЕНТРИЧЕСКАЯ ПОЗИЦИЯ — ПРЯМОЙ ВЕКТОР (без observe)
# ============================================================
def helio_position(name, dt):
    """
    Возвращает гелиоцентрический вектор позиции (а.е.) и скорости (а.е./день)
    в эклиптической системе J2000.
    """
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    sun_at = SUN.at(t)
    body_at = body.at(t)

    r_vec = np.array(body_at.position.au, dtype=float) - np.array(sun_at.position.au, dtype=float)
    v_vec = np.array(body_at.velocity.au_per_d, dtype=float) - np.array(sun_at.velocity.au_per_d, dtype=float)

    # Преобразуем из экваториальной (ICRF) в эклиптическую (J2000)
    r_vec = to_ecliptic(r_vec)
    v_vec = to_ecliptic(v_vec)

    return r_vec, v_vec

def real_helio_long(name, dt):
    """Гелиоцентрическая эклиптическая долгота (J2000) — прямой вектор."""
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
# ВНИМАНИЕ: Это Sun-only оскулирующие элементы, вычисленные из DE422 state vector
# с использованием двухтельных формул и солнечного GM.
# Они содержат короткопериодические колебания от планетных возмущений,
# уже заложенных в DE422, но не являются эквивалентом динамических элементов
# VSOP87E или канонических элементов DE422.
def osculating_full(name, dt):
    """
    Полный набор оскулирующих элементов в эклиптической системе J2000.
    Возвращает (a_osc, e_osc, varpi_deg, M_rad).

    varpi_deg — проекционная долгота вектора эксцентриситета на плоскость
    J2000 ecliptic. Это не полная 3D-долгота перицентра (Ω + ω).
    Для Меркурия (i≈7°) и Марса (i≈1.85°) наклонение может давать
    поправки на уровне угловых секунд за столетие.
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
    # Это не полная 3D-долгота перицентра (Ω + ω).
    varpi_deg = np.degrees(np.arctan2(e_vec[1], e_vec[0])) % 360.0

    # Истинная аномалия: угол между e_vec и r_vec
    nu = np.arccos(np.clip(np.dot(e_vec, r_vec) / (e_osc * r), -1, 1))
    if np.dot(np.cross(e_vec, r_vec), h_vec) < 0:
        nu = 2 * np.pi - nu

    M = true_to_mean_anomaly(nu, e_osc)

    return a_osc, e_osc, varpi_deg, M

# ============================================================
# МОДЕЛЬНАЯ ДОЛГОТА — для постоянных моделей (одиночная точка)
# ============================================================
def compute_model_long(name, model, start_date, day):
    """
    Вычисляет модельную долготу для постоянных моделей (P0, P_GR, P_391838).
    Для моделей с переменной скоростью (P_391838_et, DE422_minus_VSOP)
    используйте compute_model_long_array() — с кумулятивным интегрированием.
    """
    p = PLANETS[name]

    if model in ('P_391838_et', 'DE422_minus_VSOP'):
        raise ValueError(
            f"Model {model} requires cumulative integration. "
            "Use compute_model_long_array() instead."
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
# МОДЕЛЬНАЯ ДОЛГОТА — массив с кумулятивным интегрированием
# ============================================================
def compute_model_long_array(name, model, start_date, days_arr, vsop_data):
    """
    Вычисляет модельные долготы для массива дней.

    Для постоянных моделей (P0, P_GR, P_391838): domega = const,
    поэтому domega * day точно — перебор по точкам.

    Для переменных моделей (P_391838_et, DE422_minus_VSOP):
    кумулятивное трапецеидальное интегрирование domega(t):
      varpi(t) = varpi(0) + ∫₀ᵗ domega(τ) dτ
    """
    days_float = days_arr.astype(float)

    if model in ('P_391838_et', 'DE422_minus_VSOP'):
        # --- Переменные модели: кумулятивное интегрирование ---

        # Первый проход: собираем оскулирующие элементы
        a_arr = np.zeros(len(days_arr))
        e_arr = np.zeros(len(days_arr))
        varpi_arr = np.zeros(len(days_arr))
        M_arr = np.zeros(len(days_arr))

        for i, day in enumerate(days_arr):
            dt = start_date + timedelta(days=int(day))
            a_t, e_t, varpi_t, M_t = osculating_full(name, dt)
            a_arr[i] = a_t
            e_arr[i] = e_t
            varpi_arr[i] = varpi_t
            M_arr[i] = M_t

        varpi_0 = varpi_arr[0]

        # Вычисление массива скоростей прецессии
        domega_arr = np.zeros(len(days_arr))

        if model == 'P_391838_et':
            for i in range(len(days_arr)):
                domega_arr[i] = precession_deg_per_day(model, a_arr[i], e_arr[i])

        elif model == 'DE422_minus_VSOP':
            for i in range(len(days_arr)):
                # DE422 мгновенная скорость прецессии (центральная разность
                # с корректной угловой разностью)
                if i == 0:
                    dvarpi_de422 = (
                        angular_difference_deg(varpi_arr[1], varpi_arr[0])
                        / (days_float[1] - days_float[0])
                    )
                elif i == len(days_arr) - 1:
                    dvarpi_de422 = (
                        angular_difference_deg(varpi_arr[-1], varpi_arr[-2])
                        / (days_float[-1] - days_float[-2])
                    )
                else:
                    dvarpi_de422 = (
                        angular_difference_deg(varpi_arr[i + 1], varpi_arr[i - 1])
                        / (days_float[i + 1] - days_float[i - 1])
                    )

                # VSOP87E аналитическая скорость прецессии
                dt = start_date + timedelta(days=int(days_arr[i]))
                t_mill = datetime_to_vsop87_t(dt)
                _, _, dvarpi_vsop = vsop87e_compute(vsop_data[name], t_mill)
                dvarpi_vsop_deg_day = dvarpi_vsop / 3600.0 / 100.0 / 365.25

                # Диагностическая разность: DE422 − VSOP87E
                domega_arr[i] = dvarpi_de422 - dvarpi_vsop_deg_day

        # Кумулятивное трапецеидальное интегрирование
        varpi_integrated = np.radians(varpi_0) + np.radians(
            cumulative_trapezoid_manual(domega_arr, days_float)
        )

        # Истинная аномалия из реального M(t) и e(t)
        longitudes = np.degrees(
            varpi_integrated + true_anomaly(M_arr, e_arr)
        ) % 360.0
        return longitudes

    else:
        # --- Постоянные модели: domega = const, domega*day точно ---
        longitudes = np.zeros(len(days_arr))
        for i, day in enumerate(days_arr):
            longitudes[i] = compute_model_long(name, model, start_date, int(day))
        return longitudes

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
# ПРЯМОЕ СРАВНЕНИЕ СКОРОСТЕЙ ПРЕЦЕССИИ
# ============================================================
def run_precession_comparison(years=1980, step_days=30, vsop_data=None):
    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    days = np.arange(0, total_days + 1, step_days)
    years_arr = days / 365.25

    MODELS = ['Newtonian_residual', 'P0', 'P_GR', 'P_391838', 'P_391838_et']

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Сбор d\u03c0/dt для {name}...")
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

        # --- Секулярная скорость через линейную регрессию ---
        coef = np.polyfit(years_arr, varpi_unwrapped, 1)
        secular_rate_deg_per_year = coef[0]
        secular_prec = secular_rate_deg_per_year * 3600 * 100  # arcsec/century

        # --- Мгновенная скорость (dvarpi/dt, содержит короткопериодические колебания) ---
        step_years = step_days / 365.25
        dvarpi = np.gradient(varpi_unwrapped, step_years)
        prec_obs_instant = dvarpi * 3600 * 100  # arcsec/century

        # --- Newtonian residual: DE422 total − published Newtonian ---
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
            if model == 'P_391838_et':
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
            # Полная мгновенная скорость из DE422 (содержит короткопериодические колебания)
            'prec_obs': prec_obs_instant,
            # Секулярная скорость (наклон линейной регрессии за весь интервал)
            'secular_prec': secular_prec,
            # Опубликованный Newtonian
            'newtonian_planetary':
                np.full(len(days), newtonian_val),
            # Остаток после Newtonian (мгновенный)
            'residual_after_newtonian': newtonian_residual_arr,
            # Теоретические модели
            'prec_models': prec_models,
            # Диагностика: DE422 − VSOP87E (НЕ GR!)
            'vsop_difference': vsop_diff_arr,
            'dvarpi_vsop': dvarpi_vsop_arr,
        }

    return results


# ============================================================
# ДЛИННЫЙ РАСЧЁТ (долготы)
# ============================================================
def run_long_comparison(years=1980, step_days=30, vsop_data=None):
    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    # Включаем день 0 для корректного интегрирования
    days_full = np.arange(0, total_days + 1, step_days)
    days = days_full[1:]  # для ошибок: пропускаем день 0

    MODELS = ['DE422_minus_VSOP', 'P0', 'P_GR', 'P_391838', 'P_391838_et']
    MODEL_LABELS = {
        'DE422_minus_VSOP': 'DE422 \u2212 VSOP87E (диагн.)',
        'P0':               'P\u2080 (без e-поправки)',
        'P_GR':             'P_GR (1/(1\u2212e\u00b2))',
        'P_391838':         'P_A391838 (e\u2080)',
        'P_391838_et':      'P_A391838 (a(t),e(t))',
    }

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Расчёт {name} на {years} лет (1010\u2013{1010+years})...")
        results[name] = {}

        # Предвычисляем реальные долготы для всех дней (включая 0)
        lon_real_arr = np.zeros(len(days_full))
        for i, day in enumerate(days_full):
            dt = start_dt + timedelta(days=int(day))
            lon_real_arr[i], _ = real_helio_long(name, dt)

        for model in MODELS:
            # Вычисляем модельные долготы для всех дней (включая 0)
            lon_model_arr = compute_model_long_array(
                name, model, start_dt, days_full, vsop_data
            )

            # Ошибки: пропускаем день 0
            errors = []
            for i in range(1, len(days_full)):
                d = (lon_model_arr[i] - lon_real_arr[i] + 180) % 360 - 180
                if i > 1:
                    while d - errors[-1] > 180: d -= 360
                    while d - errors[-1] < -180: d += 360
                errors.append(d)
            results[name][model] = np.array(errors)

    return days, results, MODEL_LABELS, MODELS


# ============================================================
# VSOP87E: ПАРСИНГ
# ============================================================
def parse_vsop87e(filename):
    series = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}  # a, lambda, h, k, p, q
    
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
    MODELS = ['DE422_minus_VSOP', 'P0', 'P_GR', 'P_391838', 'P_391838_et']

    # Массив дней: 0..81 (включаем 0 для интегрирования)
    days_test_full = np.arange(0, NUM_DAYS + 1)
    days_test = days_test_full[1:]  # 1..81

    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        print(f"\n  {name}:")

        # Реальные долготы (включая день 0)
        lon_real_test = np.zeros(len(days_test_full))
        for i, day in enumerate(days_test_full):
            dt = start_dt + timedelta(days=int(day))
            lon_real_test[i], _ = real_helio_long(name, dt)

        for model in MODELS:
            lon_models = compute_model_long_array(
                name, model, start_dt, days_test_full, vsop_data
            )
            # Ошибки: дни 1..81
            rms_list = []
            for i in range(1, len(days_test_full)):
                d = (lon_models[i] - lon_real_test[i] + 180) % 360 - 180
                rms_list.append(d**2)
            rms = np.sqrt(np.mean(rms_list))
            print(f"    {model:20s}  RMS = {rms:.6f}\u00b0")

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
        prec_results = run_precession_comparison(years=1980, step_days=30, vsop_data=vsop_data)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback; traceback.print_exc()
        prec_results = None

    if prec_results is not None:
        for name in ['Mercury', 'Mars']:
            r = prec_results[name]
            secular = r['secular_prec']
            newtonian = NEWTONIAN_PLANETARY[name]
            residual_secular = secular - newtonian

            print(f"\n  {name}:")
            print(f"             {'Модель':>25s}  {'Среднее':>20s}  {'Секулярная':>20s}")
            print(f"  {'-'*70}")
            print(f"  {'DE422 мгновенная (d\u03c0/dt)':>25s}  {np.mean(r['prec_obs']):>20.4f}  {secular:>20.4f}")
            print(f"  {'Newtonian (опубл.)':>25s}  {newtonian:>20.4f}  {newtonian:>20.4f}")
            print(f"  {'Residual (DE422\u2212Newt.)':>25s}  {np.mean(r['residual_after_newtonian']):>20.4f}  {residual_secular:>20.4f}")
            print(f"  {'DE422\u2212VSOP87E (диагн.)':>25s}  {np.mean(r['vsop_difference']):>20.4f}  {'\u2014':>20s}")
            print()

            for model in ['P0', 'P_GR', 'P_391838', 'P_391838_et']:
                val = np.mean(r['prec_models'][model])
                print(f"  {model:>25s}  {val:>20.4f}")

            print()
            print(f"  Секулярный остаток vs GR:      {residual_secular:.4f} vs {np.mean(r['prec_models']['P_GR']):.4f}")
            print(f"  Секулярный остаток vs A391838: {residual_secular:.4f} vs {np.mean(r['prec_models']['P_391838']):.4f}")

    # --- Длинный расчёт долготы ---
    print(f"\n{'='*80}")
    print("Длинный расчёт: 1980 лет, шаг 30 дней")
    print(f"{'='*80}")

    days_arr, long_results, model_labels, model_list = run_long_comparison(
        years=1980, step_days=30, vsop_data=vsop_data)

    # --- График 1: расхождение с эфемеридой ---
    fig1, axes1 = plt.subplots(1, 2, figsize=(18, 8))
    colors = {
        'DE422_minus_VSOP': '#9b59b6',
        'P0':               '#95a5a6',
        'P_GR':             '#3498db',
        'P_391838':         '#e74c3c',
        'P_391838_et':      '#2ecc71',
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
    plt.show()

    # --- График 2: разница между моделями ---
    fig2, axes2 = plt.subplots(1, 2, figsize=(18, 8))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes2[idx]
        e = PLANETS[name]['e']

        d_gr_p0 = long_results[name]['P_GR'] - long_results[name]['P0']
        d_a39_p0 = long_results[name]['P_391838'] - long_results[name]['P0']
        d_a39_gr = long_results[name]['P_391838'] - long_results[name]['P_GR']
        d_a39et_gr = long_results[name]['P_391838_et'] - long_results[name]['P_GR']

        years = days_arr / 365.25
        ax.plot(years, d_gr_p0 * 3600, 'b-', lw=1.5,
                label='P_GR \u2212 P\u2080', alpha=0.8)
        ax.plot(years, d_a39_p0 * 3600, 'r-', lw=1.5,
                label='P_A391838(e\u2080) \u2212 P\u2080', alpha=0.8)
        ax.plot(years, d_a39_gr * 3600, 'g--', lw=1.5,
                label='P_A391838(e\u2080) \u2212 P_GR', alpha=0.8)
        ax.plot(years, d_a39et_gr * 3600, 'm:', lw=1.5,
                label='P_A391838(a(t),e(t)) \u2212 P_GR', alpha=0.8)
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
    plt.show()

    # --- График 3: dϖ/dt — наблюдение vs модели ---
    if prec_results is not None:
        fig3, axes3 = plt.subplots(2, 1, figsize=(18, 10))
        for idx, name in enumerate(['Mercury', 'Mars']):
            ax = axes3[idx]
            r = prec_results[name]
            yrs = r['years']

            ax.plot(yrs, r['prec_obs'], 'k-', lw=0.3, alpha=0.3,
                    label='DE422 \u043c\u0433\u043d\u043e\u0432\u0435\u043d\u043d\u0430\u044f (d\u03c0/dt, \u043e\u0441\u043a\u0443\u043b\u0438\u0440\u0443\u044e\u0449\u0430\u044f)')
            for model in ['P0', 'P_GR', 'P_391838', 'P_391838_et']:
                ax.plot(yrs, r['prec_models'][model], lw=0.8, alpha=0.8,
                        color=colors[model], label=model_labels[model])
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
        plt.show()

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
        plt.show()

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
    plt.show()

    # ============================================================
    # ГРАФИК: БЮДЖЕТ ПРЕЦЕССИИ
    # ============================================================
    if prec_results is not None:
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        for idx, name in enumerate(['Mercury', 'Mars']):
            ax = axes[idx]
            r = prec_results[name]
            yrs = r['years']

            # Полная мгновенная прецессия из DE422
            ax.plot(yrs, r['prec_obs'], 'k-', lw=0.3, alpha=0.25,
                    label='DE422 \u043c\u0433\u043d\u043e\u0432\u0435\u043d\u043d\u0430\u044f')

            # Newtonian planetary
            if name == 'Mars':
                ax.axhline(NEWTONIAN_PLANETARY[name], color='gray', ls='--',
                           lw=1.5, label='Newtonian (\u043e\u0440\u0438\u0435\u043d\u0442.)')
            else:
                ax.axhline(NEWTONIAN_PLANETARY[name], color='gray', ls='--',
                           lw=1.5, label='Newtonian (\u043e\u043f\u0443\u0431\u043b.)')

            # Residual после Newtonian
            ax.plot(yrs, r['residual_after_newtonian'], color='red',
                    lw=0.8, alpha=0.5, label='DE422 \u2212 Newtonian')

            # GR теория
            ax.plot(yrs, r['prec_models']['P_GR'], color='blue',
                    lw=1.5, label='P_GR (\u0442\u0435\u043e\u0440\u0438\u044f)')

            # A391838 теория
            ax.plot(yrs, r['prec_models']['P_391838'], color='green',
                    lw=1.5, label='P_391838 (\u0442\u0435\u043e\u0440\u0438\u044f)')

            # Секулярная скорость (регрессия)
            ax.axhline(r['secular_prec'], color='black', ls=':',
                       lw=1, label=f'\u0421\u0435\u043a\u0443\u043b\u044f\u0440\u043d\u0430\u044f: {r["secular_prec"]:.2f}')

            ax.set_title(name, fontsize=13)
            ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
            ax.set_ylabel('arcsec / \u0432\u0435\u043a')
            ax.grid(True, alpha=0.2)
            ax.legend(fontsize=8, loc='upper right')

        plt.tight_layout()
        plt.savefig('newtonian_residual_vs_gr.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("  newtonian_residual_vs_gr.png")

    print(f"\n{'='*80}")
    print("\u0413\u0440\u0430\u0444\u0438\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b:")
    print("  long_comparison_2000yr.png")
    print("  model_differences_2000yr.png")
    print("  precession_rate_comparison.png")
    print("  osculating_elements.png")
    print("  heliocentric_longitude_2000yr.png")
    print(f"{'='*80}")
