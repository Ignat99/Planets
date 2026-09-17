"""
Сравнение четырёх моделей прецессии с точными эфемеридами NASA (DE422).
Расчёт на тысячи лет + координаты Сварожьего Круга (чертоги/залы/столы/лавки/места).

Модели:
  P0:          K / a^(5/2)                        — без e-поправки
  P_GR:        K / (a^(5/2) * (1-e^2))            — стандартная GR
  P_391838:    (K + L*(A391838(e)-1)) / a^(5/2)   — A391838, постоянный e
  P_391838_et: (K + L*(A391838(e(t))-1)) / a^(5/2) — A391838, реальный e(t)

Координаты чертогов: сдвиг 130°, деление 16→9→9→72→760
  (1, 1, 2, 9, 72, 760 — последовательность A391838)

Требования: pip install skyfield numpy matplotlib
Эфемерида: de422.bsp (загружается автоматически при первом запуске)
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from skyfield.api import load
from skyfield.constants import GM_SUN_DE440_km3_s2 as GM_SUN

# ============================================================
# ЗАГРУЗКА ЭФЕМЕРИДЫ NASA
# ============================================================
print("Загрузка эфемериды DE422...")
planets = load('de422.bsp')
ts = load.timescale()

SUN = planets[10]
EARTH = planets[399]

# Небесные тела (NASA JPL ID)
BODIES = {
    'Mercury': planets[1],
    'Venus':   planets[2],
    'Earth':   planets[3],   # барицентр Земля+Луна
    'Mars':    planets[4],
    'Jupiter': planets[5],
    'Saturn':  planets[6],
    'Uranus':  planets[7],
    'Neptune': planets[8],
    'Pluto':   planets[9],
}

# Параметры планет (J2000 — для моделей прецессии)
PLANETS = {
    'Mercury': {'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456,  'period': 87.969},
    'Venus':   {'a': 0.723332, 'e': 0.006772, 'varpi0': 131.533, 'period': 224.701},
    'Earth':   {'a': 1.000000, 'e': 0.016709, 'varpi0': 102.937, 'period': 365.256},
    'Mars':    {'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040, 'period': 686.98},
}

# ============================================================
# УРАВНЕНИЕ ЦЕНТРА (разложение до e^5)
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

# ============================================================
# ПРЕОБРАЗОВАНИЕ ν → E → M
# ============================================================
def true_to_mean_anomaly(nu, e):
    E = 2 * np.arctan2(
        np.sqrt(1 - e) * np.sin(nu / 2),
        np.sqrt(1 + e) * np.cos(nu / 2)
    )
    E = E % (2 * np.pi)
    M = (E - e * np.sin(E)) % (2 * np.pi)
    return M

# ============================================================
# A391838 — коэффициенты ряда f^{-1}(x)/x
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]
A391838_LABELS = ['1', '1', '1', '3/2', '3', '19/3', '55/4', '31', '72']

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

# ============================================================
# КАЛИБРОВКА
# ============================================================
K = 3.8313   # arcsec/century — эмпирический
L = 0.6496   # вес A391838-поправки — эмпирический

# ============================================================
# МОДЕЛИ ПРЕЦЕССИИ
# ============================================================
def precession_deg_per_day(model, a, e):
    if model == 'P0':
        prec = K / a**2.5
    elif model == 'P_GR':
        prec = K / (a**2.5 * (1 - e**2))
    elif model in ('P_391838', 'P_391838_et'):
        prec = (K + L * (A391838_truncated(e) - 1)) / a**2.5
    else:
        raise ValueError(f"Unknown model: {model}")
    return prec / 3600.0 / 36525.0  # arcsec/century → deg/day

# ============================================================
# ТОЧНЫЕ ГЕЛИОЦЕНТРИЧЕСКИЕ КООРДИНАТЫ ИЗ NASA DE422
# ============================================================
def real_helio_long(name, dt):
    """Гелиоцентрическая эклиптическая долгота (J2000) из DE422."""
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    # Гелиоцентрическая позиция: наблюдение с Солнца
    astrometric = SUN.at(t).observe(body)
    lat, lon, distance = astrometric.ecliptic_latlon()
    return np.degrees(lon.radians) % 360.0, distance.au

def real_helio_elements(name, dt):
    """Гелиоцентрическая долгота, расстояние и эффективный e из DE422."""
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    astrometric = SUN.at(t).observe(body)
    lat, lon, distance = astrometric.ecliptic_latlon()
    lon_deg = np.degrees(lon.radians) % 360.0
    r_au = distance.au
    a = PLANETS[name]['a']
    varpi0 = np.radians(PLANETS[name]['varpi0'])
    hlon = np.radians(lon_deg)
    nu = (hlon - varpi0 + np.pi) % (2 * np.pi) - np.pi
    cos_nu = np.cos(nu)
    discriminant = (r_au * cos_nu) ** 2 + 4 * a * (a - r_au)
    if discriminant < 0:
        e_eff = PLANETS[name]['e']
    else:
        e_eff = (-r_au * cos_nu + np.sqrt(discriminant)) / (2 * a)
        e_eff = max(0.0, min(0.99, e_eff))
    return lon_deg, r_au, e_eff

# ============================================================
# МОДЕЛЬНАЯ ДОЛГОТА
# ============================================================
def compute_model_long(name, model, start_date, day):
    p = PLANETS[name]
    period = p['period']
    e0 = p['e']
    varpi0 = np.radians(p['varpi0'])
    n = 2 * np.pi / period

    if model == 'P_391838_et':
        e_start = real_helio_elements(name, start_date)[2]
        dt_current = start_date + timedelta(days=day)
        e_current = real_helio_elements(name, dt_current)[2]
    else:
        e_start = e0
        e_current = e0

    domega = precession_deg_per_day(model, p['a'], e_current)

    lon_0, _, _ = real_helio_elements(name, start_date)
    nu_0 = (np.radians(lon_0) - varpi0 + np.pi) % (2 * np.pi) - np.pi
    M_0 = true_to_mean_anomaly(nu_0, e_start)

    M = M_0 + n * day
    varpi = varpi0 + np.radians(domega) * day
    lon = np.degrees(varpi + true_anomaly(M, e_current)) % 360.0
    return lon

# ============================================================
# КООРДИНАТЫ СВАРОЖЬЕГО КРУГА
# Деление: 16 чертогов → 9 залов → 9 столов → 72 лавок → 760 мест
# Сдвиг: 130 градусов (дрейф точки равноденствия)
# ============================================================
def calculate_chertog(lon_deg):
    """
    Вычисляет координаты чертога/зала/стола/лавки/места.
    
    Делители: 16, 9, 9, 72, 760
    Шаги:     22.5°, 2.5°, 0.2778°, 0.003858°, 0.00000507°
    
    Возвращает (lon_deg, chertog, zal, stol, lavka, mesto)
    """
    # Базовый сдвиг системы — 130 градусов
    deg = (lon_deg - 130.0) % 360.0

    # Шаги деления
    STEP_CHERTOG = 22.5              # 360 / 16
    STEP_ZAL = STEP_CHERTOG / 9      # 2.5°
    STEP_STOL = STEP_ZAL / 9         # ~0.2778°
    STEP_LAVKA = STEP_STOL / 72      # ~0.003858°
    STEP_MESTO = STEP_LAVKA / 760    # ~0.00000507°

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
# СТРУКТУРА ДЕЛЕНИЯ И СВЯЗЬ С A391838
# ============================================================
def print_chertog_structure():
    print(f"\n{'='*80}")
    print("Структура Сварожьего Круга и связь с A391838")
    print(f"{'='*80}")

    steps = [
        ('Чертог',  16,   22.5,         360.0 / 16),
        ('Зал',     9,    2.5,          22.5 / 9),
        ('Стол',    9,    0.277778,     2.5 / 9),
        ('Лавка',   72,   0.003858,     0.277778 / 72),
        ('Место',   760,  0.000005076,  0.003858 / 760),
    ]

    print(f"\n  {'Уровень':>8}  {'Делитель':>10}  {'Шаг (град)':>16}  "
          f"{'Шаг (выч.)':>16}  {'Накопл.деление':>16}")
    print(f"  {'-'*8}  {'-'*10}  {'-'*16}  {'-'*16}  {'-'*16}")

    cumulative = 1
    for name, div, step_deg, step_calc in steps:
        cumulative *= div
        print(f"  {name:>8}  {div:>10}  {step_deg:>16.9f}  "
              f"{step_calc:>16.9f}  {cumulative:>16}")

    print(f"\n  Полное деление: 16 × 9 × 9 × 72 × 760 = {16*9*9*72*760}")
    print(f"  Точность: 360° / {16*9*9*72*760} = "
          f"{360.0 / (16*9*9*72*760):.12f}°")
    print(f"           = {360*3600 / (16*9*9*72*760):.6f} arcsec")
    print(f"           = {360*3600*1000 / (16*9*9*72*760):.4f} mas")

    print(f"\n  Делители: 16, 9, 9, 72, 760")
    print(f"  A391838:  1, 1, 2, 9, 72, 760, ...")
    print(f"  Совпадение на делителях 9, 72, 760 — три уровня подряд")

    # Проверка: сколько знаков A391838 используется
    print(f"\n  Числа Стирлинга (e.g.f. коэффициенты, ×(n-1)!):")
    b = [1, 1, 2, 9, 72, 760]
    for i, val in enumerate(b):
        print(f"    n={i+1}: b_{i+1} = {val}")

    print(f"\n  Делители чертогов:  16, 9, 9, 72, 760")
    print(f"  Ряд A391838 (e.g.f): 1, 1, 2, 9, 72, 760, ...")
    print(f"  Общие элементы:             9, 72, 760")

    # Точность мест
    total = 16 * 9 * 9 * 72 * 760
    precision_arcsec = 360.0 * 3600.0 / total
    print(f"\n  Точность одного места: {precision_arcsec:.8f} arcsec")
    print(f"  Точность одной лавки:  {360*3600/(16*9*9*72):.6f} arcsec")
    print(f"  Точность одного стола: {360*3600/(16*9*9):.4f} arcsec")
    print(f"  Точность одного зала:  {360*3600/(16*9):.2f} arcsec")

# ============================================================
# РАСЧЁТ НА ДЛИННЫЙ ИНТЕРВАЛ (тысячи лет)
# ============================================================
def run_long_comparison2000(years=2000, step_days=30):
    """
    Сравнение моделей прецессии с NASA DE422 на длинном интервале.
    Возвращает массивы ошибок для каждой модели.
    """
    start_dt = datetime(2000, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    days = np.arange(1, total_days + 1, step_days)

    MODELS = ['P0', 'P_GR', 'P_391838', 'P_391838_et']
    MODEL_LABELS = {
        'P0':          'P₀ (без e-поправки)',
        'P_GR':        'P_GR (1/(1−e²))',
        'P_391838':    'P_A391838 (e₀)',
        'P_391838_et': 'P_A391838 (e(t))',
    }

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Расчёт {name} на {years} лет...")
        results[name] = {}

        for model in MODELS:
            errors = []
            for i, day in enumerate(days):
                dt = start_dt + timedelta(days=int(day))
                lon_model = compute_model_long(name, model, start_dt, int(day))
                lon_real, _ = real_helio_long(name, dt)
                d = (lon_model - lon_real + 180) % 360 - 180
                # Unwrap
                if i > 0:
                    while d - errors[-1] > 180: d -= 360
                    while d - errors[-1] < -180: d += 360
                errors.append(d)
            results[name][model] = np.array(errors)

    return days, results, MODEL_LABELS, MODELS

def run_long_comparison(years=1980, step_days=30):  # years=2000
    """
    Сравнение моделей прецессии с NASA DE422 на длинном интервале.
    DE422 покрывает -3000..+3000, поэтому старт с 1010 г.
    """
    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    total_days = int(years * 365.25)
    days = np.arange(1, total_days + 1, step_days)

    MODELS = ['P0', 'P_GR', 'P_391838', 'P_391838_et']
    MODEL_LABELS = {
        'P0':          'P\u2080 (без e-поправки)',
        'P_GR':        'P_GR (1/(1\u2212e\u00b2))',
        'P_391838':    'P_A391838 (e\u2080)',
        'P_391838_et': 'P_A391838 (e(t))',
    }

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  Расчёт {name} на {years} лет (1010\u2013{1010+years})...")
        results[name] = {}

        for model in MODELS:
            errors = []
            for i, day in enumerate(days):
                dt = start_dt + timedelta(days=int(day))
                lon_model = compute_model_long(name, model, start_dt, int(day))
                lon_real, _ = real_helio_long(name, dt)
                d = (lon_model - lon_real + 180) % 360 - 180
                if i > 0:
                    while d - errors[-1] > 180: d -= 360
                    while d - errors[-1] < -180: d += 360
                errors.append(d)
            results[name][model] = np.array(errors)

    return days, results, MODEL_LABELS, MODELS


# ============================================================
# ОСНОВНОЙ ЗАПУСК
# ============================================================
if __name__ == '__main__':

    # --- Структура чертогов ---
    print_chertog_structure()

    # --- Таблица вкладов A391838 ---
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
              f"1/(1-e²)-1 = {a_gr-1:.6f}")

    # --- Короткий тест (81 день) ---
    print(f"\n{'='*80}")
    print("Короткий тест: 81 день от 2026-09-16")
    print(f"{'='*80}")

    start_dt = datetime(2026, 9, 16, 1, 0, 0)
#    start_dt = datetime(990, 1, 1, 12, 0, 0) # years=2000
    NUM_DAYS = 81
    MODELS = ['P0', 'P_GR', 'P_391838', 'P_391838_et']

    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        print(f"\n  {name}:")
        for model in MODELS:
            rms_list = []
            for day in range(1, NUM_DAYS + 1):
                dt = start_dt + timedelta(days=day)
                lon_model = compute_model_long(name, model, start_dt, day)
                lon_real, _ = real_helio_long(name, dt)
                d = (lon_model - lon_real + 180) % 360 - 180
                rms_list.append(d**2)
            rms = np.sqrt(np.mean(rms_list))
            print(f"    {model:15s}  RMS = {rms:.6f}°")

    # --- Чертоги для текущей даты ---
    print(f"\n{'='*80}")
    print("Координаты Сварожьего Круга на 2026-09-16 08:28 UTC")
    print(f"{'='*80}")

    test_dt = datetime(2026, 9, 16, 8, 28, 0)
    for name in ['Mercury', 'Venus', 'Earth', 'Mars', 'Jupiter', 'Saturn']:
        lon_deg, r_au = real_helio_long(name, test_dt)
        ch, za, st, la, me = calculate_chertog(lon_deg)
        print(f"  {name:10s}  λ={lon_deg:8.4f}°  "
              f"Чертог {ch:2d} — Зал {za} — Стол {st} — "
              f"Лавка {la:3d} — Место {me:5d}  "
              f"r={r_au:.4f} а.е.")

    # --- Длинный расчёт (2000 лет) ---
    print(f"\n{'='*80}")
    print("Длинный расчёт: 2000 лет, шаг 30 дней")
    print(f"{'='*80}")

#    days_arr, long_results, model_labels, model_list = run_long_comparison(
#        years=2000, step_days=30)

    days_arr, long_results, model_labels, model_list = run_long_comparison(
        years=1980, step_days=30)


    # --- График 1: расхождение с эфемеридой (2000 лет) ---
    fig1, axes1 = plt.subplots(1, 2, figsize=(18, 8))
    colors = {
        'P0':          '#95a5a6',
        'P_GR':        '#3498db',
        'P_391838':    '#e74c3c',
        'P_391838_et': '#2ecc71',
    }

    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes1[idx]
        for model in model_list:
            err = long_results[name][model]
            err_calibrated = err - err[0]  # убираем начальную подгонку
            years = days_arr / 365.25
            ax.plot(years, err_calibrated * 3600,
                    color=colors[model], lw=1.2,
                    label=model_labels[model], alpha=0.85)
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.set_title(f'{name}', fontweight='bold', fontsize=13)
#        ax.set_xlabel('Годы от 2000 г.')
        ax.set_xlabel('Годы от 1010 г.')
        ax.set_ylabel('Δλ (arcsec)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

#    fig1.suptitle(
#        'Расхождение моделей прецессии с NASA DE422 (2000 лет)\n'
#        'Начальная подгонка удалена',
#        fontsize=14, fontweight='bold')
    fig1.suptitle(
        'Расхождение моделей прецессии с NASA DE422 (1010\u20132990)\n'
        'Начальная подгонка удалена',
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
                label='P_GR − P₀', alpha=0.8)
        ax.plot(years, d_a39_p0 * 3600, 'r-', lw=1.5,
                label='P_A391838(e₀) − P₀', alpha=0.8)
        ax.plot(years, d_a39_gr * 3600, 'g--', lw=1.5,
                label='P_A391838(e₀) − P_GR', alpha=0.8)
        ax.plot(years, d_a39et_gr * 3600, 'm:', lw=1.5,
                label='P_A391838(e(t)) − P_GR', alpha=0.8)
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.set_title(f'{name}  (e={e:.4f})', fontweight='bold')
        ax.set_xlabel('Годы от 2000 г.')
        ax.set_ylabel('Δλ (arcsec)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    fig2.suptitle(
        'Разница между моделями прецессии за 2000 лет',
        fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('model_differences_2000yr.png', dpi=150, bbox_inches='tight')
    plt.show()

    # --- График 3: чертоги — тренд долготы за 2000 лет ---
#    fig3, ax3 = plt.subplots(1, 1, figsize=(16, 6))

#    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
#        lons = []
#        sample_days = np.arange(0, int(2000 * 365.25), 365)
#        for d in sample_days:
#            dt = datetime(2000, 1, 1) + timedelta(days=int(d))
#            lon, _ = real_helio_long(name, dt)
#            lons.append(lon)
#        years = sample_days / 365.25
#        ax3.plot(years, lons, lw=0.8, label=name, alpha=0.7)

#    ax3.set_title('Гелиоцентрическая долгота (NASA DE422, 2000 лет)',
#                  fontweight='bold')
#    ax3.set_xlabel('Годы от 2000 г.')


    # --- График 3: чертоги — тренд долготы за 1980 лет ---
    fig3, ax3 = plt.subplots(1, 1, figsize=(16, 6))

    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        lons = []
        sample_days = np.arange(0, int(1980 * 365.25), 365)
        for d in sample_days:
            dt = datetime(1010, 1, 1) + timedelta(days=int(d))
            lon, _ = real_helio_long(name, dt)
            lons.append(lon)
        years = sample_days / 365.25
        ax3.plot(years, lons, lw=0.8, label=name, alpha=0.7)

    ax3.set_title('Гелиоцентрическая долгота (NASA DE422, 1010\u20132990)',
                  fontweight='bold')
    ax3.set_xlabel('Годы от 1010 г.')


    ax3.set_ylabel('λ (град)')
    ax3.legend()
    ax3.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('heliocentric_longitude_2000yr.png', dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n{'='*80}")
    print("Графики сохранены:")
    print("  long_comparison_2000yr.png  — расхождение моделей с эфемеридой")
    print("  model_differences_2000yr.png — разница между моделями")
    print("  heliocentric_longitude_2000yr.png — тренд долготы")
    print(f"{'='*80}")
