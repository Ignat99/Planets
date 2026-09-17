"""
Спектральный анализ оскулирующего e(t) и скорости прецессии.
FFT на 1980 лет (1010–2990), сравнение с делителями Сварожьего Круга.

Требования: pip install skyfield numpy matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from skyfield.api import load

# ============================================================
# ЗАГРУЗКА
# ============================================================
print("Загрузка DE422...")
planets = load('de422.bsp')
ts = load.timescale()

SUN = planets[10]
BODIES = {
    'Mercury': planets[1],
    'Mars':    planets[4],
}

PLANETS = {
    'Mercury': {'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456, 'period': 87.969},
    'Mars':    {'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040, 'period': 686.98},
}

GM_SUN_AU3_DAY2 = 1.32712440018e20 / (1.495978707e11)**3 * (86400)**2

# ============================================================
# A391838
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

K = 3.8313
L = 0.6496

# ============================================================
# ОСКУЛИРУЮЩИЕ ЭЛЕМЕНТЫ
# ============================================================
def osculating_elements(name, dt):
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    sun_at = SUN.at(t)
    body_at = body.at(t)
    r_vec = np.array(body_at.position.au, dtype=float) - np.array(sun_at.position.au, dtype=float)
    v_vec = np.array(body_at.velocity.au_per_d, dtype=float) - np.array(sun_at.velocity.au_per_d, dtype=float)
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
    return a_osc, min(max(e_osc, 0.0), 0.99)

# ============================================================
# ГЕЛИОЦЕНТРИЧЕСКАЯ ДОЛГОТА
# ============================================================
def real_helio_long(name, dt):
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    pos = SUN.at(t).observe(body)
    lat, lon, distance = pos.ecliptic_latlon()
    return np.degrees(lon.radians) % 360.0, distance.au

# ============================================================
# СКОРОСТЬ ПРЕЦЕССИИ ИЗ НАБЛЮДЕНИЯ
# (производная долготы перигелия по времени)
# ============================================================
def observed_varpi_rate(name, dt, dt_step=10):
    """
    Оценивает скорость прецессии долготы перигелия
    через конечную разность за dt_step дней.
    """
    p = PLANETS[name]
    varpi0 = np.radians(p['varpi0'])
    a = p['a']

    # Два момента времени
    dt1 = dt
    dt2 = dt + timedelta(days=dt_step)

    _, e1 = osculating_elements(name, dt1)
    _, e2 = osculating_elements(name, dt2)

    # Долгота перигелия из позиции и e_vec
    t1 = ts.utc(dt1.year, dt1.month, dt1.day, dt1.hour, dt1.minute, dt1.second)
    t2 = ts.utc(dt2.year, dt2.month, dt2.day, dt2.hour, dt2.minute, dt2.second)

    sun1 = SUN.at(t1)
    sun2 = SUN.at(t2)
    body1 = BODIES[name].at(t1)
    body2 = BODIES[name].at(t2)

    r1 = np.array(body1.position.au, float) - np.array(sun1.position.au, float)
    r2 = np.array(body2.position.au, float) - np.array(sun2.position.au, float)
    v1 = np.array(body1.velocity.au_per_d, float) - np.array(sun1.velocity.au_per_d, float)
    v2 = np.array(body2.velocity.au_per_d, float) - np.array(sun2.velocity.au_per_d, float)

    h1 = np.cross(r1, v1)
    h2 = np.cross(r2, v2)

    # Вектор эксцентриситета → направление перигелия
    e_vec1 = np.cross(v1, h1) / GM_SUN_AU3_DAY2 - r1 / np.sqrt(np.sum(r1**2))
    e_vec2 = np.cross(v2, h2) / GM_SUN_AU3_DAY2 - r2 / np.sqrt(np.sum(r2**2))

    # Долгота перигелия (проекция на эклиптику)
    varpi1 = np.degrees(np.arctan2(e_vec1[1], e_vec1[0])) % 360
    varpi2 = np.degrees(np.arctan2(e_vec2[1], e_vec2[0])) % 360

    dvarpi = (varpi2 - varpi1 + 180) % 360 - 180
    rate_deg_per_day = dvarpi / dt_step
    rate_arcsec_per_century = rate_deg_per_day * 3600 * 36525

    return rate_arcsec_per_century, (e1 + e2) / 2

# ============================================================
# СБОР ДАННЫХ
# ============================================================
print("Сбор данных: 1980 лет, шаг 30 дней...")

start_dt = datetime(1010, 1, 1, 12, 0, 0)
step_days = 30
total_days = int(1980 * 365.25)
sample_days = np.arange(0, total_days, step_days)
years = sample_days / 365.25

data = {}
for name in ['Mercury', 'Mars']:
    print(f"  {name}...")
    e_arr = []
    prec_obs = []   # наблюдаемая скорость прецессии
    prec_a39 = []   # предсказание A391838
    prec_gr = []    # предсказание GR

    for d in sample_days:
        dt = start_dt + timedelta(days=int(d))
        a_osc, e_osc = osculating_elements(name, dt)
        e_arr.append(e_osc)

        rate_obs, e_avg = observed_varpi_rate(name, dt, dt_step=10)
        prec_obs.append(rate_obs)

        # Модельные скорости
        a = PLANETS[name]['a']
        prec_gr.append(K / (a**2.5 * (1 - e_osc**2)))
        prec_a39.append((K + L * (A391838_truncated(e_osc) - 1)) / a**2.5)

    data[name] = {
        'e': np.array(e_arr),
        'prec_obs': np.array(prec_obs),
        'prec_gr': np.array(prec_gr),
        'prec_a39': np.array(prec_a39),
    }

# ============================================================
# FFT
# ============================================================
def compute_spectrum(signal, step_days):
    """Возвращает (периоды_в_годах, амплитуды)."""
    n = len(signal)
    # Удаляем тренд
    signal_detrend = signal - np.polyval(np.polyfit(np.arange(n), signal, 1), np.arange(n))
    # Окно Хэннинга
    window = np.hanning(n)
    signal_windowed = signal_detrend * window
    # FFT
    fft = np.fft.rfft(signal_windowed)
    freqs = np.fft.rfftfreq(n, d=step_days)  # циклов/день
    periods_years = 1.0 / (freqs * 365.25)  # лет/цикл
    amplitudes = np.abs(fft) * 2 / n
    return periods_years, amplitudes

# ============================================================
# ИЗВЕСТНЫЕ ВЕКОВЫЕ ПЕРИОДЫ
# ============================================================
KNOWN_PERIODS = {
    'Mercury': [
        (5.0,   'Сарос (18 лет × n)'),
        (40.0,  'Меркурий-Венера'),
        (240.0, 'Меркурий e-цикл'),
        (500.0, 'Долгий цикл'),
        (883.0, 'Великое неравенство J-S'),
    ],
    'Mars': [
        (15.0,  'Марс-Земля'),
        (70.0,  'Марс e-короткий'),
        (175.0, 'Марс-Юпитер'),
        (883.0, 'Великое неравенство J-S'),
        (2000.0, 'Долгий цикл'),
    ],
}

# Делители Сварожьего Круга
DIVISORS = {
    'АХиневич': [16, 9, 9, 72, 760],
    'Реконструкция': [1, 2, 9, 72, 760],
    'A391838': [1, 1, 2, 9, 72, 760],
}

# ============================================================
# ГРАФИКИ
# ============================================================

# --- График 1: e(t) ---
fig1, axes1 = plt.subplots(2, 1, figsize=(18, 10))

for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes1[idx]
    ax.plot(years, data[name]['e'], 'b-', lw=0.5, alpha=0.7)
    ax.set_title(f'{name}: оскулирующий e(t)', fontweight='bold', fontsize=13)
    ax.set_xlabel('Годы от 1010 г.')
    ax.set_ylabel('e(t)')
    ax.grid(True, alpha=0.2)

    # Отметка среднего
    e_mean = np.mean(data[name]['e'])
    ax.axhline(e_mean, color='r', ls='--', lw=0.8, alpha=0.5,
               label=f'среднее e = {e_mean:.6f}')
    ax.legend(fontsize=9)

fig1.suptitle('Оскулирующий эксцентриситет (NASA DE422, 1010–2990)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('eccentricity_2000yr.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 2: спектр e(t) ---
fig2, axes2 = plt.subplots(2, 1, figsize=(18, 10))

for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes2[idx]
    periods, amps = compute_spectrum(data[name]['e'], step_days)

    # Ограничиваем периоды до 3000 лет (интересный диапазон)
    mask = (periods > 1) & (periods < 3000)
    ax.plot(periods[mask], amps[mask], 'b-', lw=0.8)
    ax.set_title(f'{name}: спектр e(t)', fontweight='bold', fontsize=13)
    ax.set_xlabel('Период (годы)')
    ax.set_ylabel('Амплитуда')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.2)

    # Отметка известных периодов
    for period, label in KNOWN_PERIODS[name]:
        ax.axvline(period, color='r', ls='--', lw=0.8, alpha=0.5)
        ax.text(period * 1.05, ax.get_ylim()[1] * 0.85, label,
                fontsize=7, color='r', rotation=90, va='top')

    # Отметка делителей (как периоды в годах)
    # Если базовый цикл ~16 лет, то делители дают:
    div_labels = [16, 16*9, 16*72, 16*2, 16*9*9]
    for d in div_labels:
        if 1 < d < 3000:
            ax.axvline(d, color='g', ls=':', lw=1.0, alpha=0.6)

    # Топ-5 пиков
    amps_masked = amps[mask]
    periods_masked = periods[mask]
    top_indices = np.argsort(amps_masked)[-5:][::-1]
    print(f"\n  {name} — топ-5 периодов e(t):")
    for i, ti in enumerate(top_indices):
        print(f"    {i+1}. {periods_masked[ti]:.1f} лет  "
              f"(амплитуда {amps_masked[ti]:.6f})")

fig2.suptitle('Спектр оскулирующего эксцентриситета (FFT)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('spectrum_e_2000yr.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 3: наблюдаемая прецессия vs модели ---
fig3, axes3 = plt.subplots(2, 1, figsize=(18, 10))

for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes3[idx]
    ax.plot(years, data[name]['prec_obs'], 'k-', lw=0.5, alpha=0.5,
            label='Наблюдение (DE422)')
    ax.plot(years, data[name]['prec_gr'], 'b-', lw=0.5, alpha=0.7,
            label='P_GR')
    ax.plot(years, data[name]['prec_a39'], 'r-', lw=0.5, alpha=0.7,
            label='P_A391838')
    ax.set_title(f'{name}: скорость прецессии (arcsec/век)',
                 fontweight='bold', fontsize=13)
    ax.set_xlabel('Годы от 1010 г.')
    ax.set_ylabel('arcsec/век')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

fig3.suptitle('Скорость прецессии: наблюдение vs модели',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('precession_rate_2000yr.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 4: спектр наблюдаемой прецессии ---
fig4, axes4 = plt.subplots(2, 1, figsize=(18, 10))

for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes4[idx]

    # Остаток: наблюдение − GR
    residual = data[name]['prec_obs'] - data[name]['prec_gr']
    periods, amps = compute_spectrum(residual, step_days)

    mask = (periods > 1) & (periods < 3000)
    ax.plot(periods[mask], amps[mask], 'b-', lw=0.8,
            label='Наблюдение − GR')

    # Остаток: наблюдение − A391838
    residual_a39 = data[name]['prec_obs'] - data[name]['prec_a39']
    _, amps_a39 = compute_spectrum(residual_a39, step_days)
    ax.plot(periods[mask], amps_a39[mask], 'r-', lw=0.8, alpha=0.7,
            label='Наблюдение − A391838')

    ax.set_title(f'{name}: спектр остатка прецессии',
                 fontweight='bold', fontsize=13)
    ax.set_xlabel('Период (годы)')
    ax.set_ylabel('Амплитуда')
    ax.set_xscale('log')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

    for period, label in KNOWN_PERIODS[name]:
        ax.axvline(period, color='gray', ls='--', lw=0.5, alpha=0.4)
        ax.text(period * 1.05, ax.get_ylim()[1] * 0.7, label,
                fontsize=7, color='gray', rotation=90, va='top')

    # Топ-5 пиков остатка (наблюдение − GR)
    amps_m = amps[mask]
    periods_m = periods[mask]
    top = np.argsort(amps_m)[-5:][::-1]
    print(f"\n  {name} — топ-5 периодов (набл. − GR):")
    for i, ti in enumerate(top):
        print(f"    {i+1}. {periods_m[ti]:.1f} лет  "
              f"(амплитуда {amps_m[ti]:.6f})")

fig4.suptitle('Спектр остатка прецессии (FFT)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('spectrum_residual_2000yr.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 5: корреляция A391838(e) с наблюдаемой прецессией ---
fig5, axes5 = plt.subplots(1, 2, figsize=(16, 7))

for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes5[idx]
    e = data[name]['e']
    obs = data[name]['prec_obs']
    gr = data[name]['prec_gr']
    a39 = data[name]['prec_a39']

    ax.scatter(e, obs, s=1, c='black', alpha=0.3, label='Наблюдение')
    e_sorted = np.sort(e)
    ax.plot(e_sorted, K / (PLANETS[name]['a']**2.5 * (1 - e_sorted**2)),
            'b-', lw=1.5, label='P_GR')
    ax.plot(e_sorted, (K + L * (A391838_truncated(e_sorted) - 1)) / PLANETS[name]['a']**2.5,
            'r-', lw=1.5, label='P_A391838')
    ax.set_title(f'{name}: прецессия vs e(t)', fontweight='bold')
    ax.set_xlabel('e(t)')
    ax.set_ylabel('arcsec/век')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

fig5.suptitle('Зависимость скорости прецессии от e(t)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('precession_vs_e.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# ВЫВОД: сравнение периодов с делителями
# ============================================================
print(f"\n{'='*80}")
print("Сравнение найденных периодов с делителями Сварожьего Круга")
print(f"{'='*80}")

print(f"\n  Делители:")
print(f"    АХиневич:       16, 9, 9, 72, 760")
print(f"    Реконструкция:   1, 2, 9, 72, 760")
print(f"    A391838:         1, 1, 2, 9, 72, 760")

print(f"\n  Если базовый цикл = 16 лет (1 сороковник):")
base = 16
for label, divs in DIVISORS.items():
    periods = [base * d for d in divs if base * d < 3000]
    print(f"    {label:15s}: {periods}")

print(f"\n  Если базовый цикл = 1 год:")
base = 1
for label, divs in DIVISORS.items():
    periods = [base * d for d in divs if base * d < 3000]
    print(f"    {label:15s}: {periods}")

print(f"\n  Графики сохранены:")
print("    eccentricity_2000yr.png")
print("    spectrum_e_2000yr.png")
print("    precession_rate_2000yr.png")
print("    spectrum_residual_2000yr.png")
print("    precession_vs_e.png")
