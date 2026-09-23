#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  Кеплеровы параметры орбит и их звуковые проявления
  для Меркурия, Венеры, Земли и Марса

  Скрипт в стиле галгебра-проектов:
    1) Символьный вывод всех ключевых формул из статьи "Расчёт положения
       небесных тел" с помощью sympy;
    2) Численный расчёт шести кеплеровских параметров для четырёх планет
       по данным NASA Planetary Fact Sheet (J2000.0);
    3) Отображение каждого параметра в звуковую характеристику.

  Источники данных:
    NASA Planetary Fact Sheet — https://nssdc.gsfc.nasa.gov/planetary/factsheet/
    Standish & Williams, J2000.0 Keplerian elements.

  Шесть кеплеровских параметров (Keplerian orbital elements):
    a   — Semi-major axis           / Большая полуось
    e   — Eccentricity              / Эксцентриситет
    i   — Inclination               / Наклонение (к эклиптике)
    Ω   — Longitude of ascending node / Долгота восходящего узла
    ω   — Argument of perihelion   / Аргумент перигелия
    M₀  — Mean anomaly at epoch     / Средняя аномалия в эпоху

  Звуковое отображение (Sound mapping):
    a  → базовая частота (pitch / base frequency)
    e  → глубина амплитудной модуляции (tremolo depth)
    i  → панорама / пространственное смещение (pan)
    Ω  → фазовый сдвиг относительно основного аккорда (phase shift)
    ω  → тембральная окраска / добавочные гармоники (timbre)
    M₀ → текущее положение в цикле модуляции (position in modulation cycle)
================================================================================
"""

from sympy import (
    symbols, var, sin, cos, tan, sqrt, pi, Function, Derivative,
    simplify, expand, trigsimp, solve, latex, Eq, Rational, atan2,
    nsimplify, Integral, oo
)
from sympy import Matrix, Symbol
import numpy as np

# ============================================================================
# ЧАСТЬ 1. СИМВОЛЬНЫЙ ВЫВОД ФОРМУЛ ИЗ СТАТЬИ
# ============================================================================

print("=" * 80)
print("ЧАСТЬ 1. СИМВОЛЬНЫЙ ВЫВОД ФОРМУЛ КЕПЛЕРОВОЙ ОРБИТЫ")
print("=" * 80)

# --- Символы -----------------------------------------------------------------
# G — гравитационная постоянная (gravitational constant)
# m1, m2 — массы двух тел (masses of the two bodies)
# R — расстояние между телами (distance between bodies)
# r — радиус-вектор (radius vector)
# v — скорость (velocity)
# t — время (time)
# theta — полярный угол / истинная аномалия (true anomaly)
# p — фокальный параметр (semi-latus rectum / focal parameter)
# e — эксцентриситет (eccentricity)
# a — большая полуось (semi-major axis)
# b — малая полуось (semi-minor axis)
# n — среднее движение (mean motion)
# T — период обращения (orbital period)
# M — средняя аномалия (mean anomaly)
# E — эксцентрическая аномалия (eccentric anomaly)
# nu — истинная аномалия (true anomaly) — обозначим как theta в символьной части

G, m1, m2, R_mag = symbols('G m_1 m_2 R', positive=True)
r_sym, v_sym, t_sym = symbols('r v t')
theta, p_foc, e_sym = symbols('theta p e')
a_sym, b_sym = symbols('a b', positive=True)
n_sym, T_sym, M_sym = symbols('n T M')
E_sym, nu_sym = symbols('E nu')
mu = symbols('mu', positive=True)  # mu = G * M_sun (standard gravitational parameter)

# ----------------------------------------------------------------------------
# 1.1. Закон всемирного тяготения Ньютона (Newton's law of universal gravitation)
#      F = G * m1 * m2 / R^2
# ----------------------------------------------------------------------------
print("\n--- 1.1. Закон всемирного тяготения Ньютона ---")
print("    Newton's law of universal gravitation\n")

F_grav = G * m1 * m2 / R_mag**2
print("F =", latex(F_grav))
print("где G — гравитационная постоянная (gravitational constant)")

# ----------------------------------------------------------------------------
# 1.2. Второй закон Ньютона (Newton's second law)
#      F = m * a  =>  a = F / m
#      В векторной форме: d(m*v)/dt = F
#      Для постоянной массы: m * dv/dt = F  =>  m * a = F
# ----------------------------------------------------------------------------
print("\n--- 1.2. Второй закон Ньютона ---")
print("    Newton's second law\n")

m_body, F_vec = symbols('m F_vec')
# В векторной форме: dp/dt = F, где p = m*v — импульс (momentum)
p_mom = symbols('p')  # импульс / momentum
# dp/dt = F  =>  m * dv/dt = F  =>  m * a = F
print(r"  $\frac{d\vec{p}}{dt} = \vec{F}$,  где $\vec{p} = m\vec{v}$ — импульс (momentum)")
print(r"  Для постоянной массы: $m\vec{a} = \vec{F}$")

# ----------------------------------------------------------------------------
# 1.3. Закон сохранения момента импульса (Conservation of angular momentum)
#      L = r × p = m * r × v = const
#      dL/dt = r × F = 0  (для центральной силы)
# ----------------------------------------------------------------------------
print("\n--- 1.3. Закон сохранения момента импульса ---")
print("    Conservation of angular momentum\n")

# Производная векторного произведения r × v:
# d/dt(r × v) = dr/dt × v + r × dv/dt = v × v + r × a = 0 + r × a
# Для центральной силы r × F = 0, значит r × a = 0
# Следовательно d/dt(r × v) = 0  =>  r × v = const
print(r"  $\frac{d}{dt}(\vec{r} \times \vec{v}) = \vec{v} \times \vec{v} + \vec{r} \times \vec{a} = 0 + 0 = 0$")
print(r"  $\Rightarrow \vec{r} \times \vec{v} = \text{const}$  (закон сохранения момента импульса)")
print("  Second Kepler's law: равные площади за равные времена")
print("  (equal areas in equal times)")

# ----------------------------------------------------------------------------
# 1.4. Секториальная скорость (Sectorial velocity)
#      dS/dt = (1/2) * |r × v| = const
# ----------------------------------------------------------------------------
print("\n--- 1.4. Секториальная скорость ---")
print("    Sectorial velocity\n")

# |r × v| = r * v * sin(angle) = r * r * d(theta)/dt = r^2 * d(theta)/dt
# dS/dt = (1/2) * r^2 * d(theta)/dt
r_mod = symbols('r', positive=True)
dtheta_dt = symbols('\\dot{\\theta}')
sectorial_vel = Rational(1, 2) * r_mod**2 * dtheta_dt
print(r"  $\frac{dS}{dt} = \frac{1}{2} r^2 \dot{\theta} = \text{const}$")
print("  где dS/dt — секториальная скорость (sectorial velocity)")

# ----------------------------------------------------------------------------
# 1.5. Уравнение орбиты — уравнение эллипса в полярных координатах
#      (Orbit equation — ellipse in polar coordinates)
#      r(θ) = p / (1 + e * cos(θ))
#      где p = a(1 - e^2) — фокальный параметр (semi-latus rectum)
# ----------------------------------------------------------------------------
print("\n--- 1.5. Уравнение орбиты (эллипс в полярных координатах) ---")
print("    Orbit equation — ellipse in polar coordinates\n")

# Радиус-вектор как функция истинной аномалии
# r(theta) = p / (1 + e * cos(theta))
r_orbit = p_foc / (1 + e_sym * cos(theta))
print(r"  $r(\theta) = \frac{p}{1 + e\cos\theta}$")
print(r"  где $p = a(1 - e^2)$ — фокальный параметр (semi-latus rectum)")

# ----------------------------------------------------------------------------
# 1.6. Параметры эллипса (Ellipse parameters)
#      S = π * a * b         — площадь эллипса (area of ellipse)
#      b = a * sqrt(1 - e^2) — малая полуось (semi-minor axis)
#      e = sqrt(1 - b^2/a^2) — эксцентриситет (eccentricity)
#      p = a * (1 - e^2)     — фокальный параметр (semi-latus rectum)
# ----------------------------------------------------------------------------
print("\n--- 1.6. Параметры эллипса ---")
print("    Ellipse parameters\n")

S_ellipse = pi * a_sym * b_sym
b_from_e = a_sym * sqrt(1 - e_sym**2)
e_from_ab = sqrt(1 - (b_sym/a_sym)**2)
p_from_ae = a_sym * (1 - e_sym**2)

print(r"  Площадь эллипса (Area):  $S = \pi a b$ =", latex(S_ellipse))
print(r"  Малая полуось (Semi-minor axis):  $b = a\sqrt{1 - e^2}$ =", latex(b_from_e))
print(r"  Эксцентриситет (Eccentricity):  $e = \sqrt{1 - \frac{b^2}{a^2}}$ =", latex(e_from_ab))
print(r"  Фокальный параметр (Semi-latus rectum):  $p = a(1 - e^2)$ =", latex(p_from_ae))

# ----------------------------------------------------------------------------
# 1.7. Первый закон Кеплера (Kepler's first law)
#      Каждая планета обращается по эллипсу, в одном из фокусов которого
#      находится Солнце.
# ----------------------------------------------------------------------------
print("\n--- 1.7. Первый закон Кеплера ---")
print("    Kepler's first law\n")
print("  Planets move in elliptical orbits with the Sun at one focus.")
print("  Планеты движутся по эллиптическим орбитам, в одном из фокусов — Солнце.")

# ----------------------------------------------------------------------------
# 1.8. Третий закон Кеплера (Kepler's third law)
#      T^2 = (4π^2 / (G*M)) * a^3
#      или: n^2 * a^3 = mu  (mu = G*M_sun)
# ----------------------------------------------------------------------------
print("\n--- 1.8. Третий закон Кеплера ---")
print("    Kepler's third law\n")

T_squared = 4 * pi**2 / mu * a_sym**3
print(r"  $T^2 = \frac{4\pi^2}{\mu} a^3$,  где $\mu = GM_{\odot}$")

# ----------------------------------------------------------------------------
# 1.9. Среднее движение (Mean motion)
#      n = 2π / T = sqrt(mu / a^3)
# ----------------------------------------------------------------------------
print("\n--- 1.9. Среднее движение ---")
print("    Mean motion\n")

n_motion = 2 * pi / T_sym
n_motion2 = sqrt(mu / a_sym**3)
print(r"  $n = \frac{2\pi}{T}$ =", latex(n_motion))
print(r"  $n = \sqrt{\frac{\mu}{a^3}}$ =", latex(n_motion2))
print("  n — среднее движение (mean motion), рад/с")

# ----------------------------------------------------------------------------
# 1.10. Средняя аномалия (Mean anomaly)
#       M = n * (t - t0) + M0
#       M0 — средняя аномалия в эпоху (mean anomaly at epoch)
# ----------------------------------------------------------------------------
print("\n--- 1.10. Средняя аномалия ---")
print("    Mean anomaly\n")

M0_sym = symbols('M_0')
t0_sym = symbols('t_0')
M_anomaly = n_sym * (t_sym - t0_sym) + M0_sym
print(r"  $M = n(t - t_0) + M_0$")
print("  M — средняя аномалия (mean anomaly)")
print("  M₀ — средняя аномалия в эпоху (mean anomaly at epoch)")

# ----------------------------------------------------------------------------
# 1.11. Уравнение Кеплера (Kepler's equation)
#       M = E - e * sin(E)
#       где E — эксцентрическая аномалия (eccentric anomaly)
# ----------------------------------------------------------------------------
print("\n--- 1.11. Уравнение Кеплера ---")
print("    Kepler's equation\n")

kepler_eq = Eq(M_sym, E_sym - e_sym * sin(E_sym))
print(r"  $M = E - e\sin E$")
print("  E — эксцентрическая аномалия (eccentric anomaly)")
print("  Уравнение связывает среднюю (M) и эксцентрическую (E) аномалии")

# ----------------------------------------------------------------------------
# 1.12. Связь истинной и эксцентрической аномалии
#       (True anomaly from eccentric anomaly)
#       tan(nu/2) = sqrt((1+e)/(1-e)) * tan(E/2)
#       r = a * (1 - e * cos(E))
# ----------------------------------------------------------------------------
print("\n--- 1.12. Связь истинной и эксцентрической аномалии ---")
print("    True anomaly from eccentric anomaly\n")

tan_nu_half = sqrt((1 + e_sym) / (1 - e_sym)) * tan(E_sym / 2)
r_from_E = a_sym * (1 - e_sym * cos(E_sym))
print(r"  $\tan\frac{\nu}{2} = \sqrt{\frac{1+e}{1-e}} \tan\frac{E}{2}$")
print(r"  $r = a(1 - e\cos E)$")
print("  nu — истинная аномалия (true anomaly)")

# ----------------------------------------------------------------------------
# 1.13. Связь истинной аномалии с радиус-вектором
#       r = p / (1 + e * cos(nu)) = a(1-e^2) / (1 + e*cos(nu))
# ----------------------------------------------------------------------------
print("\n--- 1.13. Радиус-вектор через истинную аномалию ---")
print("    Radius vector from true anomaly\n")

r_from_nu = a_sym * (1 - e_sym**2) / (1 + e_sym * cos(nu_sym))
print(r"  $r = \frac{a(1 - e^2)}{1 + e\cos\nu}$")
print("  Это уравнение эллипса в полярных координатах (orbit equation in polar form)")

# ----------------------------------------------------------------------------
# 1.14. Ориентация орбиты в пространстве
#       (Orbital orientation in 3D space)
#       i  — наклонение (inclination) — угол между плоскостью орбиты и эклиптикой
#       Ω  — долгота восходящего узла (longitude of ascending node)
#       ω  — аргумент перигелия (argument of perihelion)
#       ϖ  — долгота перигелия (longitude of perihelion) = Ω + ω
#       L  — средняя долгота (mean longitude) = ϖ + M
#       M  — средняя аномалия (mean anomaly) = L - ϖ
# ----------------------------------------------------------------------------
print("\n--- 1.14. Ориентация орбиты в пространстве ---")
print("    Orbital orientation in 3D\n")

Omega_sym = symbols('Omega')
omega_sym = symbols('omega')
varpi_sym = symbols('varpi')
L_sym = symbols('L')

print("  Six Keplerian elements (шесть кеплеровских элементов):")
print("    a — Semi-major axis           / Большая полуось")
print("    e — Eccentricity              / Эксцентриситет")
print("    i — Inclination               / Наклонение (к эклиптике)")
print("    Ω — Longitude of ascending node / Долгота восходящего узла (RAAN)")
print("    ω — Argument of perihelion    / Аргумент перигелия")
print("    M₀— Mean anomaly at epoch     / Средняя аномалия в эпоху")
print()
print("  Связанные величины (derived quantities):")
print("    ϖ = Ω + ω   (longitude of perihelion / долгота перигелия)")
print("    L = ϖ + M   (mean longitude / средняя долгота)")
print("    M = L - ϖ   (mean anomaly / средняя аномалия)")

# ----------------------------------------------------------------------------
# 1.15. Переход от орбитальных координат к гелиоцентрическим эклиптическим
#       (Transformation from orbital to heliocentric ecliptic coordinates)
#       X = r * [cos(Ω)*cos(ω+ν) - sin(Ω)*sin(ω+ν)*cos(i)]
#       Y = r * [sin(Ω)*cos(ω+ν) + cos(Ω)*sin(ω+ν)*cos(i)]
#       Z = r * sin(ω+ν) * sin(i)
# ----------------------------------------------------------------------------
print("\n--- 1.15. Гелиоцентрические эклиптические координаты ---")
print("    Heliocentric ecliptic coordinates\n")

i_sym = symbols('i')
X_helio = r_sym * (cos(Omega_sym) * cos(omega_sym + nu_sym) - sin(Omega_sym) * sin(omega_sym + nu_sym) * cos(i_sym))
Y_helio = r_sym * (sin(Omega_sym) * cos(omega_sym + nu_sym) + cos(Omega_sym) * sin(omega_sym + nu_sym) * cos(i_sym))
Z_helio = r_sym * sin(omega_sym + nu_sym) * sin(i_sym)

print(r"  $X = r[\cos\Omega\cos(\omega+\nu) - \sin\Omega\sin(\omega+\nu)\cos i]$")
print(r"  $Y = r[\sin\Omega\cos(\omega+\nu) + \cos\Omega\sin(\omega+\nu)\cos i]$")
print(r"  $Z = r\sin(\omega+\nu)\sin i$")
print()
print("  где r — радиус-вектор, ν — истинная аномалия (true anomaly)")


# ============================================================================
# ЧАСТЬ 2. ЧИСЛЕННЫЕ РАСЧЁТЫ ДЛЯ МЕРКУРИЯ, ВЕНЕРЫ, ЗЕМЛИ И МАРСА
# ============================================================================

print("\n" + "=" * 80)
print("ЧАСТЬ 2. ЧИСЛЕННЫЕ РАСЧЁТЫ ДЛЯ ПЛАНЕТ")
print("=" * 80)

# --- Данные NASA Planetary Fact Sheet + J2000.0 элементы ---
# Источник: https://nssdc.gsfc.nasa.gov/planetary/factsheet/
#           Standish & Williams, J2000.0 Keplerian elements
#           in-the-sky.org (J2000 osculating elements)
#
# Для Земли используем данные из Standish (через in-the-sky.org):
#   a = 1.00000018 AU, e = 0.01673163, i = -0.00054346 deg
#   L = 100.46645683 deg, ϖ = 102.93768193 deg, Ω = -11.26064 deg
#   => ω = ϖ - Ω = 114.198 deg, M = L - ϖ = -2.471 deg (= 357.529 deg)
# (У Земли наклонение ~0, поэтому Ω и ω определены условно)

AU = 1.495978707e8  # астрономическая единица в км (AU in km)

planets = {
    "Mercury (Меркурий)": {
        # NASA Fact Sheet
        "mass_1024kg":      0.330,
        "diameter_km":      4879,
        "orbital_period_d": 88.0,
        "orbital_vel_km_s": 47.4,
        "dist_sun_1e6km":   57.9,
        "perihelion_1e6km": 46.0,
        "aphelion_1e6km":   69.8,
        # J2000.0 Keplerian elements (Standish/Williams)
        "a_AU":    0.38709927,
        "e":       0.20563593,
        "i_deg":   7.00497902,
        "Omega_deg": 48.33076593,   # Longitude of ascending node
        "omega_deg": 29.12703,       # Argument of perihelion
        "M0_deg":  174.79253,        # Mean anomaly at epoch
        "L_deg":   252.250323,       # Mean longitude
        "varpi_deg": 77.4577963,     # Longitude of perihelion = Ω + ω
    },
    "Venus (Венера)": {
        "mass_1024kg":      4.87,
        "diameter_km":      12104,
        "orbital_period_d": 224.7,
        "orbital_vel_km_s": 35.0,
        "dist_sun_1e6km":   108.2,
        "perihelion_1e6km": 107.5,
        "aphelion_1e6km":   108.9,
        "a_AU":    0.72333566,
        "e":       0.00677672,
        "i_deg":   3.39468,
        "Omega_deg": 76.67984,
        "omega_deg": 54.92262,
        "M0_deg":  50.37663,
        "L_deg":   181.979098,
        "varpi_deg": 131.60246,
    },
    "Earth (Земля)": {
        "mass_1024kg":      5.97,
        "diameter_km":      12756,
        "orbital_period_d": 365.2,
        "orbital_vel_km_s": 29.8,
        "dist_sun_1e6km":   149.6,
        "perihelion_1e6km": 147.1,
        "aphelion_1e6km":   152.1,
        "a_AU":    1.00000261,
        "e":       0.01671122,
        "i_deg":  -0.00001531,
        "Omega_deg": 0.0,       # условно, т.к. i ~ 0 (undefined for i≈0)
        "omega_deg": 102.93768193,  # Для Земли ω ≈ ϖ, т.к. Ω ≈ 0
        "M0_deg":  357.529,      # M = L - ϖ ≈ 100.467 - 102.938 = -2.471 ≡ 357.529
        "L_deg":   100.46645683,
        "varpi_deg": 102.93768193,
    },
    "Mars (Марс)": {
        "mass_1024kg":      0.642,
        "diameter_km":      6792,
        "orbital_period_d": 687.0,
        "orbital_vel_km_s": 24.1,
        "dist_sun_1e6km":   228.0,
        "perihelion_1e6km": 206.7,
        "aphelion_1e6km":   249.3,
        "a_AU":    1.52371034,
        "e":       0.09339410,
        "i_deg":   1.84969,
        "Omega_deg": 49.55954,
        "omega_deg": -73.50317,   # Отрицательное значение — в статье тоже возможно
        "M0_deg":  19.39020,
        "L_deg":   355.433098,
        "varpi_deg": 336.04084,
    },
}

# --- Константы ---
G_const = 6.67430e-11         # м^3 кг^-1 с^-2 (gravitational constant)
M_sun = 1.98847e30           # кг (solar mass)
mu_sun = G_const * M_sun      # м^3 с^-2 (standard gravitational parameter)
day_to_sec = 86400.0          # секунд в сутках

print("\nКонстанты:")
print(f"  G = {G_const} м^3/(кг·с^2)")
print(f"  M_sun = {M_sun} кг")
print(f"  mu = G*M_sun = {mu_sun:.6e} м^3/с^2")
print(f"  1 AU = {AU} км")

# --- Расчёт для каждой планеты ---
print("\n" + "-" * 80)

for name, p in planets.items():
    print(f"\n{'=' * 80}")
    print(f"  {name}")
    print(f"{'=' * 80}")

    # --- Кеплеровские параметры ---
    a_AU = p["a_AU"]
    a_km = a_AU * AU
    a_m = a_km * 1e3
    e = p["e"]
    i_rad = np.radians(p["i_deg"])
    i_deg = p["i_deg"]
    Omega_deg = p["Omega_deg"]
    Omega_rad = np.radians(Omega_deg)
    omega_deg = p["omega_deg"]
    omega_rad = np.radians(omega_deg)
    M0_deg = p["M0_deg"]
    M0_rad = np.radians(M0_deg)
    varpi_deg = p["varpi_deg"]
    L_deg = p["L_deg"]

    # --- Производные величины ---
    # Малая полуось (semi-minor axis): b = a * sqrt(1 - e^2)
    b_AU = a_AU * np.sqrt(1 - e**2)
    b_km = b_AU * AU
    # Фокальный параметр (semi-latus rectum): p = a * (1 - e^2)
    p_AU = a_AU * (1 - e**2)
    p_km = p_AU * AU
    # Перицентр (perihelion distance): q = a * (1 - e)
    q_AU = a_AU * (1 - e)
    q_km = q_AU * AU
    # Апоцентр (aphelion distance): Q = a * (1 + e)
    Q_AU = a_AU * (1 + e)
    Q_km = Q_AU * AU
    # Период (orbital period) из третьего закона Кеплера
    T_sec = 2 * np.pi * np.sqrt(a_m**3 / mu_sun)
    T_days = T_sec / day_to_sec
    # Среднее движение (mean motion): n = 2π / T
    n_rad_s = 2 * np.pi / T_sec
    n_deg_day = 360.0 / T_days
    # Площадь эллипса
    S_ellipse = np.pi * a_km * b_km

    print(f"\n  --- Кеплеровские элементы (Keplerian elements) ---")
    print(f"  a   = {a_AU:.8f} AU = {a_km:.2f} км   (Semi-major axis / Большая полуось)")
    print(f"  e   = {e:.8f}                  (Eccentricity / Эксцентриситет)")
    print(f"  i   = {i_deg:.5f}°              (Inclination / Наклонение)")
    print(f"  Ω   = {Omega_deg:.5f}°           (Longitude of ascending node / Долгота восходящего узла)")
    print(f"  ω   = {omega_deg:.5f}°           (Argument of perihelion / Аргумент перигелия)")
    print(f"  M₀  = {M0_deg:.5f}°           (Mean anomaly at epoch / Средняя аномалия в эпоху)")

    print(f"\n  --- Производные величины (Derived quantities) ---")
    print(f"  b   = {b_AU:.8f} AU = {b_km:.2f} км   (Semi-minor axis / Малая полуось)")
    print(f"  p   = {p_AU:.8f} AU = {p_km:.2f} км   (Semi-latus rectum / Фокальный параметр)")
    print(f"  q   = {q_AU:.8f} AU = {q_km:.2f} км   (Perihelion distance / Перигелий)")
    print(f"  Q   = {Q_AU:.8f} AU = {Q_km:.2f} км   (Aphelion distance / Афелий)")
    print(f"  T   = {T_sec:.2f} с = {T_days:.2f} дней     (Orbital period / Период обращения)")
    print(f"  n   = {n_rad_s:.6e} рад/с = {n_deg_day:.6f} °/день  (Mean motion / Среднее движение)")
    print(f"  S   = {S_ellipse:.4e} км²    (Ellipse area / Площадь эллипса)")
    print(f"  ϖ   = {varpi_deg:.5f}°           (Longitude of perihelion / Долгота перигелия)")
    print(f"  L   = {L_deg:.5f}°           (Mean longitude / Средняя долгота)")

    # --- Решение уравнения Кеплера для эпохи J2000 ---
    # M = E - e*sin(E)  =>  находим E методом Ньютона
    M_rad = M0_rad
    E_rad = M_rad
    for _ in range(100):
        f = E_rad - e * np.sin(E_rad) - M_rad
        fp = 1 - e * np.cos(E_rad)
        dE = f / fp
        E_rad -= dE
        if abs(dE) < 1e-12:
            break
    E_deg = np.degrees(E_rad)

    # Истинная аномалия (true anomaly)
    nu_rad = 2 * np.arctan(np.sqrt((1 + e) / (1 - e)) * np.tan(E_rad / 2))
    # Нормализуем в [0, 2π)
    nu_rad = nu_rad % (2 * np.pi)
    nu_deg = np.degrees(nu_rad)

    # Радиус-вектор
    r_AU = a_AU * (1 - e * np.cos(E_rad))
    r_km = r_AU * AU

    print(f"\n  --- Решение уравнения Кеплера для J2000 ---")
    print(f"  M   = {M0_deg:.5f}°  (средняя аномалия / mean anomaly)")
    print(f"  E   = {E_deg:.5f}°  (эксцентрическая аномалия / eccentric anomaly)")
    print(f"  ν   = {nu_deg:.5f}°  (истинная аномалия / true anomaly)")
    print(f"  r   = {r_AU:.8f} AU = {r_km:.2f} км  (радиус-вектор / radius vector)")

    # --- Гелиоцентрические эклиптические координаты ---
    X = r_km * (np.cos(Omega_rad) * np.cos(omega_rad + nu_rad) -
                np.sin(Omega_rad) * np.sin(omega_rad + nu_rad) * np.cos(i_rad))
    Y = r_km * (np.sin(Omega_rad) * np.cos(omega_rad + nu_rad) +
                np.cos(Omega_rad) * np.sin(omega_rad + nu_rad) * np.cos(i_rad))
    Z = r_km * np.sin(omega_rad + nu_rad) * np.sin(i_rad)

    # Эклиптическая долгота и широта
    lam = np.degrees(np.arctan2(Y, X)) % 360
    beta = np.degrees(np.arctan2(Z, np.sqrt(X**2 + Y**2)))

    print(f"\n  --- Гелиоцентрические эклиптические координаты (J2000) ---")
    print(f"  X = {X:.2f} км")
    print(f"  Y = {Y:.2f} км")
    print(f"  Z = {Z:.2f} км")
    print(f"  λ (ecliptic longitude) = {lam:.5f}°  (эклиптическая долгота)")
    print(f"  β (ecliptic latitude)  = {beta:.5f}°  (эклиптическая широта)")


# ============================================================================
# ЧАСТЬ 3. ЗВУКОВЫЕ ПРОЯВЛЕНИЯ КЕПЛЕРОВСКИХ ПАРАМЕТРОВ
# ============================================================================

print("\n" + "=" * 80)
print("ЧАСТЬ 3. ЗВУКОВЫЕ ПРОЯВЛЕНИЯ КЕПЛЕРОВСКИХ ПАРАМЕТРОВ")
print("=" * 80)

print("""
Отображение шести кеплеровских параметров в звуковые характеристики:

  Параметр                    | Звуковое проявление
  ----------------------------|------------------------------------------
  a  — Большая полуось        | Базовая частота (высота ноты / pitch)
  e  — Эксцентриситет         | Глубина амплитудной модуляции (тремоло)
  i  — Наклонение             | Панорама / пространственное смещение (pan)
  Ω  — Долгота восх. узла     | Фазовый сдвиг (phase shift)
  ω  — Аргумент перигелия     | Тембральная окраска (добавочные гармоники)
  M₀ — Средняя аномалия       | Текущее положение в цикле модуляции
""")

# Базовая частота для Земли (эталон)
f_base_earth = 440.0  # A4 = 440 Гц

print(f"Эталонная частота Земли: f_Earth = {f_base_earth:.1f} Гц (A4)\n")

for name, p in planets.items():
    a_AU = p["a_AU"]
    e = p["e"]
    i_deg = p["i_deg"]
    Omega_deg = p["Omega_deg"]
    omega_deg = p["omega_deg"]
    M0_deg = p["M0_deg"]

    # --- 1. Базовая частота (pitch) ---
    # Отображение: f = f_earth * (a_earth / a_planet)
    # Чем больше a, тем ниже частота (как при удалении от источника)
    # Используем логарифмическую шкалу для большего диапазона
    f_base = f_base_earth * (1.0 / a_AU)

    # --- 2. Глубина амплитудной модуляции (тремоло) ---
    # Эксцентриситет определяет, насколько сильно меняется яркость/громкость
    # depth = e * 100%  (0 — нет тремоло, 1 — максимальное)
    tremolo_depth_pct = e * 100.0
    tremolo_rate = 1.0 / (p["orbital_period_d"] * day_to_sec)  # Гц

    # --- 3. Панорама (pan) ---
    # Наклонение определяет пространственное смещение звука
    # pan = sin(i) : от -1 (лево) до +1 (право)
    # Для малых углов pan ≈ i в радианах
    pan = np.sin(np.radians(i_deg))

    # --- 4. Фазовый сдвиг (phase shift) ---
    # Долгота восходящего узла задаёт фазовый сдвиг
    # phase = Omega / 360 * 2π (полный оборот = 2π)
    phase_shift_rad = np.radians(Omega_deg)
    phase_shift_deg = Omega_deg

    # --- 5. Тембральная окраска (добавочные гармоники) ---
    # Аргумент перигелия определяет, какие гармоники доминируют
    # Номер основной добавочной гармоники: N = 1 + round(|omega| / 30)
    # (пример: omega=0° → 1-я гармоника, omega=90° → 4-я, omega=180° → 7-я)
    n_harmonic = 1 + round(abs(omega_deg) / 30.0)

    # --- 6. Текущее положение в цикле модуляции ---
    # Средняя аномалия задаёт фазу внутри цикла
    mod_phase_rad = np.radians(M0_deg)
    mod_phase_deg = M0_deg

    print(f"  {'=' * 76}")
    print(f"  {name}")
    print(f"  {'=' * 76}")
    print(f"  a  → Базовая частота (pitch):           f = {f_base:.2f} Гц")
    print(f"      (a = {a_AU:.6f} AU, отношение к Земле: {1.0/a_AU:.4f})")
    print(f"  e  → Глубина тремоло (tremolo depth):    {tremolo_depth_pct:.2f}%")
    print(f"      Частота тремоло:                     {tremolo_rate:.6e} Гц (период = {p['orbital_period_d']:.1f} дней)")
    print(f"  i  → Панорама (pan):                    {pan:.6f}")
    print(f"      (i = {i_deg:.5f}°, sin(i) = {pan:.6f})")
    print(f"  Ω  → Фазовый сдвиг (phase shift):       {phase_shift_deg:.5f}° = {phase_shift_rad:.6f} рад")
    print(f"  ω  → Тембр / добавочная гармоника:       #{n_harmonic}")
    print(f"      (ω = {omega_deg:.5f}°, N = 1 + round(|ω|/30) = {n_harmonic})")
    print(f"  M₀ → Положение в цикле модуляции:        {mod_phase_deg:.5f}° = {mod_phase_rad:.6f} рад")
    print()

# --- Сводная таблица ---
print("\n" + "=" * 80)
print("СВОДНАЯ ТАБЛИЦА ЗВУКОВЫХ ПАРАМЕТРОВ")
print("=" * 80)
print(f"{'Планета':<22} {'f, Гц':>10} {'тремоло,%':>10} {'pan':>10} {'фаза,°':>10} {'гарм.':>8} {'M₀,°':>10}")
print("-" * 80)
for name, p in planets.items():
    a_AU = p["a_AU"]
    e = p["e"]
    i_deg = p["i_deg"]
    Omega_deg = p["Omega_deg"]
    omega_deg = p["omega_deg"]
    M0_deg = p["M0_deg"]

    f_base = f_base_earth * (1.0 / a_AU)
    tremolo = e * 100.0
    pan = np.sin(np.radians(i_deg))
    n_harm = 1 + round(abs(omega_deg) / 30.0)

    short_name = name.split("(")[0].strip()
    print(f"{short_name:<22} {f_base:>10.2f} {tremolo:>10.2f} {pan:>10.6f} {Omega_deg:>10.5f} {n_harm:>8d} {M0_deg:>10.5f}")

print("\n" + "=" * 80)
print("КОНЕЦ РАСЧЁТА")
print("=" * 80)
