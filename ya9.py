"""
Спектральный анализ e(t) и прецессии — версия 2.
Усреднение по орбитальному периоду перед FFT.
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from skyfield.api import load

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

A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

K = 3.8313
L = 0.6496

# ============================================================
# ОСКУЛИРУЮЩИЕ ЭЛЕМЕНТЫ + ДОЛГОТА ПЕРИГЕЛИЯ
# ============================================================
def osculating_full(name, dt):
    """Возвращает (a_osc, e_osc, varpi_deg) — все из вектора эксцентриситета."""
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    sun_at = SUN.at(t)
    body_at = body.at(t)

    r_vec = np.array(body_at.position.au, float) - np.array(sun_at.position.au, float)
    v_vec = np.array(body_at.velocity.au_per_d, float) - np.array(sun_at.velocity.au_per_d, float)

    r = np.sqrt(np.sum(r_vec**2))
    v = np.sqrt(np.sum(v_vec**2))
    mu = GM_SUN_AU3_DAY2

    energy = 0.5 * v**2 - mu / r
    h_vec = np.cross(r_vec, v_vec)

    if energy >= 0:
        a_osc = PLANETS[name]['a']
    else:
        a_osc = -mu / (2 * energy)

    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r
    e_osc = np.sqrt(np.sum(e_vec**2))

    # Долгота перигелия — направление e_vec в эклиптической плоскости
    varpi_deg = np.degrees(np.arctan2(e_vec[1], e_vec[0])) % 360.0

    return a_osc, min(max(e_osc, 0.0), 0.99), varpi_deg

# ============================================================
# СБОР ДАННЫХ — частый шаг для усреднения
# ============================================================
print("Сбор данных: 1980 лет, шаг 5 дней...")

start_dt = datetime(1010, 1, 1, 12, 0, 0)
step_raw = 5           # дней между точками
total_days = int(1980 * 365.25)
sample_raw = np.arange(0, total_days, step_raw)

# Окно сглаживания: ~2 орбитальных периода
WINDOWS = {
    'Mercury': int(2 * 87.969 / step_raw),   # ~35 точек = 175 дней
    'Mars':    int(2 * 686.98 / step_raw),    # ~275 точек = 1375 дней
}

data = {}
for name in ['Mercury', 'Mars']:
    print(f"  {name}...")
    e_raw = []
    varpi_raw = []
    a = PLANETS[name]['a']

    for d in sample_raw:
        dt = start_dt + timedelta(days=int(d))
        _, e_osc, varpi = osculating_full(name, dt)
        e_raw.append(e_osc)
        varpi_raw.append(varpi)

    e_raw = np.array(e_raw)
    varpi_raw = np.array(varpi_raw)

    # Сглаживание скользящим средним
    win = WINDOWS[name]
    kernel = np.ones(win) / win
    e_smooth = np.convolve(e_raw, kernel, mode='valid')

    # Для долготы перигелия:unwrap + сглаживание + производная
    varpi_unwrapped = np.copy(varpi_raw)
    for i in range(1, len(varpi_unwrapped)):
        while varpi_unwrapped[i] - varpi_unwrapped[i-1] > 180:
            varpi_unwrapped[i] -= 360
        while varpi_unwrapped[i] - varpi_unwrapped[i-1] < -180:
            varpi_unwrapped[i] += 360
    varpi_smooth = np.convolve(varpi_unwrapped, kernel, mode='valid')

    # Производная: dϖ/dt через центральную разность
    # Шаг в годах
    step_years = step_raw / 365.25
    n_smooth = len(varpi_smooth)
    prec_obs = np.gradient(varpi_smooth, step_years)  # град/год
    prec_obs = prec_obs * 3600  # → arcsec/год
    # Но прецессия — это dϖ/dt, а не град/год полной долготы
    # Нужна скорость относительно равномерного движения
    # Проще: prec_obs уже = d(ϖ)/dt в arcsec/год

    # Модельные скорости со сглаженным e
    prec_gr = K / (a**2.5 * (1 - e_smooth**2))
    prec_a39 = (K + L * (A391838_truncated(e_smooth) - 1)) / a**2.5

    # Время для сглаженных рядов (коррекция на convolve 'valid')
    years_smooth = (sample_raw[:len(e_smooth)] + win * step_raw / 2) / 365.25

    data[name] = {
        'e': e_smooth,
        'prec_obs': prec_obs,
        'prec_gr': prec_gr,
        'prec_a39': prec_a39,
        'years': years_smooth,
    }

# ============================================================
# FFT (с защитой от деления на ноль)
# ============================================================
def compute_spectrum(signal, step_days):
    n = len(signal)
    signal_detrend = signal - np.polyval(np.polyfit(np.arange(n), signal, 3), np.arange(n))
    window = np.hanning(n)
    signal_windowed = signal_detrend * window
    fft = np.fft.rfft(signal_windowed)
    freqs = np.fft.rfftfreq(n, d=step_days)
    # Защита от freqs=0
    periods_years = np.where(freqs > 0, 1.0 / (freqs * 365.25), np.inf)
    amplitudes = np.abs(fft) * 2 / n
    return periods_years, amplitudes

# ============================================================
# ИЗВЕСТНЫЕ ПЕРИОДЫ
# ============================================================
KNOWN_PERIODS = {
    'Mercury': [
        (240.0, 'Mercury e-цикл'),
        (500.0, 'Долгий цикл'),
        (883.0, 'Великое неравенство J-S'),
        (1200.0, 'Очень долгий'),
    ],
    'Mars': [
        (125.0, 'Марс e-короткий'),
        (175.0, 'Марс-Юпитер'),
        (883.0, 'Великое неравенство J-S'),
        (1200.0, 'Очень долгий'),
    ],
}

# Делители × базовый цикл
DIVISOR_PERIODS = {
    16: '16 лет',
    32: '16×2',
    144: '16×9',
    256: '16×16',
    1152: '16×72',
    760: '760',
    9: '9',
    72: '72',
}

# ============================================================
# ГРАФИКИ
# ============================================================

# --- График 1: e(t) сглаженный ---
fig1, axes1 = plt.subplots(2, 1, figsize=(18, 10))
for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes1[idx]
    ax.plot(data[name]['years'], data[name]['e'], 'b-', lw=0.5, alpha=0.7)
    e_mean = np.mean(data[name]['e'])
    ax.axhline(e_mean, color='r', ls='--', lw=0.8, alpha=0.5,
               label=f'среднее e = {e_mean:.6f}')
    ax.set_title(f'{name}: оскулирующий e(t), сглаженный по ~2 периода',
                 fontweight='bold', fontsize=13)
    ax.set_xlabel('Годы от 1010 г.')
    ax.set_ylabel('e(t)')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

fig1.suptitle('Сглаженный эксцентриситет (NASA DE422, 1010–2990)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('eccentricity_smoothed.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 2: спектр e(t) ---
fig2, axes2 = plt.subplots(2, 1, figsize=(18, 10))
for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes2[idx]
    periods, amps = compute_spectrum(data[name]['e'], step_raw)

    mask = (periods > 10) & (periods < 5000)
    ax.plot(periods[mask], amps[mask], 'b-', lw=0.8)
    ax.set_title(f'{name}: спектр e(t) после сглаживания',
                 fontweight='bold', fontsize=13)
    ax.set_xlabel('Период (годы)')
    ax.set_ylabel('Амплитуда')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.2)

    # Известные периоды
    for period, label in KNOWN_PERIODS[name]:
        ax.axvline(period, color='r', ls='--', lw=0.8, alpha=0.5)
        ax.text(period * 1.03, ax.get_ylim()[1] * 0.85, label,
                fontsize=7, color='r', rotation=90, va='top')

    # Делители Сварожьего Круга
    for p, lbl in DIVISOR_PERIODS.items():
        if 10 < p < 5000:
            ax.axvline(p, color='g', ls=':', lw=0.8, alpha=0.5)

    # Топ-10 пиков
    amps_m = amps[mask]
    periods_m = periods[mask]
    top = np.argsort(amps_m)[-10:][::-1]
    print(f"\n  {name} — топ-10 периодов e(t):")
    for i, ti in enumerate(top):
        print(f"    {i+1:2d}. {periods_m[ti]:8.1f} лет  "
              f"(амплитуда {amps_m[ti]:.8f})")

fig2.suptitle('Спектр эксцентриситета (FFT, сглаженный)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('spectrum_e_smoothed.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 3: наблюдаемая прецессия vs модели ---
fig3, axes3 = plt.subplots(2, 1, figsize=(18, 10))
for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes3[idx]
    yrs = data[name]['years']
    ax.plot(yrs, data[name]['prec_obs'], 'k-', lw=0.4, alpha=0.4,
            label='Наблюдение (dϖ/dt)')
    ax.plot(yrs, data[name]['prec_gr'], 'b-', lw=0.8, alpha=0.7,
            label='P_GR')
    ax.plot(yrs, data[name]['prec_a39'], 'r-', lw=0.8, alpha=0.7,
            label='P_A391838')
    ax.set_title(f'{name}: скорость прецессии (arcsec/год)',
                 fontweight='bold', fontsize=13)
    ax.set_xlabel('Годы от 1010 г.')
    ax.set_ylabel('arcsec/год')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

fig3.suptitle('Скорость прецессии: наблюдение vs модели',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('precession_rate_smoothed.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 4: спектр остатка прецессии ---
fig4, axes4 = plt.subplots(2, 1, figsize=(18, 10))
for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes4[idx]

    residual_gr = data[name]['prec_obs'] - data[name]['prec_gr']
    residual_a39 = data[name]['prec_obs'] - data[name]['prec_a39']

    periods, amps_gr = compute_spectrum(residual_gr, step_raw)
    _, amps_a39 = compute_spectrum(residual_a39, step_raw)

    mask = (periods > 10) & (periods < 5000)
    ax.plot(periods[mask], amps_gr[mask], 'b-', lw=0.8,
            label='Наблюдение − GR')
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
        ax.text(period * 1.03, ax.get_ylim()[1] * 0.7, label,
                fontsize=7, color='gray', rotation=90, va='top')

    for p, lbl in DIVISOR_PERIODS.items():
        if 10 < p < 5000:
            ax.axvline(p, color='g', ls=':', lw=0.8, alpha=0.4)

    # Топ-10 пиков остатка (набл − GR)
    amps_m = amps_gr[mask]
    periods_m = periods[mask]
    top = np.argsort(amps_m)[-10:][::-1]
    print(f"\n  {name} — топ-10 периодов (набл. − GR):")
    for i, ti in enumerate(top):
        print(f"    {i+1:2d}. {periods_m[ti]:8.1f} лет  "
              f"(амплитуда {amps_m[ti]:.4f})")

    # Топ-10 пиков остатка (набл − A391838)
    amps_a = amps_a39[mask]
    top_a = np.argsort(amps_a)[-10:][::-1]
    print(f"\n  {name} — топ-10 периодов (набл. − A391838):")
    for i, ti in enumerate(top_a):
        print(f"    {i+1:2d}. {periods_m[ti]:8.1f} лет  "
              f"(амплитуда {amps_a[ti]:.4f})")

fig4.suptitle('Спектр остатка прецессии (FFT, сглаженный)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('spectrum_residual_smoothed.png', dpi=150, bbox_inches='tight')
plt.show()

# --- График 5: прецессия vs e ---
fig5, axes5 = plt.subplots(1, 2, figsize=(16, 7))
for idx, name in enumerate(['Mercury', 'Mars']):
    ax = axes5[idx]
    e = data[name]['e']
    obs = data[name]['prec_obs']
    a = PLANETS[name]['a']

    ax.scatter(e, obs, s=1, c='black', alpha=0.2, label='Наблюдение')
    e_sorted = np.sort(e)
    ax.plot(e_sorted, K / (a**2.5 * (1 - e_sorted**2)),
            'b-', lw=1.5, label='P_GR')
    ax.plot(e_sorted, (K + L * (A391838_truncated(e_sorted) - 1)) / a**2.5,
            'r-', lw=1.5, label='P_A391838')
    ax.set_title(f'{name}: прецессия vs e(t)', fontweight='bold')
    ax.set_xlabel('e(t)')
    ax.set_ylabel('arcsec/год')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2)

fig5.suptitle('Зависимость скорости прецессии от e(t)',
              fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('precession_vs_e_smoothed.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# ИТОГ
# ============================================================
print(f"\n{'='*80}")
print("Графики сохранены:")
print("  eccentricity_smoothed.png")
print("  spectrum_e_smoothed.png")
print("  precession_rate_smoothed.png")
print("  spectrum_residual_smoothed.png")
print("  precession_vs_e_smoothed.png")
print(f"{'='*80}")
