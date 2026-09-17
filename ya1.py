"""
Расхождение простой модели (Kepler + A391838 прецессия) с реальными эфемеридами.

Требования: pip install ephem numpy matplotlib

Вход: дата и час (минуты и секунды = 0).
Выход: для каждой планеты (Меркурий, Венера, Земля, Марс) —
       расхождение в днях, часах, минутах, секундах на каждый из 81 дней вперёд.
"""

import ephem
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# ВХОДНЫЕ ДАННЫЕ
# ============================================================

INPUT_YEAR  = 2026
INPUT_MONTH = 9
INPUT_DAY   = 16
INPUT_HOUR  = 1       # минуты и секунды = 0
NUM_DAYS    = 81

# ============================================================
# ПАРАМЕТРЫ ПЛАНЕТ
# ============================================================

PLANETS = {
    'Mercury': {'ephem_obj': ephem.Mercury(), 'period': 87.969,  'a': 0.387098, 'e': 0.205630},
    'Venus':   {'ephem_obj': ephem.Venus(),   'period': 224.701, 'a': 0.723332, 'e': 0.006772},
    'Earth':   {'ephem_obj': ephem.Sun(),     'period': 365.256, 'a': 1.000000, 'e': 0.016709},
    'Mars':    {'ephem_obj': ephem.Mars(),    'period': 686.98,  'a': 1.523679, 'e': 0.093400},
}

# ============================================================
# МОДЕЛЬ A391838 (нормализованные коэффициенты, без факториалов)
# ============================================================

A391838_norm = [1, 1, 1, 1.5, 3.0]   # 1/0!, 1/1!, 2/2!, 9/3!, 72/4!

def S4(e):
    return sum(c * e**k for k, c in enumerate(A391838_norm))

K_cal  = 3.83    # базовая прецессия
L_cal  = 0.66    # масштаб эксцентриситетной поправки
ALPHA  = 2.5     # степень полуоси (5/2 из GR)

def precession_arcsec_per_century(a, e):
    return (K_cal + L_cal * (S4(e) - 1)) / a**ALPHA

def precession_deg_per_day(a, e):
    return precession_arcsec_per_century(a, e) / 3600.0 / 36525.0

# ============================================================
# УРАВНЕНИЕ ЦЕНТРА (истинная аномалия из средней)
# ============================================================

def true_anomaly(M, e):
    nu = M
    nu += 2*e*np.sin(M)
    nu += (5/4)*e**2*np.sin(2*M)
    nu += (e**3/12)*(13*np.sin(3*M) - 3*np.sin(M))
    nu += (e**4/96)*(103*np.sin(4*M) - 24*np.sin(2*M))
    return nu % (2*np.pi)

# ============================================================
# РЕАЛЬНЫЕ ПОЗИЦИИ ИЗ ЭФЕМЕРИД
# ============================================================

def real_helio_long(planet_name, dt):
    p = PLANETS[planet_name]
    obj = p['ephem_obj']
    obj.compute(dt)
    if planet_name == 'Earth':
        return (np.degrees(float(obj.hlong)) + 180.0) % 360.0
    return np.degrees(float(obj.hlon)) % 360.0

def real_perihelion_long(planet_name):
    return {'Mercury': 77.456, 'Venus': 131.533, 'Earth': 102.937, 'Mars': 336.040}[planet_name]

# ============================================================
# ГЛАВНЫЙ РАСЧЁТ
# ============================================================

def calculate(start_date, num_days):
    results = {}
    for name, p in PLANETS.items():
        period  = p['period']
        a      = p['a']
        e      = p['e']
        lon_0  = real_helio_long(name, start_date)
        omega0 = np.radians(real_perihelion_long(name))
        M_0    = np.radians(lon_0 - real_perihelion_long(name)) % (2*np.pi)
        n      = 2*np.pi / period
        domega = np.radians(precession_deg_per_day(a, e))
        rate   = np.degrees(n) + precession_deg_per_day(a, e)

        rows = []
        for day in range(1, num_days + 1):
            dt = ephem.Date(start_date) + day
            M_model = M_0 + n * day
            omega_m = omega0 + domega * day
            lon_model = np.degrees(omega_m + true_anomaly(M_model, e)) % 360.0
            lon_real  = real_helio_long(name, dt)
            dlon = (lon_model - lon_real + 180) % 360 - 180
            t_days = dlon / rate
            rows.append((day, t_days * 86400, dlon))
        results[name] = rows
    return results

# ============================================================
# ВЫВОД ТАБЛИЦЫ
# ============================================================

def print_table(results):
    for name in ['Mercury', 'Venus', 'Earth', 'Mars']:
        data = results[name]
        p = PLANETS[name]
        print(f"\n{'='*80}")
        print(f"Планета: {name}")
        print(f"  Период: {p['period']:.3f} дней | e={p['e']:.6f} | "
              f"прецессия A391838: {precession_arcsec_per_century(p['a'], p['e']):.2f}\"/век")
        print(f"  {'День':>4}  {'Δдни':>8}  {'Δч':>4}  {'Δмин':>4}  {'Δсек':>6}  {'Δlon°':>8}")
        print(f"  {'-'*4}  {'-'*8}  {'-'*4}  {'-'*4}  {'-'*6}  {'-'*8}")
        for day, t_sec, dlon in data:
            sign = '+' if t_sec >= 0 else '-'
            t = abs(t_sec)
            d = int(t // 86400);  t %= 86400
            h = int(t // 3600);   t %= 3600
            m = int(t // 60);     s = t % 60
            print(f"  {day:>4}  {sign}{d:>7}  {h:>4}  {m:>4}  {s:>6.1f}  {dlon:>8.4f}")
    print(f"\n{'='*80}")
    print("'+' — модель опережает реальную планету | '−' — отстаёт")

# ============================================================
# ГРАФИКИ
# ============================================================

def plot_results(results):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    colors = {'Mercury': '#e74c3c', 'Venus': '#2ecc71', 'Earth': '#3498db', 'Mars': '#e67e22'}
    for idx, name in enumerate(['Mercury', 'Venus', 'Earth', 'Mars']):
        ax = axes[idx // 2][idx % 2]
        data = results[name]
        days = [d[0] for d in data]
        hours = [d[1] / 3600 for d in data]
        dlons = [d[2] for d in data]
        ax2 = ax.twinx()
        ax.plot(days, hours, color=colors[name], lw=2, label='Δ времени (ч)')
        ax2.plot(days, dlons, color='gray', lw=1.5, ls='--', alpha=0.7, label='Δlon (°)')
        e = PLANETS[name]['e']
        prec = precession_arcsec_per_century(PLANETS[name]['a'], e)
        ax.set_title(f'{name}  (e={e:.4f}, прецессия={prec:.1f}\"/век)', fontweight='bold')
        ax.set_xlabel('День'); ax.set_ylabel('Δ (часы)', color=colors[name])
        ax2.set_ylabel('Δlon (°)', color='gray')
        ax.axhline(0, color='black', lw=0.5, alpha=0.3)
        ax.grid(True, alpha=0.2)
        l1, la1 = ax.get_legend_handles_labels()
        l2, la2 = ax2.get_legend_handles_labels()
        ax.legend(l1 + l2, la1 + la2, fontsize=8)
    fig.suptitle('Модель (Kepler + A391838) vs реальные эфемериды', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('planet_discrepancies.png', dpi=150, bbox_inches='tight')
    plt.show()

# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == '__main__':
    start = ephem.Date(datetime(INPUT_YEAR, INPUT_MONTH, INPUT_DAY, INPUT_HOUR, 0, 0))
    print(f"Старт: {INPUT_YEAR:04d}-{INPUT_MONTH:02d}-{INPUT_DAY:02d} {INPUT_HOUR:02d}:00:00")
    print(f"Расчёт на {NUM_DAYS} дней вперёд\n")
    res = calculate(start, NUM_DAYS)
    print_table(res)
    plot_results(res)
