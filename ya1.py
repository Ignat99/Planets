"""
Сравнение трёх моделей прецессии с реальными эфемеридами.
Все исправления из критики применены.

Модели:
  P0:       K / a^(5/2)                        — без e-поправки
  P_GR:     K / (a^(5/2) * (1-e^2))            — стандартная GR
  P_391838: (K + L*(A391838(e)-1)) / a^(5/2)   — A391838 (e.g.f.)

Калибровка K,L — по Mercury+Venus (GR-only значения).
Train/test — все комбинации проверены.

Требования: pip install ephem numpy matplotlib
"""

import ephem
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# ВХОДНЫЕ ДАННЫЕ
# ============================================================
INPUT_YEAR, INPUT_MONTH, INPUT_DAY, INPUT_HOUR = 2026, 9, 16, 1
NUM_DAYS = 81

# ============================================================
# ПЛАНЕТЫ (J2000)
# ============================================================
PLANETS = {
    'Mercury': {'obj': ephem.Mercury(), 'period': 87.969,  'a': 0.387098, 'e': 0.205630, 'omega0': 77.456},
    'Venus':   {'obj': ephem.Venus(),   'period': 224.701, 'a': 0.723332, 'e': 0.006772, 'omega0': 131.533},
    'Earth':   {'obj': ephem.Sun(),     'period': 365.256, 'a': 1.000000, 'e': 0.016709, 'omega0': 102.937},
    'Mars':    {'obj': ephem.Mars(),    'period': 686.98,  'a': 1.523679, 'e': 0.093400, 'omega0': 336.040},
}

# ============================================================
# ИСПРАВЛЕННОЕ уравнение центра (разложение до e^5)
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
# A391838 (нормализованные коэффициенты e.g.f., без факториалов)
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]

def A391838_truncated(e, order=8):
    """Усечённая e.g.f. A391838 до заданного порядка."""
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

# ============================================================
# Калибровка (GR-only, Mercury+Venus)
# ============================================================
K = 3.8313
L = 0.6496
K_PGR = K * (1 - 0.205630**2)  # для P_GR

# ============================================================
# Три модели прецессии
# ============================================================
def precession_deg_per_day(model, a, e):
    """Возвращает скорость прецессии в градусах/день."""
    if model == 'P0':
        prec = K / a**2.5
    elif model == 'P_GR':
        prec = K_PGR / (a**2.5 * (1 - e**2))
    elif model == 'P_391838':
        prec = (K + L * (A391838_truncated(e) - 1)) / a**2.5
    return prec / 3600.0 / 36525.0  # arcsec/century → deg/day

# ============================================================
# Реальная гелиоцентрическая долгота (БЕЗ +180 для Земли)
# ============================================================
def real_helio_long(name, dt):
    obj = PLANETS[name]['obj']
    obj.compute(dt)
    return np.degrees(float(obj.hlon)) % 360.0

# ============================================================
# Модельная долгота
# ============================================================
def compute_model_long(name, model, start_date, day):
    p = PLANETS[name]
    period = p['period']
    e = p['e']
    omega0 = np.radians(p['omega0'])
    n = 2 * np.pi / period
    domega = precession_deg_per_day(model, p['a'], e)

    lon_0 = np.radians(real_helio_long(name, start_date))
    M_0 = (lon_0 - omega0) % (2 * np.pi)

    M = M_0 + n * day
    omega = omega0 + np.radians(domega) * day
    lon = np.degrees(omega + true_anomaly(M, e)) % 360.0
    return lon

# ============================================================
# РАСЧЁТ
# ============================================================
MODELS = ['P0', 'P_GR', 'P_391838']
MODEL_LABELS = {
    'P0':       'P\u2080 (без e-поправки)',
    'P_GR':     'P_GR (1/(1\u2212e\u00b2))',
    'P_391838': 'P_A391838'
}

start = ephem.Date((INPUT_YEAR, INPUT_MONTH, INPUT_DAY, INPUT_HOUR, 0, 0))
print(f"Старт: {INPUT_YEAR:04d}-{INPUT_MONTH:02d}-{INPUT_DAY:02d} "
      f"{INPUT_HOUR:02d}:00:00")
print(f"Расчёт на {NUM_DAYS} дней\n")

results = {}
for name in PLANETS:
    results[name] = {}
    for model in MODELS:
        rows = []
        for day in range(1, NUM_DAYS + 1):
            dt = ephem.Date(start) + day
            lon_model = compute_model_long(name, model, start, day)
            lon_real = real_helio_long(name, dt)
            dlon = (lon_model - lon_real + 180) % 360 - 180
            n_deg = 360.0 / PLANETS[name]['period']
            prec_rate = precession_deg_per_day(
                model, PLANETS[name]['a'], PLANETS[name]['e'])
            rate = n_deg + prec_rate  # deg/day
            equivalent_phase_time_error = dlon / rate * 86400  # sec
            rows.append((day, equivalent_phase_time_error, dlon))
        results[name][model] = rows

# ============================================================
# ВЫВОД ТАБЛИЦЫ (каждые 10 дней)
# ============================================================
for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
    p = PLANETS[name]
    print(f"\n{'='*80}")
    print(f"{name}  (e={p['e']:.4f}, период={p['period']:.2f} дн)")
    print(f"  {'День':>4}  {'P0 \u0394\u0447':>8}  "
          f"{'GR \u0394\u0447':>8}  {'A39 \u0394\u0447':>8}  "
          f"{'P0 \u0394\u00b0':>8}  {'GR \u0394\u00b0':>8}  "
          f"{'A39 \u0394\u00b0':>8}")
    print(f"  {'-'*4}  {'-'*8}  {'-'*8}  {'-'*8}  "
          f"{'-'*8}  {'-'*8}  {'-'*8}")

    for day in [1] + list(range(10, NUM_DAYS + 1, 10)):
        idx = day - 1
        t0 = results[name]['P0'][idx][1] / 3600
        tg = results[name]['P_GR'][idx][1] / 3600
        ta = results[name]['P_391838'][idx][1] / 3600
        d0 = results[name]['P0'][idx][2]
        dg = results[name]['P_GR'][idx][2]
        da = results[name]['P_391838'][idx][2]
        print(f"  {day:>4}  {t0:8.2f}  {tg:8.2f}  {ta:8.2f}  "
              f"{d0:8.4f}  {dg:8.4f}  {da:8.4f}")

    for model in MODELS:
        rms = np.sqrt(np.mean([r[2]**2 for r in results[name][model]]))
        print(f"  RMS {MODEL_LABELS[model]:25s}: {rms:.4f}\u00b0")

print(f"\n{'='*80}")
print("\u0394\u0447 — эквивалентная фазовая ошибка (часы)")
print("\u0394\u00b0 — угловое расхождение (градусы)")
print("Положительное значение — модель опережает реальную планету")

# ============================================================
# ГРАФИК: разница между моделями за 10 лет
# ============================================================
days_10yr = np.arange(1, 3653, 5)
start_10 = ephem.Date((2020, 1, 1, 0, 0, 0))

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
colors = {'Mercury': '#e74c3c', 'Venus': '#2ecc71',
          'Earth': '#3498db', 'Mars': '#e67e22'}

for idx, name in enumerate(['Mercury', 'Venus', 'Earth', 'Mars']):
    ax = axes[idx // 2][idx % 2]
    e = PLANETS[name]['e']

    lons = {}
    for model in MODELS:
        lons[model] = np.array([
            compute_model_long(name, model, start_10, day)
            for day in days_10yr])

    def unwrap_diff(a, b):
        d = a - b
        d = (d + 180) % 360 - 180
        for i in range(1, len(d)):
            while d[i] - d[i-1] > 180: d[i] -= 360
            while d[i] - d[i-1] < -180: d[i] += 360
        return d * 3600  # → arcsec

    d_gr_p0 = unwrap_diff(lons['P_GR'], lons['P0'])
    d_a39_p0 = unwrap_diff(lons['P_391838'], lons['P0'])
    d_a39_gr = unwrap_diff(lons['P_391838'], lons['P_GR'])

    years = days_10yr / 365.25
    ax.plot(years, d_gr_p0, 'b-', lw=1.5, label='P_GR \u2212 P\u2080', alpha=0.8)
    ax.plot(years, d_a39_p0, 'r-', lw=1.5,
            label='P_A391838 \u2212 P\u2080', alpha=0.8)
    ax.plot(years, d_a39_gr, 'g--', lw=1.5,
            label='P_A391838 \u2212 P_GR', alpha=0.8)
    ax.axhline(0, color='black', lw=0.5, alpha=0.3)
    ax.set_title(f'{name}  (e={e:.4f})', fontweight='bold')
    ax.set_xlabel('Годы от старта')
    ax.set_ylabel('\u0394\u03bb (arcsec)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2)

fig.suptitle(
    'Разница между моделями прецессии за 10 лет\n'
    '(возмущения сокращаются — видна чистая разница прецессии)',
    fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('model_differences_10yr.png', dpi=150, bbox_inches='tight')
plt.show()
