"""
Тест сходимости: проверка стабильности секулярной скорости прецессии
при разных шагах интегрирования.

Шаги: 60, 30, 15, 7.5 дней
Интервал: 1980 лет (1010–2990)
Планеты: Mercury, Mars
Метрики: dvarpi_secular (3 метода), RMS для моделей

Запуск: py convergence_test.py
"""

import numpy as np
import math
from scipy.integrate import cumulative_trapezoid
from skyfield.api import load
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ==========================================================================
# 1. Независимый генератор A391838 из беззнаковых чисел Стирлинга I рода
# ==========================================================================

def stirling_first_kind(N):
    """Беззнаковые числа Стирлинга первого рода s(n,k).
    Рекурсия: s(n,k) = s(n-1,k-1) + (n-1)*s(n-1,k)
    """
    s = [[0]*(N+1) for _ in range(N+1)]
    s[0][0] = 1
    for n in range(1, N+1):
        for k in range(1, n+1):
            s[n][k] = s[n-1][k-1] + (n-1)*s[n-1][k]
    return s

def generate_a391838(n_max):
    """Генерация A391838 из чисел Стирлинга.
    
    Формула OEIS A391838:
    a(n) = (n!)^2 * Sum_{k=0..floor(n/2)} |Stirling1(n-k, n-2k)| / ((2k+1)! * (n-k)!)
    
    Цепочка: Stirling -> диагонали (n-k, n-2k) -> A391838 -> нормировка a_n/n!
    """
    s = stirling_first_kind(n_max + 1)
    result = []
    for n in range(n_max + 1):
        total = 0.0
        for k in range(n // 2 + 1):
            row = n - k
            col = n - 2 * k
            if col < 0 or row < 0:
                break
            stirling_val = s[row][col]
            if stirling_val == 0:
                continue
            # (2k+1)!
            denom_fact_2k1 = math.factorial(2*k + 1)
            # (n-k)!
            denom_fact_nk = math.factorial(n - k)
            total += stirling_val / (denom_fact_2k1 * denom_fact_nk)
        # (n!)^2
        n_fact = math.factorial(n)
        a_n = n_fact * n_fact * total
        result.append(round(a_n))  # округляем до целого
    return result

# Генерация коэффициентов
A391838_int = generate_a391838(8)
A391838_norm = [A391838_int[n] / math.factorial(n) for n in range(9)]

print("=" * 80)
print("Генератор A391838 из беззнаковых чисел Стирлинга первого рода")
print("=" * 80)
print(f"  Формула: a(n) = (n!)^2 * Sum |Stirling1(n-k, n-2k)| / ((2k+1)! * (n-k)!)")
print(f"  Целочисленная последовательность: {A391838_int}")
print(f"  Нормированные коэффициенты a_n/n!: {A391838_norm}")
print(f"  Сравнение с OEIS: 1, 1, 2, 9, 72, 760, 9900, 156240, 2903040")
ref_check = [1, 1, 2, 9, 72, 760, 9900, 156240, 2903040]
all_match = all(A391838_int[i] == ref_check[i] for i in range(9))
print(f"  Все 9 членов совпадают: {'ДА' if all_match else 'НЕТ'}")
print()

# ==========================================================================
# 2. Константы и параметры
# ==========================================================================

AU_KM = 1.49597870700e8
GM_SUN_KM3_S2 = 1.32712440018e11
DAY_S = 86400.0
ARCSEC_PER_RAD = 206264.80624709636
C_KM_S = 299792.458
SECONDS_PER_CENTURY = 36525.0 * DAY_S
DEG_TO_ARCSEC = 3600.0

# Калиброванная константа прецессии (соответствует ya15.py)
# K = 3 * GM^1.5 / (c^2 * AU^2.5) * ARCSEC_PER_RAD * SECONDS_PER_CENTURY
K_PREC = 3 * (GM_SUN_KM3_S2 ** 1.5) / (C_KM_S ** 2 * AU_KM ** 2.5) * \
         ARCSEC_PER_RAD * SECONDS_PER_CENTURY

# L-коэффициент для A391838 (в тех же единицах, что K)
L_PREC = 0.6496

PLANETS = {
    'Mercury': {'de422_id': 1, 'a0': 0.387098, 'e0': 0.205630,
                'newtonian': 532.3035, 'newtonian_label': 'опубл.'},
    'Mars':    {'de422_id': 4, 'a0': 1.523710, 'e0': 0.093400,
                'newtonian': 1598.2000, 'newtonian_label': 'ориент.'},
}

# ==========================================================================
# 3. Функции
# ==========================================================================

def angular_difference_deg(a, b):
    """Угловая разность без скачков 0/360."""
    return (a - b + 180.0) % 360.0 - 180.0

def A391838_eval(e):
    """Вычисление A391838(e) через нормированные коэффициенты."""
    return sum(A391838_norm[k] * e ** k for k in range(9))

def precession_arcsec_per_century(model, a, e):
    """Скорость прецессии в arcsec/век.
    
    Формулы (соответствуют ya15.py):
      P0:       K / a^2.5
      P_GR:     K / (a^2.5 * (1 - e^2))
      P_391838: (K + L * (A391838(e) - 1)) / a^2.5
    """
    a25 = a ** 2.5
    if model == 'P0':
        return K_PREC / a25
    elif model == 'P_GR':
        return K_PREC / (a25 * (1.0 - e ** 2))
    elif model == 'P_391838':
        return (K_PREC + L_PREC * (A391838_eval(e) - 1.0)) / a25
    elif model == 'P_A391838_hybrid':
        # То же, что P_391838, но с переменными a(t), e(t)
        return (K_PREC + L_PREC * (A391838_eval(e) - 1.0)) / a25
    else:
        raise ValueError(f"Unknown model: {model}")

def helio_state(eph, planet_id, t):
    """Гелиоцентрические координаты из DE422 (геометрический режим)."""
    sun = eph['sun']
    body = eph['planets'][planet_id]
    pos = body.at(t) - sun.at(t)
    r_vec = np.array([pos.position.au[0], pos.position.au[1], pos.position.au[2]])
    v_vec = np.array([pos.velocity.au_per_d[0], pos.velocity.au_per_d[1],
                      pos.velocity.au_per_d[2]])
    return r_vec, v_vec

def osculating_elements(r_vec, v_vec):
    """Мгновенные оскулирующие элементы (Sun-only, двухтельные).
    
    Это НЕ канонические элементы VSOP87 и НЕ чисто секулярные элементы.
    """
    mu = GM_SUN_KM3_S2 / (AU_KM ** 3) * DAY_S ** 2
    r = np.linalg.norm(r_vec)
    v = np.linalg.norm(v_vec)
    energy = 0.5 * v ** 2 - mu / r
    a = -mu / (2 * energy)
    h_vec = np.cross(r_vec, v_vec)
    h = np.linalg.norm(h_vec)
    e_vec = np.cross(v_vec, h_vec) / mu - r_vec / r
    e = np.linalg.norm(e_vec)
    # Долгота проекции вектора эксцентриситета на эклиптику (J2000)
    varpi = np.degrees(np.arctan2(e_vec[1], e_vec[0])) % 360.0
    return a, e, varpi

def run_convergence_test(eph, ts, planet_name, step_days_list):
    """Запуск теста сходимости для одной планеты."""
    params = PLANETS[planet_name]
    planet_id = params['de422_id']
    
    results = {}
    
    for step_days in step_days_list:
        # Временная сетка
        year_start = 1010
        year_end = 2990
        n_steps = int((year_end - year_start) * 365.25 / step_days)
        
        # Генерация времени
        years_arr = np.linspace(year_start, year_end, n_steps + 1)
        start_jd = int(year_start * 365.25 + 1721028.5)
        days = np.arange(0, n_steps + 1) * step_days
        
        print(f"  {planet_name}, шаг {step_days} дней, {n_steps + 1} точек...")
        
        # Сбор оскулирующих элементов
        varpi_arr = np.zeros(n_steps + 1)
        a_arr = np.zeros(n_steps + 1)
        e_arr = np.zeros(n_steps + 1)
        
        batch = 200
        for i in range(0, n_steps + 1, batch):
            end_i = min(i + batch, n_steps + 1)
            t_batch = ts.tt(jd=start_jd + days[i:end_i])
            for j in range(end_i - i):
                idx = i + j
                r_vec, v_vec = helio_state(eph, planet_id, t_batch[j])
                a_osc, e_osc, varpi = osculating_elements(r_vec, v_vec)
                a_arr[idx] = a_osc
                e_arr[idx] = e_osc
                varpi_arr[idx] = varpi
        
        # Unwrap
        varpi_unwrapped = np.zeros_like(varpi_arr)
        varpi_unwrapped[0] = varpi_arr[0]
        for i in range(1, len(varpi_arr)):
            diff = angular_difference_deg(varpi_arr[i], varpi_arr[i-1])
            varpi_unwrapped[i] = varpi_unwrapped[i-1] + diff
        
        # Секулярная скорость: 3 метода
        # Все скорости в градусах/век — переводим в arcsec/век (* 3600)
        years_actual = years_arr - years_arr[0]
        
        # 1. Полный интервал
        coef_full = np.polyfit(years_arr, varpi_unwrapped, 1)
        secular_full = coef_full[0] * DEG_TO_ARCSEC
        
        # 2. Центральный интервал (10-90%)
        mask = (years_arr > year_start + 0.1 * (year_end - year_start)) & \
              (years_arr < year_end - 0.1 * (year_end - year_start))
        coef_central = np.polyfit(years_arr[mask], varpi_unwrapped[mask], 1)
        secular_central = coef_central[0] * DEG_TO_ARCSEC
        
        # 3. Сглаженная кривая
        window = max(1, int(100 * 365.25 / step_days))
        kernel = np.ones(window) / window
        varpi_smooth = np.convolve(varpi_unwrapped, kernel, mode='same')
        coef_smooth = np.polyfit(years_arr[window:-window],
                                 varpi_smooth[window:-window], 1)
        secular_smooth = coef_smooth[0] * DEG_TO_ARCSEC
        
        # Остаток после Newtonian
        newtonian = params['newtonian']
        residual_full = secular_full - newtonian
        residual_central = secular_central - newtonian
        residual_smooth = secular_smooth - newtonian
        
        # Модели (постоянные a0, e0)
        a0 = params['a0']
        e0 = params['e0']
        p0 = precession_arcsec_per_century('P0', a0, e0)
        p_gr = precession_arcsec_per_century('P_GR', a0, e0)
        p_391838 = precession_arcsec_per_century('P_391838', a0, e0)
        
        # Гибридная модель (переменные a(t), e(t))
        p_hybrid_arr = np.array([
            precession_arcsec_per_century('P_A391838_hybrid', a_arr[i], e_arr[i])
            for i in range(n_steps + 1)
        ])
        p_hybrid_mean = np.mean(p_hybrid_arr)
        
        # RMS для долготы (равномерная прецессия)
        varpi_model = varpi_unwrapped[0] + secular_full / DEG_TO_ARCSEC * (years_arr - years_arr[0])
        rms_longitude = np.sqrt(np.mean((varpi_unwrapped - varpi_model) ** 2))
        
        results[step_days] = {
            'n_points': n_steps + 1,
            'secular_full': secular_full,
            'secular_central': secular_central,
            'secular_smooth': secular_smooth,
            'residual_full': residual_full,
            'residual_central': residual_central,
            'residual_smooth': residual_smooth,
            'p0': p0,
            'p_gr': p_gr,
            'p_391838': p_391838,
            'p_hybrid': p_hybrid_mean,
            'rms_longitude': rms_longitude,
        }
    
    return results

# ==========================================================================
# 4. Главный блок
# ==========================================================================

def main():
    print("Загрузка эфемериды DE422...")
    eph_file = load('de422.bsp')
    eph = {
        'sun': eph_file['sun'],
        'planets': {i: eph_file[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    }
    ts = load.timescale()
    
    step_days_list = [60, 30, 15, 7.5]
    
    all_results = {}
    
    for planet_name in ['Mercury', 'Mars']:
        print(f"\n{'=' * 80}")
        print(f"Тест сходимости: {planet_name}")
        print(f"{'=' * 80}")
        
        results = run_convergence_test(eph, ts, planet_name, step_days_list)
        all_results[planet_name] = results
        
        # Вывод таблицы
        print(f"\n  {'Шаг':>6s} {'Точек':>8s} {'Секулярная':>12s} {'Центр.':>12s} "
              f"{'Сглаж.':>12s} {'Остаток':>10s} {'P0':>10s} {'P_GR':>10s} "
              f"{'P_391838':>10s} {'P_гибр.':>10s}")
        print(f"  {'-'*6} {'-'*8} {'-'*12} {'-'*12} {'-'*12} {'-'*10} "
              f"{'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        
        for step in step_days_list:
            r = results[step]
            print(f"  {step:6.1f} {r['n_points']:8d} "
                  f"{r['secular_full']:12.4f} {r['secular_central']:12.4f} "
                  f"{r['secular_smooth']:12.4f} "
                  f"{r['residual_full']:10.4f} {r['p0']:10.4f} {r['p_gr']:10.4f} "
                  f"{r['p_391838']:10.4f} {r['p_hybrid']:10.4f}")
    
    # Сводная таблица
    print(f"\n{'=' * 80}")
    print("СВОДНАЯ ТАБЛИЦА СХОДИМОСТИ")
    print(f"{'=' * 80}")
    
    for planet in ['Mercury', 'Mars']:
        print(f"\n  {planet}:")
        print(f"  {'Шаг':>6s} {'Секулярная':>12s} {'Центр.':>12s} {'Сглаж.':>12s} "
              f"{'Остаток':>10s} {'RMS':>10s}")
        print(f"  {'-'*6} {'-'*12} {'-'*12} {'-'*12} {'-'*10} {'-'*10}")
        for step in step_days_list:
            r = all_results[planet][step]
            print(f"  {step:6.1f} {r['secular_full']:12.4f} {r['secular_central']:12.4f} "
                  f"{r['secular_smooth']:12.4f} {r['residual_full']:10.4f} "
                  f"{r['rms_longitude']:10.6f}")
    
    # Анализ сходимости
    print(f"\n{'=' * 80}")
    print("АНАЛИЗ СХОДИМОСТИ")
    print(f"{'=' * 80}")
    
    for planet in ['Mercury', 'Mars']:
        print(f"\n  {planet}:")
        for i in range(len(step_days_list) - 1):
            s1 = step_days_list[i]
            s2 = step_days_list[i + 1]
            r1 = all_results[planet][s1]
            r2 = all_results[planet][s2]
            d_sec = r2['secular_full'] - r1['secular_full']
            d_res = r2['residual_full'] - r1['residual_full']
            d_rms = r2['rms_longitude'] - r1['rms_longitude']
            print(f"    {s1:.1f} -> {s2:.1f} дней:")
            print(f"      Δ секулярная:  {d_sec:+.6f} arcsec/век")
            print(f"      Δ остаток:     {d_res:+.6f} arcsec/век")
            print(f"      Δ RMS:         {d_rms:+.6f}°")
        
        # Относительное изменение 30 -> 7.5 дней
        r30 = all_results[planet][30.0]
        r75 = all_results[planet][7.5]
        rel_change = abs(r75['secular_full'] - r30['secular_full']) / abs(r30['secular_full']) * 100
        print(f"    Относительное изменение 30 -> 7.5 дней:")
        print(f"      Секулярная: {rel_change:.4f}%")
    
    # Итог
    print(f"\n{'=' * 80}")
    print("ВЫВОД:")
    print(f"{'=' * 80}")
    for planet in ['Mercury', 'Mars']:
        seculars = [all_results[planet][s]['secular_full'] for s in step_days_list]
        spread = max(seculars) - min(seculars)
        mean_sec = np.mean(seculars)
        residuals = [all_results[planet][s]['residual_full'] for s in step_days_list]
        mean_res = np.mean(residuals)
        print(f"  {planet}:")
        print(f"    Разброс секулярной скорости: {spread:.6f} arcsec/век")
        print(f"    Средний остаток:              {mean_res:.4f} arcsec/век")
        status = "УСТОЙЧИВО" if spread < 0.01 else "НЕСТАБИЛЬНО"
        print(f"    Статус: {status}")
    
    # График сходимости
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    for ax, planet in zip(axes, ['Mercury', 'Mars']):
        steps = step_days_list
        seculars = [all_results[planet][s]['secular_full'] for s in steps]
        centrals = [all_results[planet][s]['secular_central'] for s in steps]
        smooths = [all_results[planet][s]['secular_smooth'] for s in steps]
        
        ax.semilogx(steps, seculars, 'o-', label='Полный интервал', markersize=8)
        ax.semilogx(steps, centrals, 's--', label='Центральный (10-90%)', markersize=6)
        ax.semilogx(steps, smooths, '^:', label='Сглаженный', markersize=6)
        
        params = PLANETS[planet]
        newtonian = params['newtonian']
        # Теоретические линии
        a0 = params['a0']
        e0 = params['e0']
        p_gr = precession_arcsec_per_century('P_GR', a0, e0)
        p_391838 = precession_arcsec_per_century('P_391838', a0, e0)
        
        ax.axhline(y=newtonian + p_gr, color='green', linestyle='--',
                  alpha=0.5, label=f'Newtonian + GR = {newtonian + p_gr:.1f}')
        ax.axhline(y=newtonian + p_391838, color='red', linestyle='--',
                  alpha=0.5, label=f'Newtonian + A391838 = {newtonian + p_391838:.1f}')
        
        ax.set_xlabel('Шаг, дней')
        ax.set_ylabel('Секулярная скорость, arcsec/век')
        ax.set_title(f'{planet}: сходимость по шагу')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.invert_xaxis()
    
    plt.tight_layout()
    plt.savefig('convergence_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n  График сохранён: convergence_test.png")
    print("\nТест сходимости завершён.")

if __name__ == '__main__':
    main()
