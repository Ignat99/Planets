"""
Извлечение GR-компоненты прецессии:
  GR = DE422 (total) − VSOP87E (Newtonian, без GR)

VSOP87E даёт орбитальные элементы: h = e·sin(ϖ), k = e·cos(ϖ)
  ϖ(t) = atan2(h(t), k(t))
  e(t) = sqrt(h² + k²)
  dϖ/dt = (k·dh/dt − h·dk/dt) / (h² + k²)  — аналитически

DE422 — полная эфемерида (Newton + GR).
  ϖ(t) — из вектора эксцентриситета
  dϖ/dt — численно, со сглаживанием

Разность: dϖ/dt_GR = dϖ/dt_DE422 − dϖ/dt_VSOP87

Модели:
  P0:       K / a^(5/2)
  P_GR:     K / (a^(5/2) * (1-e²))
  P_A391838: (K + L*(A391838(e)-1)) / a^(5/2)

Требования: pip install skyfield numpy matplotlib
VSOP87E файлы скачиваются автоматически.
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import urllib.request
import os
from skyfield.api import load

# ============================================================
# ЗАГРУЗКА DE422
# ============================================================
print("Загрузка эфемериды DE422...")
planets_eph = load('de422.bsp')
ts = load.timescale()
SUN = planets_eph[10]

#BODIES = {
#    'Mercury': planets_eph[1],
#    'Mars':    planets_eph[4],
#}

BODIES = {
    'Mercury': planets_eph[1],
    'Venus': planets_eph[2],  # Добавляем Venus
    'Earth': planets_eph[399],
    'Mars': planets_eph[4],
}

PLANETS = {
    'Mercury': {'a': 0.387098, 'e': 0.205630, 'varpi0': 77.456,  'period': 87.969},
    'Mars':    {'a': 1.523679, 'e': 0.093400, 'varpi0': 336.040, 'period': 686.98},
}

GM_SUN_AU3_DAY2 = 1.32712440018e20 / (1.495978707e11)**3 * (86400)**2

# ============================================================
# A391838
# ============================================================
A391838_norm = [1, 1, 1, 1.5, 3.0, 19/3, 55/4, 31, 72]

def A391838_truncated(e, order=8):
    return sum(c * e**k for k, c in enumerate(A391838_norm[:order+1]))

K = 3.8313   # arcsec/century
L = 0.6496

def precession_arcsec_per_century(model, a, e):
    if model == 'P0':
        return K / a**2.5
    elif model == 'P_GR':
        return K / (a**2.5 * (1 - e**2))
    elif model in ('P_391838', 'P_391838_et'):
        return (K + L * (A391838_truncated(e) - 1)) / a**2.5
    else:
        raise ValueError(f"Unknown model: {model}")

# ============================================================
# ЭКЛИПТИЧЕСКОЕ ПРЕОБРАЗОВАНИЕ
# ============================================================
OBLIQUITY = np.radians(23.4393)
_COS_EPS = np.cos(OBLIQUITY)
_SIN_EPS = np.sin(OBLIQUITY)

def to_ecliptic(vec):
    x, y, z = vec[0], vec[1], vec[2]
    return np.array([
        x,
        y * _COS_EPS + z * _SIN_EPS,
        -y * _SIN_EPS + z * _COS_EPS
    ])

# ============================================================
# DE422: ОСКУЛИРУЮЩИЕ ЭЛЕМЕНТЫ
# ============================================================
def helio_position(name, dt):
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    body = BODIES[name]
    sun_at = SUN.at(t)
    body_at = body.at(t)
    r_vec = np.array(body_at.position.au, float) - np.array(sun_at.position.au, float)
    v_vec = np.array(body_at.velocity.au_per_d, float) - np.array(sun_at.velocity.au_per_d, float)
    r_vec = to_ecliptic(r_vec)
    v_vec = to_ecliptic(v_vec)
    return r_vec, v_vec

def osculating_full(name, dt):
    """Возвращает (a_osc, e_osc, varpi_deg) из DE422."""
    r_vec, v_vec = helio_position(name, dt)
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
    e_osc = min(max(np.sqrt(np.sum(e_vec**2)), 0.0), 0.99)
    varpi_deg = np.degrees(np.arctan2(e_vec[1], e_vec[0])) % 360.0
    return a_osc, e_osc, varpi_deg

# ============================================================
# VSOP87E: ЗАГРУЗКА И ПАРСИНГ
# ============================================================
VSOP87E_URLS = {
    'Mercury': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87E.mer',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87E.mer'
    ],
    'Mars': [
        'https://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87E.mar',
        'http://ftp.imcce.fr/pub/ephem/planets/vsop87/VSOP87E.mar'
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

def download_vsop87e1(name):
    filename = f'VSOP87E_{name}.txt'
    if os.path.exists(filename):
        print(f"  {filename} уже загружен")
        return filename
    
    urls = VSOP87E_URLS.get(name, [])
    for url in urls:
        print(f"  Попытка загрузки: {url}")
        try:
            urllib.request.urlretrieve(url, filename)
            # Проверяем, что файл содержит числовые данные
            with open(filename, 'r') as f:
                content = f.read()
#                if ('VSOP87' not in content or 
#                    len(content.strip()) < 100 or 
#                    not any(char.isdigit() for char in content)):
#                    os.remove(filename)
#                    print(f"  Файл поврежден или не содержит числовых данных")
#                    continue
            print(f"  Успешно: {filename}")
            return filename
        except Exception as e:
            print(f"  Ошибка: {e}")
    
    return None



def parse_vsop87e(filename):
    series = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}  # a, lambda, h, k, p, q
    
    current_var = None
    current_power = 0
    
    with open(filename, 'r', encoding='latin1') as f:
        for line in f:
            # Отслеживаем заголовки секций (переменная и степень T)
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
            
            # Парсим строки данных
            parts = line.split()
            if len(parts) >= 5 and current_var in series:
                try:
                    # В файлах VSOP87E значения A, B, C всегда идут последними тремя столбцами в строке
                    A = float(parts[-3])
                    B = float(parts[-2])
                    C = float(parts[-1])
                    
                    series[current_var].append((current_power, A, B, C))
                except ValueError:
                    continue

    # Проверка выгрузки h (3) и k (4)
    if len(series[3]) < 5 or len(series[4]) < 5:
        raise ValueError(f"Не удалось извлечь достаточное количество членов рядов h и k из {filename}")
        
    return series




# ============================================================
# VSOP87E: ВЫЧИСЛЕНИЕ ϖ, e, dϖ/dt
# ============================================================
def vsop87e_compute(series, t_mill):
    # Вычисление k(t) и h(t)
    k = 0.0
    for power, A, B, C in series[3]:
        k += A * t_mill**power * np.cos(B + C * t_mill)
        
    h = 0.0
    for power, A, B, C in series[4]:
        h += A * t_mill**power * np.cos(B + C * t_mill)
        
    # Вычисление эксцентриситета
    e = np.sqrt(h**2 + k**2)
    
    # Вычисление перигелия
    varpi = np.arctan2(h, k)
    varpi_deg = np.degrees(varpi) % 360.0
    
    # Вычисление производных
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
        
    # Вычисление скорости изменения перигелия
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
    return (jd - 2451545.0) / 365250.0  # перевод в юлианские тысячелетия

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':

    # --- Загрузка VSOP87E ---
    print(f"\n{'='*80}")
    print("Загрузка VSOP87E файлов")
    print(f"{'='*80}")

    vsop_data = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  {name}:")
        filename = download_vsop87e(name)
        if filename is None:
            print("  Скрипт не может продолжить без VSOP87E файлов.")
            exit(1)
        series = parse_vsop87e(filename)
        vsop_data[name] = series
        print(f"  Распарсено: h={len(series[3])} членов, k={len(series[4])} членов")

        # Проверка начальных условий
        t_j2000 = 0.0  # момент J2000
        varpi_check, e_check, _ = vsop87e_compute(series, t_j2000)
        print(f"Проверка J2000: ϖ={varpi_check:.4f}°  e={e_check:.6f}")
        print(f"  Ожидаемо:        ϖ={PLANETS[name]['varpi0']:.4f}°  e={PLANETS[name]['e']:.6f}")

    # --- Сбор данных ---
    print(f"\n{'='*80}")
    print("Сбор данных: 1980 лет, шаг 30 дней")
    print(f"{'='*80}")

    start_dt = datetime(1010, 1, 1, 12, 0, 0)
    step_days = 30
    total_days = int(1980 * 365.25)
    sample_days = np.arange(0, total_days + 1, step_days)
    years = sample_days / 365.25

    # Окна сглаживания для DE422
    WINDOWS = {
        'Mercury': max(int(2 * 87.969 / step_days), 3),
        'Mars':    max(int(2 * 686.98 / step_days), 3),
    }

    results = {}
    for name in ['Mercury', 'Mars']:
        print(f"\n  {name}...")
        varpi_de422_raw = []
        varpi_vsop_raw = []
        e_de422_raw = []
        e_vsop_raw = []
        dvarpi_vsop_raw = []

        for d in sample_days:
            dt = start_dt + timedelta(days=int(d))

            # DE422
            _, e_de4, varpi_de4 = osculating_full(name, dt)
            varpi_de422_raw.append(varpi_de4)
            e_de422_raw.append(e_de4)

            # VSOP87E
            t_mill = datetime_to_vsop87_t(dt)
            varpi_vsop, e_vsop, dvarpi_vsop = vsop87e_compute(vsop_data[name], t_mill)
            varpi_vsop_raw.append(varpi_vsop)
            e_vsop_raw.append(e_vsop)
            dvarpi_vsop_raw.append(dvarpi_vsop)

        varpi_de422_raw = np.array(varpi_de422_raw)
        varpi_vsop_raw = np.array(varpi_vsop_raw)
        e_de422_raw = np.array(e_de422_raw)
        e_vsop_raw = np.array(e_vsop_raw)
        dvarpi_vsop_raw = np.array(dvarpi_vsop_raw)

        # Unwrap долгот
        varpi_de422_unwrapped = np.copy(varpi_de422_raw)
        for i in range(1, len(varpi_de422_unwrapped)):
            while varpi_de422_unwrapped[i] - varpi_de422_unwrapped[i-1] > 180:
                varpi_de422_unwrapped[i] -= 360
            while varpi_de422_unwrapped[i] - varpi_de422_unwrapped[i-1] < -180:
                varpi_de422_unwrapped[i] += 360

        varpi_vsop_unwrapped = np.copy(varpi_vsop_raw)
        for i in range(1, len(varpi_vsop_unwrapped)):
            while varpi_vsop_unwrapped[i] - varpi_vsop_unwrapped[i-1] > 180:
                varpi_vsop_unwrapped[i] -= 360
            while varpi_vsop_unwrapped[i] - varpi_vsop_unwrapped[i-1] < -180:
                varpi_vsop_unwrapped[i] += 360

        # Δϖ = ϖ_DE422 − ϖ_VSOP87  (GR-сигнал)
        dvarpi_diff = varpi_de422_unwrapped - varpi_vsop_unwrapped

        # Сглаживание dϖ/dt для DE422
        win = WINDOWS[name]
        kernel = np.ones(win) / win
        dvarpi_de422_smooth = np.convolve(
            np.gradient(varpi_de422_unwrapped, step_days / 365.25) * 3600 * 100,
            kernel, mode='valid'
        )  # arcsec/век

        # VSOP87 dϖ/dt (уже гладкий)
        # Смещаем для выравнивания с valid-режимом convolve
        offset = win // 2
        dvarpi_vsop_aligned = dvarpi_vsop_raw[offset:offset + len(dvarpi_de422_smooth)]

        # GR-остаток: DE422 − VSOP87
        gr_residual = dvarpi_de422_smooth - dvarpi_vsop_aligned

        # e(t) — для моделей
        e_for_models = e_de422_raw[offset:offset + len(dvarpi_de422_smooth)]
        years_aligned = years[offset:offset + len(dvarpi_de422_smooth)]

        # Модельные предсказания
        a0 = PLANETS[name]['a']
        p0_model = np.full(len(gr_residual), K / a0**2.5)
        p_gr_model = K / (a0**2.5 * (1 - e_for_models**2))
        p_a39_model = (K + L * (A391838_truncated(e_for_models) - 1)) / a0**2.5

        results[name] = {
            'years': years_aligned,
            'dvarpi_de422': dvarpi_de422_smooth,
            'dvarpi_vsop': dvarpi_vsop_aligned,
            'gr_residual': gr_residual,
            'e': e_for_models,
            'e_de422': e_de422_raw,
            'e_vsop': e_vsop_raw,
            'dvarpi_diff': dvarpi_diff,
            'years_full': years,
            'varpi_de422': varpi_de422_unwrapped,
            'varpi_vsop': varpi_vsop_unwrapped,
            'p0': p0_model,
            'p_gr': p_gr_model,
            'p_a39': p_a39_model,
        }

    # --- Таблица результатов ---
    print(f"\n{'='*80}")
    print("РЕЗУЛЬТАТЫ: GR-компонента прецессии")
    print(f"{'='*80}")

    for name in ['Mercury', 'Mars']:
        r = results[name]
        gr_res = r['gr_residual']

        # Средние значения (исключая края из-за сглаживания)
        n_trim = 20
        gr_mean = np.mean(gr_res[n_trim:-n_trim])
        p0_mean = np.mean(r['p0'][n_trim:-n_trim])
        pgr_mean = np.mean(r['p_gr'][n_trim:-n_trim])
        pa39_mean = np.mean(r['p_a39'][n_trim:-n_trim])

        # RMS остатка относительно моделей
        rms_p0 = np.sqrt(np.mean((gr_res[n_trim:-n_trim] - r['p0'][n_trim:-n_trim])**2))
        rms_pgr = np.sqrt(np.mean((gr_res[n_trim:-n_trim] - r['p_gr'][n_trim:-n_trim])**2))
        rms_pa39 = np.sqrt(np.mean((gr_res[n_trim:-n_trim] - r['p_a39'][n_trim:-n_trim])**2))

        # Линейная аппроксимация Δϖ(t)
        # Наклон = средняя GR-скорость (град/год → arcsec/век)
        yrs = r['years_full']
        dvp = r['dvarpi_diff']
        mask_fit = np.isfinite(dvp)
        if np.sum(mask_fit) > 10:
            coeffs = np.polyfit(yrs[mask_fit], dvp[mask_fit], 1)
            gr_slope = coeffs[0]  # град/год
            gr_slope_arcsec_cent = gr_slope * 3600 * 100  # arcsec/век
        else:
            gr_slope_arcsec_cent = np.nan

        print(f"\n  {name}:")
        print(f"    {'Источник':>20}  {'Среднее (arcsec/век)':>22}  {'RMS остатка':>14}")
        print(f"    {'-'*20}  {'-'*22}  {'-'*14}")
        print(f"    {'GR наблюдаемый':>20}  {gr_mean:22.4f}  {'—':>14}")
        print(f"    {'GR (наклон Δϖ)':>20}  {gr_slope_arcsec_cent:22.4f}  {'—':>14}")
        print(f"    {'P0':>20}  {p0_mean:22.4f}  {rms_p0:14.4f}")
        print(f"    {'P_GR':>20}  {pgr_mean:22.4f}  {rms_pgr:14.4f}")
        print(f"    {'P_A391838':>20}  {pa39_mean:22.4f}  {rms_pa39:14.4f}")

        # Отношения RMS
        if rms_pgr > 0:
            print(f"\n    RMS(A391838) / RMS(GR) = {rms_pa39 / rms_pgr:.4f}")
            if rms_pa39 < rms_pgr:
                print(f"    → A391838 точнее на {(1 - rms_pa39/rms_pgr)*100:.1f}%")
            else:
                print(f"    → GR точнее на {(rms_pa39/rms_pgr - 1)*100:.1f}%")

        # Разница моделей
        d_a39_gr = pa39_mean - pgr_mean
        print(f"\n    Разница средних (A391838 − GR) = {d_a39_gr:+.4f} arcsec/век")
        print(f"    За 1980 лет: {d_a39_gr * 1980:+.2f} arcsec = {d_a39_gr * 1980 / 3600:+.4f}°")

    # ============================================================
    # ГРАФИКИ
    # ============================================================

    def real_helio_long(name, dt):
        """
        Возвращает гелиоцентрическую эклиптическую долготу (J2000) планеты.
        """
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        body = BODIES[name]
        sun_at = SUN.at(t)
        body_at = body.at(t)
    
        # Гелиоцентрический вектор
        r_vec = np.array(body_at.position.au, float) - np.array(sun_at.position.au, float)
    
        # Преобразование в эклиптическую систему
        r_vec_ecl = to_ecliptic(r_vec)
    
        # Долгота
        lon_rad = np.arctan2(r_vec_ecl[1], r_vec_ecl[0])
        lon_deg = np.degrees(lon_rad) % 360.0
    
        # Расстояние
        r_au = np.sqrt(np.sum(r_vec_ecl**2))
    
        return lon_deg, r_au


    # --- График 1: Δϖ(t) — GR-сигнал ---
    fig1, axes1 = plt.subplots(1, 2, figsize=(18, 7))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes1[idx]
        r = results[name]
        ax.plot(r['years_full'], r['dvarpi_diff'] * 3600, 'b-', lw=0.5, alpha=0.7)
        # Линейная аппроксимация
        mask = np.isfinite(r['dvarpi_diff'])
        if np.sum(mask) > 10:
            coeffs = np.polyfit(r['years_full'][mask], r['dvarpi_diff'][mask], 1)
            ax.plot(r['years_full'], (np.polyval(coeffs, r['years_full'])) * 3600,
                    'r--', lw=1.5, label=f'Наклон = {coeffs[0]*3600*100:.2f} arcsec/век')
        ax.set_title(f'{name}: Δϖ = ϖ(DE422) − ϖ(VSOP87)', fontweight='bold')
        ax.set_xlabel('Годы от 1010 г.')
        ax.set_ylabel('Δϖ (arcsec)')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.2)

    fig1.suptitle('GR-сигнал: разность долгот перигелия (DE422 − VSOP87)',
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('gr_signal_delta_varpi.png', dpi=150, bbox_inches='tight')
    plt.show()

    # --- График 2: dϖ/dt — DE422 vs VSOP87 ---
    fig2, axes2 = plt.subplots(1, 2, figsize=(18, 7))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes2[idx]
        r = results[name]
        ax.plot(r['years'], r['dvarpi_de422'], 'k-', lw=0.3, alpha=0.3,
                label='DE422 (с GR)')
        ax.plot(r['years'], r['dvarpi_vsop'], 'r-', lw=0.8, alpha=0.7,
                label='VSOP87 (без GR)')
        ax.set_title(f'{name}: dϖ/dt', fontweight='bold')
        ax.set_xlabel('Годы от 1010 г.')
        ax.set_ylabel('arcsec/век')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    fig2.suptitle('Скорость прецессии: DE422 (полная) vs VSOP87 (ньютоновская)',
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('precession_de422_vs_vsop87.png', dpi=150, bbox_inches='tight')
    plt.show()

    # --- График 3: GR-остаток vs модели (КЛЮЧЕВЫЙ) ---
    fig3, axes3 = plt.subplots(1, 2, figsize=(18, 7))
    for idx, name in enumerate(['Mercury', 'Mars']):
        ax = axes3[idx]
        r = results[name]
        ax.plot(r['years'], r['gr_residual'], 'k-', lw=0.3, alpha=0.3,
                label='GR наблюдаемый')
        ax.plot(r['years'], r['p_gr'], 'b-', lw=1.0, alpha=0.8, label='P_GR')
        ax.plot(r['years'], r['p_a39'], 'r-', lw=1.0, alpha=0.8, label='P_A391838')
        ax.plot(r['years'], r['p0'], 'g--', lw=0.8, alpha=0.5, label='P₀')
        ax.set_title(f'{name}: GR-остаток vs модели', fontweight='bold')
        ax.set_xlabel('Годы от 1010 г.')
        ax.set_ylabel('arcsec/век')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    fig3.suptitle('GR-компонента прецессии: наблюдение vs модели',
                  fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('gr_residual_vs_models.png', dpi=150, bbox_inches='tight')
    plt.show()

    # --- График 4: e(t) — DE422 vs VSOP87 ---
    fig4, axes4 = plt.subplots(1, 2, figsize=(18, 7))
    for idx, name in enumerate(['Mercury', 'Mars']):
        r = results[name]
        ax = axes4[idx]
        ax.plot(r['years_full'], r['e_de422'], 'b-', lw=0.3, alpha=0.5, label='DE422')
        ax.plot(r['years_full'], r['e_vsop'], 'r-', lw=0.3, alpha=0.5, label='VSOP87')
        ax.set_title(f'{name}: e(t)', fontweight='bold')
        ax.set_xlabel('Годы от 1010 г.')
        ax.set_ylabel('e')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)

    fig4.suptitle('Эксцентриситет: DE422 vs VSOP87', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('e_de422_vs_vsop87.png', dpi=150, bbox_inches='tight')
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
    ax5.set_title('Гелиоцентрическая долгота (DE422, 1010–2990)', fontweight='bold')
    ax5.set_xlabel('Годы от 1010 г.')
    ax5.set_ylabel('λ (град)')
    ax5.legend()
    ax5.grid(True, alpha=0.2)
    plt.tight_layout()
    plt.savefig('heliocentric_longitude_2000yr.png', dpi=150, bbox_inches='tight')
    plt.show()

    print(f"\n{'='*80}")
    print("\u0413\u0440\u0430\u0444\u0438\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b:")
    print("  long_comparison_2000yr.png")
    print("  model_differences_2000yr.png")
    print("  precession_rate_comparison.png")
    print("  osculating_elements.png")
    print("  heliocentric_longitude_2000yr.png")
    print(f"{'='*80}")

