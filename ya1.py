"""
Сравнение трёх моделей прецессии с реальными эфемеридами.
Все исправления применены.

Модели:
  P0:       K / a^(5/2)                        — без e-поправки
  P_GR:     K / (a^(5/2) * (1-e^2))            — стандартная GR
  P_391838: (K + L*(A391838(e)-1)) / a^(5/2)   — A391838 (e.g.f.)
  P_391838_et: то же с реальным e(t) из эфемериды

Исправления:
  1. K_PGR удалён — стандартная GR
  2. График λ_model − λ_ephemeris
  3. Таблица вкладов коэффициентов A391838
  4. Модель A391838 с e(t)
  5. Правильное преобразование ν → E → M для M_0
  6. omega0 → varpi0 (долгота перигелия)

Требования: pip install ephem numpy matplotlib
"""

import ephem
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# ВХОДНЫЕ ДАННЫЕ
# ============================================================
INPUT_YEAR, INPUT_MONTH, INPUT_DAY, INPUT_HOUR = 2026, 9, 16, 1
NUM_DAYS = 81

# ============================================================
# ПЛАНЕТЫ (J2000)
# varpi0 — долгота перигелия (Ω + ω), в градусах
# ============================================================
PLANETS = {
    'Mercury': {'obj': ephem.Mercury(), 'period': 87.969,  'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456},
    'Venus':   {'obj': ephem.Venus(),   'period': 224.701, 'a': 0.723332, 'e': 0.006772, 'varpi0': 131.533},
    'Earth':   {'obj': ephem.Sun(),     'period': 365.256, 'a': 1.000000, 'e': 0.016709, 'varpi0': 102.937},
    'Mars':    {'obj': ephem.Mars(),    'period': 686.98,  'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040},
}

# ============================================================
# Уравнение центра (разложение до e^5)
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
# Преобразование истинной аномалии → эксцентрическая → средняя
# (исправление 5)
# ============================================================
def true_to_mean_anomaly(nu, e):
    """ν → E → M через уравнение Кеплера."""
    # ν → E
    E = 2 * np.arctan2(
        np.sqrt(1 - e) * np.sin(nu / 2),
        np.sqrt(1 + e) * np.cos(nu / 2)
    )
    E = E % (2 * np.pi)
    # E → M
    M = (E - e * np.sin(E)) % (2 * np.pi)
    return M

# ============================================================
# A391838 (нормализованные коэффициенты e.g.f.)
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]
A391838_LABELS = ['1', '1', '1', '3/2', '3', '19/3', '55/4', '31', '72']

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

# ============================================================
# Калибровка
# ============================================================
K = 3.8313
L = 0.6496

# ============================================================
# Четыре модели прецессии
# ============================================================
def precession_deg_per_day(model, a, e):
    if model == 'P0':
        prec = K / a**2.5
    elif model == 'P_GR':
        prec = K / (a**2.5 * (1 - e**2))
    elif model == 'P_391838':
        prec = (K + L * (A391838_truncated(e) - 1)) / a**2.5
    elif model == 'P_391838_et':
        prec = (K + L * (A391838_truncated(e) - 1)) / a**2.5
    return prec / 3600.0 / 36525.0  # arcsec/century → deg/day

# ============================================================
# Реальная гелиоцентрическая долгота
# ============================================================
def real_helio_long(name, dt):
    obj = PLANETS[name]['obj']
    obj.compute(dt)
    return np.degrees(float(obj.hlon)) % 360.0

# ============================================================
# Реальный эксцентриситет из эфемериды
# ============================================================
def real_eccentricity(name, dt):
    p = PLANETS[name]
    obj = p['obj']
    obj.compute(dt)
    a = p['a']
    varpi0 = np.radians(p['varpi0'])

    if name == 'Earth':
        r = float(obj.earth_distance)
    else:
        r = float(obj.sun_distance)

    hlon = np.radians(np.degrees(float(obj.hlon)) % 360.0)
    nu = (hlon - varpi0 + np.pi) % (2 * np.pi) - np.pi
    cos_nu = np.cos(nu)

    discriminant = (r * cos_nu) ** 2 + 4 * a * (a - r)
    if discriminant < 0:
        return p['e']
    e = (-r * cos_nu + np.sqrt(discriminant)) / (2 * a)
    return max(0.0, min(0.99, e))

# ============================================================
# Модельная долгота (с исправленным M_0)
# ============================================================
def compute_model_long(name, model, start_date, day):
    p = PLANETS[name]
    period = p['period']
    e = p['e']
    varpi0 = np.radians(p['varpi0'])
    n = 2 * np.pi / period

    # Для P_391838_et берём реальный e(t)
    if model == 'P_391838_et':
        dt = ephem.Date(start_date) + day
        e = real_eccentricity(name, dt)

    domega = precession_deg_per_day(model, p['a'], e)

    # --- Исправление 5: правильное M_0 через ν → E → M ---
    lon_0 = np.radians(real_helio_long(name, start_date))
    nu_0 = (lon_0 - varpi0 + np.pi) % (2 * np.pi) - np.pi
    M_0 = true_to_mean_anomaly(nu_0, e)

    M = M_0 + n * day
    varpi = varpi0 + np.radians(domega) * day
    lon = np.degrees(varpi + true_anomaly(M, e)) % 360.0
    return lon

# ============================================================
# Таблица вкладов коэффициентов A391838
# ============================================================
def print_contribution_table():
    print(f"\n{'='*80}")
    print("Вклады коэффициентов A391838 по планетам")
    print(f"{'='*80}")
    print(f"\nA(e) - 1 = сумма вкладов (поправка к K)\n")

    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        e = PLANETS[name]['e']
        print(f"\n  {name}  (e={e:.6f}):")
        print(f"    {'k':>3}  {'Коэфф':>8}  {'e^k':>14}  {'Вклад':>14}  {'Накопл.':>14}")
        print(f"    {'-'*3}  {'-'*8}  {'-'*14}  {'-'*14}  {'-'*14}")

        cumulative = 0.0
        for k in range(len(A391838_norm)):
            c = A391838_norm[k]
            ek = e**k
            contrib = c * ek
            cumulative += contrib
            print(f"    {k:>3}  {A391838_LABELS[k]:>8}  {ek:>14.6e}  "
                  f"{contrib:>14.6e}  {cumulative:>14.6e}")

        a_gr = 1.0 / (1 - e**2)
        print(f"\n    A(e)-1 (усечённый, 9 членов) = {cumulative - 1:.6f}")
        print(f"    1/(1-e^2)-1 (GR)             = {a_gr - 1:.6f}")
        print(f"    L*(A-1)                      = {L * (cumulative - 1):.6f}")
        print(f"    L*(1/(1-e^2)-1)              = {L * (a_gr - 1):.6f}")

# ============================================================
# РАСЧЁТ
# ============================================================
MODELS = ['P0', 'P_GR', 'P_391838', 'P_391838_et']
MODEL_LABELS = {
    'P0':          'P\u2080 (без e-поправки)',
    'P_GR':        'P_GR (1/(1\u2212e\u00b2))',
    'P_391838':    'P_A391838 (e\u2080)',
    'P_391838_et': 'P_A391838 (e(t))',
}

print_contribution_table()

start = ephem.Date((INPUT_YEAR, INPUT_MONTH, INPUT_DAY, INPUT_HOUR, 0, 0))
print(f"\n{'='*80}")
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
            rate = n_deg + prec_rate
            equivalent_phase_time_error = dlon / rate * 86400
            rows.append((day, equivalent_phase_time_error, dlon))
        results[name][model] = rows

# ============================================================
# ВЫВОД ТАБЛИЦЫ
# ============================================================
for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
    p = PLANETS[name]
    print(f"\n{'='*80}")
    print(f"{name}  (e={p['e']:.4f}, период={p['period']:.2f} дн)")
    print(f"  {'День':>4}  {'P0 \u0394\u0447':>8}  "
          f"{'GR \u0394\u0447':>8}  {'A39 \u0394\u0447':>8}  {'A39e \u0394\u0447':>8}  "
          f"{'P0 \u0394\u00b0':>8}  {'GR \u0394\u00b0':>8}  "
          f"{'A39 \u0394\u00b0':>8}  {'A39e \u0394\u00b0':>8}")
    print(f"  {'-'*4}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  "
          f"{'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")

    for day in [1] + list(range(10, NUM_DAYS + 1, 10)):
        idx = day - 1
        t0 = results[name]['P0'][idx][1] / 3600
        tg = results[name]['P_GR'][idx][1] / 3600
        ta = results[name]['P_391838'][idx][1] / 3600
        te = results[name]['P_391838_et'][idx][1] / 3600
        d0 = results[name]['P0'][idx][2]
        dg = results[name]['P_GR'][idx][2]
        da = results[name]['P_391838'][idx][2]
        de = results[name]['P_391838_et'][idx][2]
        print(f"  {day:>4}  {t0:8.2f}  {tg:8.2f}  {ta:8.2f}  {te:8.2f}  "
              f"{d0:8.4f}  {dg:8.4f}  {da:8.4f}  {de:8.4f}")

    for model in MODELS:
        rms = np.sqrt(np.mean([r[2]**2 for r in results[name][model]]))
        print(f"  RMS {MODEL_LABELS[model]:25s}: {rms:.4f}\u00b0")

print(f"\n{'='*80}")
print("\u0394\u0447 — эквивалентная фазовая ошибка (часы)")
print("\u0394\u00b0 — угловое расхождение (градусы)")
print("Положительное значение — модель опережает реальную планету")

# ============================================================
# ГРАФИК 1: λ_model − λ_ephemeris
# ============================================================
days_81 = np.arange(1, NUM_DAYS + 1)

fig1, axes1 = plt.subplots(2, 2, figsize=(16, 12))
colors_model = {
    'P0':          '#95a5a6',
    'P_GR':        '#3498db',
    'P_391838':    '#e74c3c',
    'P_391838_et': '#2ecc71',
}

for idx, name in enumerate(['Mercury', 'Venus', 'Earth', 'Mars']):
    ax = axes1[idx // 2][idx % 2]

    errors = {}
    for model in MODELS:
        err_list = []
        for day in days_81:
            lon_model = compute_model_long(name, model, start, day)
            lon_real = real_helio_long(name, ephem.Date(start) + day)
            d = (lon_model - lon_real + 180) % 360 - 180
            err_list.append(d)
        err = np.array(err_list, dtype=float)
        for i in range(1, len(err)):
            while err[i] - err[i-1] > 180: err[i] -= 360
            while err[i] - err[i-1] < -180: err[i] += 360
        err -= err[0]
        errors[model] = err * 3600

    for model in MODELS:
        ax.plot(days_81, errors[model],
                color=colors_model[model], lw=1.5,
                label=MODEL_LABELS[model], alpha=0.85)

    ax.axhline(0, color='black', lw=0.5, alpha=0.3)
    e_val = PLANETS[name]['e']
    ax.set_title(f'{name}  (e={e_val:.4f})', fontweight='bold')
    ax.set_xlabel('Дни от старта')
    ax.set_ylabel('\u03bb_model \u2212 \u03bb_ephemeris (arcsec)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.2)

fig1.suptitle(
    'Расхождение моделей с реальной эфемеридой\n'
    '(начальная подгонка удалена — \u0394\u03bb(t\u2080)=0)',
    fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('model_vs_ephemeris.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================================
# ГРАФИК 2: разница между моделями за 10 лет
# ============================================================
days_10yr = np.arange(1, 3653, 5)
start_10 = ephem.Date((2020, 1, 1, 0, 0, 0))

fig2, axes2 = plt.subplots(2, 2, figsize=(16, 12))

for idx, name in enumerate(['Mercury', 'Venus', 'Earth', 'Mars']):
    ax = axes2[idx // 2][idx % 2]
    e = PLANETS[name]['e']

    lons = {}
    for model in ['P0', 'P_GR', 'P_391838']:
        lons[model] = np.array([
            compute_model_long(name, model, start_10, day)
            for day in days_10yr])

    def unwrap_diff(a, b):
        d = a - b
        d = (d + 180) % 360 - 180
        for i in range(1, len(d)):
            while d[i] - d[i-1] > 180: d[i] -= 360
            while d[i] - d[i-1] < -180: d[i] += 360
        return d * 3600

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

fig2.suptitle(
    'Разница между моделями прецессии за 10 лет\n'
    '(возмущения сокращаются — видна чистая разница прецессии)',
    fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('model_differences_10yr.png', dpi=150, bbox_inches='tight')
plt.show()

