#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convergence_test.py — Тест сходимости для ревизии 5.

Проверяет устойчивость секулярной скорости прецессии и RMS долготы
при шагах интегрирования: 60, 30, 15, 7.5 дней.

Не меняет формулы. Только меняет шаг сетки.
"""

import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from skyfield.api import load
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================
# Генератор A391838 из беззнаковых чисел Стирлинга I рода
# ============================================================

def stirling1_triangle(N):
    """Треугольник беззнаковых чисел Стирлинга первого рода s(n,k)."""
    s = [[0] * (N + 1) for _ in range(N + 1)]
    s[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            s[n][k] = s[n-1][k-1] + (n-1) * s[n-1][k]
    return s

def compute_a391838_from_stirling(N_terms=9):
    """
    Вычисляет a(n) = (n!)^2 * Sum_{k=0..floor(n/2)} |Stirling1(n-k, n-2k)| / ((2k+1)! * (n-k)!)
    Строго по формуле OEIS A391838.
    """
    s = stirling1_triangle(2 * N_terms + 2)
    from math import factorial
    
    a = []
    for n in range(N_terms):
        total = 0
        for k in range(n // 2 + 1):
            row = n - k
            col = n - 2 * k
            if col < 0 or col > row:
                continue
            stirling_val = abs(s[row][col]) if row < len(s) and col < len(s[row]) else 0
            denom = factorial(2 * k + 1) * factorial(n - k)
            total += stirling_val / denom
        a_n = (factorial(n) ** 2) * total
        a.append(round(a_n))
    
    # Нормировка
    norm = [a[n] / factorial(n) for n in range(N_terms)]
    return a, norm

# ============================================================
# Вычисление
# ============================================================

print("=" * 80)
print("Генератор A391838 из беззнаковых чисел Стирлинга первого рода")
print("=" * 80)
print("  Формула: a(n) = (n!)^2 * Sum |Stirling1(n-k, n-2k)| / ((2k+1)! * (n-k)!)")

a_int, A391838_norm = compute_a391838_from_stirling(9)
print(f"  Целочисленная последовательность: {a_int}")
print(f"  Нормированные коэффициенты a_n/n!: {A391838_norm}")

oeis_ref = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
match = all(abs(a_int[i] - oeis_ref[i]) < 0.5 for i in range(len(oeis_ref)))
print(f"  Сравнение с OEIS: {', '.join(str(x) for x in oeis_ref)}")
print(f"  Все 9 членов совпадают: {'ДА' if match else 'НЕТ'}")
print()

# ============================================================
# Загрузка эфемериды
# ============================================================

print("Загрузка эфемериды DE422...")
eph_file = load('de422.bsp')

# Используем целочисленные индексы, а не строковые!
SUN = eph_file[0]
MERCURY = eph_file[1]
VENUS = eph_file[2]
EMB = eph_file[3]       # EMB, не геоцентр!
MARS = eph_file[4]
JUPITER = eph_file[5]
SATURN = eph_file[6]

ts = load.timescale()

# ============================================================
# Параметры моделей (из ya15.py rev5)
# ============================================================

# Константы
GM_sun = 1.32712440018e20  # m^3/s^2
AU = 1.495978707e11         # m
c = 2.99792458e8            # m/s

def A391838_func(e):
    """Полином A391838(e) = sum_{n=0}^{8} (a_n/n!) * e^n"""
    return sum(A391838_norm[n] * e**n for n in range(len(A391838_norm)))

def gr_factor(e):
    """Стандартный GR множитель 1/(1-e^2)"""
    return 1.0 / (1.0 - e**2)

# Планетарные параметры (J2000, из ya15.py)
BODIES = {
    'Mercury': {
        'planet': MERCURY,
        'a0': 0.38709738,
        'e0': 0.20563890,
        'varpi0': 77.3164,     # градусы
        'K': 41.0955,          # arcsec/century (ньютоновская прецессия)
        'L': 0.6496,
        'newtonian_pub': 532.3035,  # опубл. ньютоновское (arcsec/century)
    },
    'Mars': {
        'planet': MARS,
        'a0': 1.52371243,
        'e0': 0.09339410,
        'varpi0': 336.0402,
        'K': 1.3369,
        'L': 0.6496,
        'newtonian_pub': 1598.2000,  # ориентировочное
    },
}

# ============================================================
# Функции
# ============================================================

def helio_position(planet, t):
    """Гелиоцентрические координаты (геометрический режим)."""
    r = planet.at(t)
    x, y, z = r.position.au
    vx, vy, vz = r.velocity.au_per_d
    return np.array([x, y, z]), np.array([vx, vy, vz])

def osculating_full(r_vec, v_vec, GM=GM_sun, AU=AU, day=86400.0):
    """
    Полные оскулирующие элементы из state vector.
    DE422, Sun-only. Это НЕ канонические элементы VSOP87.
    """
    # Перевод в SI
    r_si = r_vec * AU
    v_si = v_vec * AU / day
    mu = GM
    
    r_mag = np.linalg.norm(r_si)
    v_mag = np.linalg.norm(v_si)
    
    # Удельная энергия
    energy = v_mag**2 / 2 - mu / r_mag
    a = -mu / (2 * energy)
    
    # Момент импульса
    h_vec = np.cross(r_si, v_si)
    h_mag = np.linalg.norm(h_vec)
    
    # Вектор Лапласа-Рунге-Ленца
    e_vec = np.cross(v_si, h_vec) / mu - r_si / r_mag
    e = np.linalg.norm(e_vec)
    
    # Наклонение
    i_inc = np.arccos(h_vec[2] / h_mag)
    
    # Долгота восходящего узла
    Omega = np.arctan2(h_vec[0], -h_vec[1])
    if Omega < 0:
        Omega += 2 * np.pi
    
    # Аргумент перицентра
    n_vec = np.array([0, 0, 1])
    N_vec = np.cross(n_vec, h_vec)
    N_mag = np.linalg.norm(N_vec)
    if N_mag > 1e-15:
        omega = np.arccos(np.clip(np.dot(N_vec, e_vec) / (N_mag * e), -1, 1))
        if e_vec[2] < 0:
            omega = 2 * np.pi - omega
    else:
        omega = 0
    
    # Истинная аномалия
    nu = np.arccos(np.clip(np.dot(e_vec, r_si) / (e * r_mag), -1, 1))
    if np.dot(r_si, v_si) < 0:
        nu = 2 * np.pi - nu
    
    # Эксцентрическая аномалия
    E = 2 * np.arctan(np.sqrt((1 - e) / (1 + e)) * np.tan(nu / 2))
    
    # Средняя аномалия
    M = E - e * np.sin(E)
    
    # Проекционная долгота перицентра (на J2000 ecliptic)
    varpi = np.degrees(Omega + omega)
    varpi = varpi % 360
    
    M_deg = np.degrees(M) % 360
    
    return {
        'a': a / AU,
        'e': e,
        'i': np.degrees(i_inc),
        'Omega': np.degrees(Omega),
        'omega': np.degrees(omega),
        'varpi': varpi,
        'M': M_deg,
        'nu': np.degrees(nu),
    }

def compute_model_long_array(body_name, dt_days, years=1980):
    """
    Вычисляет долготу планеты для набора моделей на интервале years лет.
    Шаг dt_days дней.
    """
    body = BODIES[body_name]
    planet = body['planet']
    a0 = body['a0']
    e0 = body['e0']
    varpi0 = body['varpi0']
    K = body['K']
    L = body['L']
    
    start_year = 1010
    end_year = start_year + years
    
    N = int(years * 365.25 / dt_days)
    times = [start_year + (i * dt_days) / 365.25 for i in range(N + 1)]
    
    # Разбиваем на блоки для Skyfield
    block_size = 2000
    longitudes_de422 = []
    varpi_de422 = []
    a_osc_list = []
    e_osc_list = []
    
    for blk_start in range(0, len(times), block_size):
        blk_end = min(blk_start + block_size, len(times))
        blk_times = times[blk_start:blk_end]
        
        # Skyfield время
        t = ts.utc([int(y) for y in blk_times],
                   [int((y % 1) * 12) + 1 for y in blk_times],
                   [1 for _ in blk_times])
        
        for idx in range(len(blk_times)):
            # Одна точка
            t_one = ts.utc(int(blk_times[idx]),
                          int((blk_times[idx] % 1) * 12) + 1, 1)
            r_vec, v_vec = helio_position(planet, t_one)
            osc = osculating_full(r_vec, v_vec)
            
            lam = np.degrees(np.arctan2(r_vec[1], r_vec[0])) % 360
            longitudes_de422.append(lam)
            varpi_de422.append(osc['varpi'])
            a_osc_list.append(osc['a'])
            e_osc_list.append(osc['e'])
    
    longitudes_de422 = np.array(longitudes_de422)
    varpi_de422 = np.array(varpi_de422)
    a_osc = np.array(a_osc_list)
    e_osc = np.array(e_osc_list)
    
    # Модели
    # P0: без e-поправки
    # P_GR: 1/(1-e^2)
    # P_391838: A391838(e) с постоянными a0, e0
    # P_A391838_hybrid: A391838 с оскулирующими a(t), e(t)
    
    t_years = np.array(times[:len(longitudes_de422)])
    
    # Скорости прецессии (arcsec/century)
    dvarpi_P0 = K / a0**2.5
    dvarpi_PGR = (K + L * (gr_factor(e0) - 1)) / a0**2.5
    dvarpi_P391838 = (K + L * (A391838_func(e0) - 1)) / a0**2.5
    
    # Гибрид: переменная скорость
    A_vals = np.array([A391838_func(e) for e in e_osc])
    dvarpi_hybrid = (K + L * (A_vals - 1)) / a_osc**2.5
    
    # Интегрирование (кумулятивная трапеция)
    dt_century = dt_days / 36525.0
    
    # P0
    varpi_P0 = np.cumsum(dvarpi_P0 * dt_century * np.ones(len(t_years)))
    varpi_P0 = varpi0 + varpi_P0 / 3600.0  # arcsec -> degrees
    
    # P_GR
    varpi_PGR = np.cumsum(dvarpi_PGR * dt_century * np.ones(len(t_years)))
    varpi_PGR = varpi0 + varpi_PGR / 3600.0
    
    # P_391838
    varpi_P391838 = np.cumsum(dvarpi_P391838 * dt_century * np.ones(len(t_years)))
    varpi_P391838 = varpi0 + varpi_P391838 / 3600.0
    
    # P_A391838_hybrid (трапеция)
    varpi_hybrid = np.zeros(len(t_years))
    varpi_hybrid[0] = varpi0
    for j in range(1, len(t_years)):
        avg = (dvarpi_hybrid[j] + dvarpi_hybrid[j-1]) / 2
        varpi_hybrid[j] = varpi_hybrid[j-1] + avg * dt_century / 3600.0
    
    # Долгота модели = долгота DE422 + (varpi_model - varpi_de422)
    # Но правильнее: long_model = long_de422 + (varpi_model - varpi_de422_corrections)
    # Используем простой подход: угол между моделью и DE422
    
    # Разность долгот
    def angle_diff(a, b):
        d = (a - b) % 360
        d = np.where(d > 180, d - 360, d)
        return d
    
    diff_P0 = angle_diff(varpi_P0, varpi_de422)
    diff_PGR = angle_diff(varpi_PGR, varpi_de422)
    diff_P391838 = angle_diff(varpi_P391838, varpi_de422)
    diff_hybrid = angle_diff(varpi_hybrid, varpi_de422)
    
    # RMS
    rms_P0 = np.sqrt(np.mean(diff_P0**2))
    rms_PGR = np.sqrt(np.mean(diff_PGR**2))
    rms_P391838 = np.sqrt(np.mean(diff_P391838**2))
    rms_hybrid = np.sqrt(np.mean(diff_hybrid**2))
    
    # Секулярная скорость dvarpi/dt (через линейную регрессию)
    t_centuries = (t_years - t_years[0]) / 100.0
    
    # DE422 мгновенная скорость (через разность varpi)
    dvarpi_de422_inst = np.diff(varpi_de422)
    # unwrap
    dvarpi_de422_unwrapped = np.unwrap(np.radians(varpi_de422))
    slope_de422 = np.polyfit(t_centuries, np.degrees(dvarpi_de422_unwrapped), 1)[0]
    
    # Центральный интервал (10-90%)
    n_total = len(t_centuries)
    i_lo = int(0.1 * n_total)
    i_hi = int(0.9 * n_total)
    slope_de422_center = np.polyfit(t_centuries[i_lo:i_hi], 
                                     np.degrees(dvarpi_de422_unwrapped[i_lo:i_hi]), 1)[0]
    
    # Сглаженная
    window = max(1, n_total // 20)
    varpi_smooth = np.convolve(np.degrees(dvarpi_de422_unwrapped), 
                                np.ones(window)/window, mode='valid')
    t_smooth = t_centuries[window//2:window//2 + len(varpi_smooth)]
    slope_de422_smooth = np.polyfit(t_smooth, varpi_smooth, 1)[0]
    
    return {
        'dt_days': dt_days,
        'body': body_name,
        'secular_de422': slope_de422,
        'secular_de422_center': slope_de422_center,
        'secular_de422_smooth': slope_de422_smooth,
        'newtonian': body['newtonian_pub'],
        'residual': slope_de422 - body['newtonian_pub'],
        'residual_center': slope_de422_center - body['newtonian_pub'],
        'residual_smooth': slope_de422_smooth - body['newtonian_pub'],
        'P0': dvarpi_P0,
        'P_GR': dvarpi_PGR,
        'P_391838': dvarpi_P391838,
        'P_hybrid': np.mean(dvarpi_hybrid),
        'rms_P0': rms_P0,
        'rms_PGR': rms_PGR,
        'rms_P391838': rms_P391838,
        'rms_hybrid': rms_hybrid,
        'N_points': len(t_years),
    }

# ============================================================
# Главная функция
# ============================================================

def main():
    dt_list = [60, 30, 15, 7.5]
    body_list = ['Mercury', 'Mars']
    
    results = {}
    for body_name in body_list:
        results[body_name] = {}
        print(f"\n{'=' * 80}")
        print(f"Тест сходимости: {body_name}")
        print(f"{'=' * 80}")
        
        for dt in dt_list:
            print(f"\n  Шаг {dt} дней...")
            res = compute_model_long_array(body_name, dt)
            results[body_name][dt] = res
            
            print(f"    N точек:        {res['N_points']}")
            print(f"    DE422 секуляр:   {res['secular_de422']:.4f} arcsec/век")
            print(f"    DE422 централ.:  {res['secular_de422_center']:.4f} arcsec/век")
            print(f"    DE422 сглаж.:    {res['secular_de422_smooth']:.4f} arcsec/век")
            print(f"    Newtonian:       {res['newtonian']:.4f} arcsec/век")
            print(f"    Остаток:         {res['residual']:.4f} arcsec/век")
            print(f"    Остаток центр.:  {res['residual_center']:.4f} arcsec/век")
            print(f"    Остаток сглаж.:  {res['residual_smooth']:.4f} arcsec/век")
            print(f"    P0:             {res['P0']:.4f} arcsec/век")
            print(f"    P_GR:           {res['P_GR']:.4f} arcsec/век")
            print(f"    P_391838:       {res['P_391838']:.4f} arcsec/век")
            print(f"    P_hybrid:       {res['P_hybrid']:.4f} arcsec/век")
            print(f"    RMS P0:         {res['rms_P0']:.6f}°")
            print(f"    RMS P_GR:       {res['rms_PGR']:.6f}°")
            print(f"    RMS P_391838:   {res['rms_P391838']:.6f}°")
            print(f"    RMS hybrid:     {res['rms_hybrid']:.6f}°")
    
    # Сводная таблица
    print(f"\n{'=' * 80}")
    print("СВОДНАЯ ТАБЛИЦА СХОДИМОСТИ")
    print(f"{'=' * 80}")
    
    for body_name in body_list:
        print(f"\n  {body_name}:")
        print(f"  {'Шаг':>8s}  {'Секулярная':>12s}  {'Центр.':>12s}  {'Сглаж.':>12s}  {'Остаток':>10s}  {'RMS P0':>10s}  {'RMS GR':>10s}  {'RMS A39':>10s}  {'RMS гибр.':>10s}")
        print(f"  {'-'*8}  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*10}")
        for dt in dt_list:
            r = results[body_name][dt]
            print(f"  {dt:8.1f}  {r['secular_de422']:12.4f}  {r['secular_de422_center']:12.4f}  {r['secular_de422_smooth']:12.4f}  {r['residual']:10.4f}  {r['rms_P0']:10.6f}  {r['rms_PGR']:10.6f}  {r['rms_P391838']:10.6f}  {r['rms_hybrid']:10.6f}")
    
    # Анализ сходимости
    print(f"\n{'=' * 80}")
    print("АНАЛИЗ СХОДИМОСТИ")
    print(f"{'=' * 80}")
    
    for body_name in body_list:
        print(f"\n  {body_name}:")
        dts = dt_list
        sec = [results[body_name][dt]['secular_de422'] for dt in dts]
        res = [results[body_name][dt]['residual'] for dt in dts]
        rms0 = [results[body_name][dt]['rms_P0'] for dt in dts]
        rmsgr = [results[body_name][dt]['rms_PGR'] for dt in dts]
        rms39 = [results[body_name][dt]['rms_P391838'] for dt in dts]
        rmsh = [results[body_name][dt]['rms_hybrid'] for dt in dts]
        
        # Изменение при переходе 60 -> 30, 30 -> 15, 15 -> 7.5
        for i in range(len(dts) - 1):
            d_sec = sec[i+1] - sec[i]
            d_res = res[i+1] - res[i]
            d_rms0 = rms0[i+1] - rms0[i]
            d_rmsgr = rmsgr[i+1] - rmsgr[i]
            d_rms39 = rms39[i+1] - rms39[i]
            d_rmsh = rmsh[i+1] - rmsh[i]
            
            print(f"    {dts[i]:.1f} -> {dts[i+1]:.1f} дней:")
            print(f"      Δ секулярная:  {d_sec:+.6f} arcsec/век")
            print(f"      Δ остаток:     {d_res:+.6f} arcsec/век")
            print(f"      Δ RMS P0:     {d_rms0:+.6f}°")
            print(f"      Δ RMS GR:     {d_rmsgr:+.6f}°")
            print(f"      Δ RMS A391838:{d_rms39:+.6f}°")
            print(f"      Δ RMS гибрид:  {d_rmsh:+.6f}°")
        
        # Относительное изменение 30 -> 7.5
        if len(dts) >= 3:
            idx_30 = dts.index(30) if 30 in dts else 1
            idx_75 = dts.index(7.5) if 7.5 in dts else 3
            if idx_30 < len(sec) and idx_75 < len(sec):
                rel_sec = abs((sec[idx_75] - sec[idx_30]) / sec[idx_30]) * 100 if sec[idx_30] != 0 else 0
                rel_res = abs((res[idx_75] - res[idx_30]) / res[idx_30]) * 100 if res[idx_30] != 0 else 0
                print(f"    Относительное изменение 30 -> 7.5 дней:")
                print(f"      Секулярная: {rel_sec:.4f}%")
                print(f"      Остаток:    {rel_res:.4f}%")
    
    # График
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    for idx, body_name in enumerate(body_list):
        ax1 = axes[idx, 0]
        ax2 = axes[idx, 1]
        
        for dt in dt_list:
            r = results[body_name][dt]
            ax1.plot(dt, r['secular_de422'], 'o-', label=f'Секулярная')
            ax1.plot(dt, r['secular_de422_center'], 's-', label=f'Центральная')
            ax1.plot(dt, r['secular_de422_smooth'], '^-', label=f'Сглаженная')
        
        ax1.set_xlabel('Шаг, дни')
        ax1.set_ylabel('dπ/dt, arcsec/век')
        ax1.set_title(f'{body_name}: секулярная скорость vs шаг')
        ax1.legend()
        ax1.grid(True)
        
        for dt in dt_list:
            r = results[body_name][dt]
            ax2.plot(dt, r['rms_P0'], 'o-', label='P0')
            ax2.plot(dt, r['rms_PGR'], 's-', label='P_GR')
            ax2.plot(dt, r['rms_P391838'], '^-', label='P_391838')
            ax2.plot(dt, r['rms_hybrid'], 'D-', label='P_hybrid')
        
        ax2.set_xlabel('Шаг, дни')
        ax2.set_ylabel('RMS, градусы')
        ax2.set_title(f'{body_name}: RMS долготы vs шаг')
        ax2.legend()
        ax2.grid(True)
    
    plt.suptitle('Тест сходимости: устойчивость результатов при изменении шага', fontsize=14)
    plt.tight_layout()
    plt.savefig('convergence_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n{'=' * 80}")
    print("График сохранён: convergence_test.png")
    print(f"{'=' * 80}")
    
    # Вывод: устойчив или нет
    print(f"\nВЫВОД:")
    for body_name in body_list:
        sec_vals = [results[body_name][dt]['secular_de422'] for dt in dt_list]
        res_vals = [results[body_name][dt]['residual'] for dt in dt_list]
        
        sec_spread = max(sec_vals) - min(sec_vals)
        res_spread = max(res_vals) - min(res_vals)
        res_mean = np.mean(res_vals)
        
        stable = sec_spread < 0.1 and res_spread < 0.1
        
        print(f"  {body_name}:")
        print(f"    Разброс секулярной скорости: {sec_spread:.6f} arcsec/век")
        print(f"    Разброс остатка:              {res_spread:.6f} arcsec/век")
        print(f"    Средний остаток:              {res_mean:.4f} arcsec/век")
        print(f"    Статус: {'УСТОЙЧИВО' if stable else 'НЕСТАБИЛЬНО — нужен меньший шаг'}")

if __name__ == '__main__':
    main()
