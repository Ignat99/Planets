"""
Сравнение четырёх моделей прецессии с точными эфемеридами NASA (DE422).
Ревизия: оскулирующие элементы через позицию и скорость.

Модели:
  P0:          K / a^(5/2)                        — без e-поправки
  P_GR:        K / (a^(5/2) * (1-e^2))            — стандартная GR
  P_391838:    (K + L*(A391838(e)-1)) / a^(5/2)   — A391838, постоянный e
  P_391838_et: (K + L*(A391838(e(t))-1)) / a^(5/2) — A391838, оскулирующий e(t)

Требования: pip install skyfield numpy matplotlib
Эфемерида: de422.bsp (загружается автоматически)
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from skyfield.api import load

# ============================================================
# ЗАГРУЗКА ЭФЕМЕРИДЫ
# ============================================================
print("Загрузка эфемериды DE422...")
planets = load('de422.bsp')
ts = load.timescale()

SUN = planets[10]
EARTH = planets[399]

BODIES = {
    'Mercury': planets[1],
    'Venus':   planets[2],
    'Earth':   planets[3],
    'Mars':    planets[4],
    'Jupiter': planets[5],
    'Saturn':  planets[6],
    'Uranus':  planets[7],
    'Neptune': planets[8],
    'Pluto':   planets[9],
}

PLANETS = {
    'Mercury': {'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456,  'period': 87.969},
    'Venus':   {'a': 0.723332, 'e': 0.006772, 'varpi0': 131.533, 'period': 224.701},
    'Earth':   {'a': 1.000000, 'e': 0.016709, 'varpi0': 102.937, 'period': 365.256},
    'Mars':    {'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040, 'period': 686.98},
}

# Гравитационный параметр Солнца в а.е.³/день²
# GM_SUN = 1.32712440018e20 м³/с²
# 1 а.е. = 1.495978707e11 м, 1 день = 86400 с
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

# ============================================================
# КАЛИБРОВКА
# ============================================================
K = 3.8313
L = 0.6496

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
    return prec / 3600.0 / 36525.0

# ============================================================
# ТОЧНЫЕ ГЕЛИОЦЕНТРИЧЕСКИЕ КООРДИНАТЫ (геометрические, без светового времени)
# ============================================================
def real_helio_long(name, dt):
    """Гелиоцентрическая эклиптическая долгота (J2000) из DE422."""
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    # Геометрическая позиция — без поправки на световое время
    pos = SUN.at(t).observe(body)
    lat, lon, distance = pos.ecliptic_latlon()
    return np.degrees(lon.radians) % 360.0, distance.au

# ============================================================
# ОСКУЛИРУЮЩИЕ ЭЛЕМЕНТЫ через позицию и скорость
# ============================================================
def osculating_elements(name, dt):
    """
    Вычисляет оскулирующие a и e из геометрической позиции и скорости
    относительно Солнца (без поправки на световое время).
    
    Возвращает (a_osc, e_osc).
    """
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]

    # Геометрические позиции относительно барицентра Солнечной системы
    sun_at = SUN.at(t)
    body_at = body.at(t)

    # Гелиоцентрические позиция и скорость (body − Sun)
    r_vec = np.array(body_at.position.au, dtype=float) - np.array(sun_at.position.au, dtype=float)
    v_vec = np.array(body_at.velocity.au_per_d, dtype=float) - np.array(sun_at.velocity.au_per_d, dtype=float)

    r = np.sqrt(np.sum(r_vec**2))
    v = np.sqrt(np.sum(v_vec**2))

    mu = GM_SUN_AU3_DAY2

    # Удельная энергия
    energy = 0.5 * v**2 - mu / r

    # Момент импульса
    h_vec = np.cross(r_vec, v_vec)
    h_mag = np.sqrt(np.sum(h_vec**2))

    # Большая полуось
    if energy >= 0:
        a_osc = PLANETS[name]['a']
    else:
        a_osc = -mu / (2 * energy)

    # Вектор эксцентриситета (вектор Лапласа)
    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r
    e_osc = np.sqrt(np.sum(e_vec**2))

    return a_osc, min(max(e_osc, 0.0), 0.99)


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
        _, e_start = osculating_elements(name, start_date)
        dt_current = start_date + timedelta(days=day)
        _, e_current = osculating_elements(name, dt_current)
    else:
        e_start = e0
        e_current = e0

    domega = precession_deg_per_day(model, p['a'], e_current)

    lon_0, _ = real_helio_long(name, start_date)
    nu_0 = (np.radians(lon_0) - varpi0 + np.pi) % (2 * np.pi) - np.pi
    M_0 = true_to_mean_anomaly(nu_0, e_start)

    M = M_0 + n * day
    varpi = varpi0 + np.radians(domega) * day
    lon = np.degrees(varpi + true_anomaly(M, e_current)) % 360.0
    return lon

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
# СТРУКТУРА И СВЯЗЬ С A391838
# ============================================================
def print_structure():
    print(f"\n{'='*80}")
    print("Структура деления Сварожьего Круга")
    print(f"{'='*80}")

    print(f"\n  Делители (АХиневич):     16, 9, 9, 72, 760")
    print(f"  Делители (реконструкция): 1, 2, 9, 72, 760")
    print(f"  A391838 (e.g.f.):         1, 1, 2, 9, 72, 760, ...")
    print(f"\n  Реконструкция vs A391838:")
    print(f"    1 (Священное лето)     ~ A391838[0] = 1")
    print(f"    2 (сороковники)        ~ A391838[2] = 2")
    print(f"    9 (залы)               ~ A391838[3] = 9")
    print(f"    72 (лавки)             ~ A391838[4] = 72")
    print(f"    760 (места)            ~ A391838[5] = 760")
    print(f"\n  Совпадение: 2, 9, 72, 760 — четыре делителя подряд")

    total_akh = 16 * 9 * 9 * 72 * 760
    total_recon = 1 * 2 * 9 * 72 * 760
    print(f"\n  Полное деление (АХиневич):      16×9×9×72×760 = {total_akh}")
    print(f"  Полное деление (реконструкция):  1×2×9×72×760  = {total_recon}")
    print(f"  Точность места (АХиневич):      {360*3600/total_akh:.6f} arcsec")
    print(f"  Точность места (реконструкция): {360*3600/total_recon:.6f} arcsec")

    print(f"\n  Наблюдаемое числовое совпадение — не установленная физическая связь.")

# ============================================================
# Таблица вкладов A391838
# ============================================================
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
# ДЛИННЫЙ РАСЧЁТ
# ============================================================
def run_long_comparison(years=1980, step_days=30):
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
# MAIN
# ============================================================
if __name__ == '__main__':

    print_structure()
    print_contribution_table()

    # --- Короткий тест (81 день) ---
    print(f"\n{'='*80}")
    print("Короткий тест: 81 день от 2026-09-16")
    print(f"{'='*80}")

    start_dt = datetime(2026, 9, 16, 1, 0, 0)
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
            print(f"    {model:15s}  RMS = {rms:.6f}\u00b0")

    # --- Чертоги ---
    print(f"\n{'='*80}")
    print("Координаты Сварожьего Круга")
    print(f"{'='*80}")

    test_dt = datetime(2026, 9, 16, 7, 21, 0)  # ~07:21 UTC = 09:21 CEST
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

    # --- Оскулирующие e(t) для Меркурия ---
    print(f"\n{'='*80}")
    print("Оскулирующий e(t) для Меркурия (проверка)")
    print(f"{'='*80}")
    for day in [0, 20, 40, 60, 80]:
        dt = datetime(2026, 9, 16) + timedelta(days=day)
        a_osc, e_osc = osculating_elements('Mercury', dt)
        print(f"  День {day:3d}:  a_osc = {a_osc:.8f} а.е.  "
              f"e_osc = {e_osc:.8f}")

    # --- Длинный расчёт ---
    print(f"\n{'='*80}")
    print("Длинный расчёт: 1980 лет, шаг 30 дней")
    print(f"{'='*80}")

    days_arr, long_results, model_labels, model_list = run_long_comparison(
        years=1980, step_days=30)

    # --- График 1: расхождение с эфемеридой ---
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
        '(1010\u20132990)\n\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u0430\u044f '
        '\u043f\u043e\u0434\u0433\u043e\u043d\u043a\u0430 \u0443\u0434\u0430\u043b\u0435\u043d\u0430',
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
                label='P_A391838(e(t)) \u2212 P_GR', alpha=0.8)
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.set_title(f'{name}  (e={e:.4f})', fontweight='bold')
        ax.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
        ax.set_ylabel('\u0394\u03bb (arcsec)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.2)

    fig2.suptitle(
        '\u0420\u0430\u0437\u043d\u0438\u0446\u0430 \u043c\u0435\u0436\u0434\u0443 '
        '\u043c\u043e\u0434\u0435\u043b\u044f\u043c\u0438 '
        '\u043f\u0440\u0435\u0446\u0435\u0441\u0441\u0438\u0438 '
        '\u0437\u0430 1980 \u043b\u0435\u0442',
        fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('model_differences_2000yr.png', dpi=150, bbox_inches='tight')
    plt.show()

    # --- График 3: тренд долготы ---
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
    ax3.set_title(
        '\u0413\u0435\u043b\u0438\u043e\u0446\u0435\u043d\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0430\u044f '
        '\u0434\u043e\u043b\u0433\u043e\u0442\u0430 (NASA DE422, 1010\u20132990)',
        fontweight='bold')
    ax3.set_xlabel('\u0413\u043e\u0434\u044b \u043e\u0442 1010 \u0433.')
    ax3.set_ylabel('\u03bb (\u0433\u0440\u0430\u0434)')
    ax3.legend()
    ax3.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('heliocentric_longitude_2000yr.png', dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n{'='*80}")
    print("\u0413\u0440\u0430\u0444\u0438\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b:")
    print("  long_comparison_2000yr.png")
    print("  model_differences_2000yr.png")
    print("  heliocentric_longitude_2000yr.png")
    print(f"{'='*80}")

