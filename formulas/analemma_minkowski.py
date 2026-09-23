#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расчёт положений небесных тел в 4-мерном пространстве-времени
с метрикой Минковского.

Базируется на классических кеплеровых формулах, переведённых
в 4-мерный формализм. Включает релятивистскую поправку к уравнению
орбиты и прецессию перигелия Меркурия.

Требования: sympy, galgebra
"""

from sympy.abc import x, y, z
from sympy import (
    var, symbols, sin, cos, sqrt, exp, Matrix, Symbol, Function,
    I, eye, simplify, latex, expand, solve, Eq, pi, diff, atan,
    Rational, oo, trigsimp, collect, series
)

from galgebra.printer import Format, xpdf
from galgebra.mv import Mv
from galgebra.ga import Ga

############### Инициализация ##############
Format()

##########################################################################
# 4-МЕРНОЕ ПРОСТРАНСТВО-ВРЕМЯ С МЕТРИКОЙ МИНКОВСКОГО
#
# Метрика:  g = diag(+1, -1, -1, -1)
# Координаты: x^mu = (c*t, x, y, z)
#
# Переформулируем классические формулы Кеплера в 4-мерный формализм
# и выведем релятивистскую поправку к уравнению орбиты.
##########################################################################

############################
# 0. Фундаментальные константы и метрика
############################

c = Symbol('c', positive=True)       # скорость света
t_sym, T_sym = symbols('t T', real=True)
tau = Symbol('tau', real=True)        # собственное время

m1, m2 = symbols('m_1 m_2', positive=True)
G_const = Symbol('G', positive=True)  # гравитационная постоянная
R_sym = Symbol('R', positive=True)
M_sun = Symbol('M_{sun}', positive=True)

# Метрика Минковского
g_minkowski = eye(4)
g_minkowski[1,1] = -1
g_minkowski[2,2] = -1
g_minkowski[3,3] = -1

print("=" * 60)
print("0. Метрика Минковского:")
print("g_mu_nu = diag(+1, -1, -1, -1)")
print(latex(g_minkowski))
print()

############################
# 1. 4-позиция
############################

# x^mu = (c*t, r*cos(phi), r*sin(phi), 0)  — плоская орбита в плоскости xy
r_sym = Symbol('r', positive=True)
phi_sym = Symbol('phi', real=True)

x_mu = Matrix([
    c * t_sym,
    r_sym * cos(phi_sym),
    r_sym * sin(phi_sym),
    0
])

print("=" * 60)
print("1. 4-позиция:")
print("x^mu =", latex(x_mu))
print()

############################
# 2. Интервал и метрическое соотношение
############################

# ds^2 = g_mu_nu * dx^mu * dx^nu = c^2*dt^2 - dr^2 - r^2*dphi^2
# В полярных координатах на плоскости:
# ds^2 = c^2 dt^2 - dr^2 - r^2 dphi^2

ds2 = Eq(Symbol('ds^2'), c**2 * Symbol('dt^2') - Symbol('dr^2') - r_sym**2 * Symbol('dphi^2'))

print("2. Интервал в полярных координатах (плоская орбита):")
print(latex(ds2))
print()

############################
# 3. 4-скорость
############################

# u^mu = dx^mu / dtau = gamma * (c, v_r, v_phi, 0)
# где gamma = dt/dtau = 1/sqrt(1 - v^2/c^2)

gamma = Symbol('gamma', positive=True)  # лоренц-фактор
v_r = Symbol('v_r', real=True)          # радиальная скорость
v_phi = Symbol('v_phi', real=True)       # азимутальная скорость

u_mu = Matrix([
    gamma * c,
    gamma * v_r,
    gamma * v_phi,
    0
])

# Норма 4-скорости: g_mu_nu * u^mu * u^nu = c^2
u_norm = Eq(Symbol('g_mu_nu u^mu u^nu'), c**2)
u_norm_explicit = Eq(
    gamma**2 * c**2 - gamma**2 * v_r**2 - gamma**2 * v_phi**2,
    c**2
)
u_norm_simplified = Eq(gamma, 1 / sqrt(1 - (v_r**2 + v_phi**2) / c**2))

print("3. 4-скорость:")
print("u^mu =", latex(u_mu))
print("Норма:", latex(u_norm))
print("Раскрывая:", latex(u_norm_explicit))
print("Откуда gamma =", latex(u_norm_simplified))
print()

############################
# 4. 4-импульс
############################

# p^mu = m * u^mu = (E/c, p_vec)
# E = gamma * m * c^2  — полная энергия
# p_vec = gamma * m * v_vec — пространственный импульс

m = Symbol('m', positive=True)  # масса планеты

p_mu = m * u_mu
E_total = gamma * m * c**2

print("4. 4-импульс:")
print("p^mu = m * u^mu =", latex(p_mu))
print("E = gamma * m * c^2 =", latex(E_total))
print("p^0 = E/c =", latex(E_total / c))
print()

############################
# 5. Закон всемирного тяготения в 4-мерном виде
############################

# В ньютоновском пределе сила:
#   F = -G * M * m / r^2 * e_r
# В 4-мерном формализме гравитация описывается через
# метрику пространства-времени. В слабом поле (приближение):
#   g_00 ≈ 1 + 2*Phi/c^2,  где Phi = -G*M/r

Phi_grav = -G_const * M_sun / r_sym
g00_weak = 1 + 2 * Phi_grav / c**2

F_gravity = G_const * M_sun * m / r_sym**2

print("5. Гравитация в 4-мерном формализме:")
print("Ньютоновская сила: F =", latex(F_gravity))
print("Слабое поле: g_00 ≈ 1 + 2*Phi/c^2 =", latex(g00_weak))
print("Phi =", latex(Phi_grav))
print()

############################
# 6. Сохранение 4-импульса и момент импульса
############################

# В 4-мерном виде момент импульса — антисимметричный тензор:
#   L_munu = x_mu * p_nu - x_nu * p_mu
# Аксиальный вектор (дуальный тензор):
#   L^i = epsilon^ijk * L_jk / 2  (пространственная часть)
# Для плоской орбиты (z=0) аксиальный вектор направлен вдоль z:
#   L_z = x * p_y - y * p_x = m * r^2 * dphi/dt * gamma

L_z = gamma * m * r_sym**2 * Symbol('dphi/dt')

# Классический аналог:
C_classical = r_sym**2 * Symbol('dphi/dt')

# Связь:
L_relativistic = Eq(Symbol('L_z'), gamma * m * Symbol('C'))
L_classical = Eq(Symbol('C'), r_sym**2 * Symbol('dphi/dt'))

print("6. Момент импульса:")
print("Тензор: L_munu = x_mu*p_nu - x_nu*p_mu")
print("Аксиальный вектор (z-компонента):")
print("L_z =", latex(L_z))
print("Классический аналог: C = r^2 * dphi/dt")
print("Связь:", latex(L_relativistic))
print()

############################
# 7. Секториальная скорость в 4-мерном виде
############################

# Классически: dS/dt = C/2 = r^2 * omega / 2
# В СТО: dS/dtau = gamma * r^2 * omega / 2

dS_dt = Eq(Symbol('dS/dt'), r_sym**2 * Symbol('omega') / 2)
dS_dtau = Eq(Symbol('dS/dtau'), gamma * r_sym**2 * Symbol('omega') / 2)

print("7. Секториальная скорость:")
print("Классическая:", latex(dS_dt))
print("Релятивистская (по собственному времени):", latex(dS_dtau))
print()

############################
# 8. Полярный базис в 4-мерном пространстве-времени
############################

# e_t = (1, 0, 0, 0)      — временной базисный вектор
# e_r = (0, cos(phi), sin(phi), 0)  — радиальный
# e_phi = (0, -sin(phi), cos(phi), 0) — азимутальный
# Метрика: e_t . e_t = +1, e_r . e_r = -1, e_phi . e_phi = -1

print("8. Полярный базис в пространстве-времени Минковского:")
print("e_t   = (1, 0, 0, 0)")
print("e_r   = (0, cos(phi), sin(phi), 0)")
print("e_phi = (0, -sin(phi), cos(phi), 0)")
print("e_t . e_t = +1,  e_r . e_r = -1,  e_phi . e_phi = -1")
print("Ортогональность: e_t . e_r = 0,  e_t . e_phi = 0,  e_r . e_phi = 0")
print()

############################
# 9. 4-ускорение
############################

# a^mu = du^mu / dtau
# Для движения в центральном поле:
# a^t = (gamma^3 / c) * (v_r * a_r + v_phi * a_phi)   [из условия a_mu u^mu = 0]
# a^r = gamma^2 * (d2r/dt2 - r*omega^2) + релятивистские поправки
# a^phi = ...

# Классическая радиальная составляющая:
a_radial_classical = Symbol('d2r/dt2') - r_sym * Symbol('omega')**2

# Релятивистская поправка к радиальному ускорению:
# a_r_rel = gamma^2 * (d2r/dt2 - r*omega^2) + (gamma^2 - 1) * v_r^2 / r
a_radial_rel = gamma**2 * (Symbol('d2r/dt2') - r_sym * Symbol('omega')**2)

print("9. 4-ускорение:")
print("Классическое радиальное: a_r =", latex(a_radial_classical))
print("Релятивистское (нулевой порядок по gamma^2): a_r ≈", latex(a_radial_rel))
print("Условие ортогональности: a_mu * u^mu = 0")
print()

############################
# 10. Уравнение движения и замена u = 1/r
############################

u_sym = Symbol('u', positive=True)
u_def = Eq(u_sym, 1 / r_sym)

# Классическое уравнение:
# d2u/dphi2 + u = mu / C^2
#
# Релятивистское уравнение (СТО, без GR):
# При учёте релятивистской массы m -> gamma*m,
# уравнение модифицируется:
# d2u/dphi2 + u = (mu / C^2) * (1 + 3 * (v^2/c^2) + ...)
#
# В ОТО (шварцшильдовская метрика):
# d2u/dphi2 + u = mu / C^2 + 3 * G*M / c^2 * u^2
#
# где mu = G * M_sun

mu_grav = G_const * M_sun

# Параметр релятивистской поправки:
# alpha_rel = 3 * G * M / c^2
alpha_rel = 3 * G_const * M_sun / c**2

orbit_ode_classical = Eq(
    Symbol('d2u/dphi2') + u_sym,
    mu_grav / Symbol('C')**2
)

orbit_ode_rel = Eq(
    Symbol('d2u/dphi2') + u_sym,
    mu_grav / Symbol('C')**2 + alpha_rel * u_sym**2
)

print("10. Уравнение орбиты:")
print("Классическое:", latex(orbit_ode_classical))
print("Релятивистское (ОТО):", latex(orbit_ode_rel))
print("Параметр поправки: alpha_rel =", latex(alpha_rel))
print()

############################
# 11. Решение релятивистского уравнения орбиты
############################

# Решение методом возмущений:
# u = u_0 + u_1
# где u_0 = (1/p)(1 + e*cos(phi))  — классическое решение
# u_1 — поправка первого порядка

p_sym = Symbol('p', positive=True)
e_sym = Symbol('e', positive=True)

u_0 = (1 / p_sym) * (1 + e_sym * cos(phi_sym))
u_1_correction = (alpha_rel / p_sym) * e_sym * phi_sym * sin(phi_sym)

# Полное решение:
u_total = u_0 + u_1_correction

# Это даёт смещение перигелия:
# Delta_phi = 2 * pi * alpha_rel / p = 2 * pi * 3 * G * M / (c^2 * p)
# Или через a и e:  p = a(1-e^2)
# Delta_phi = 6 * pi * G * M / (c^2 * a * (1 - e^2))

a_sym = Symbol('a', positive=True)
Delta_phi_per_orbit = 6 * pi * G_const * M_sun / (c**2 * a_sym * (1 - e_sym**2))

print("11. Решение (метод возмущений):")
print("u_0 =", latex(u_0))
print("u_1 =", latex(u_1_correction))
print("u =", latex(u_total))
print()
print("Смещение перигелия за один оборот:")
print("Delta_phi =", latex(Delta_phi_per_orbit))
print()

############################
# 12. Кеплерова орбита в 4-мерном виде
############################

# Радиус-вектор в 4-мерном виде:
# x^mu = (c*t, r*cos(phi), r*sin(phi), 0)
# r = p / (1 + e*cos(phi))  — классическая форма
# С релятивистской поправкой:
# r ≈ p / (1 + e*cos(phi*(1 - delta)))  где delta = alpha_rel/p

delta_precession = alpha_rel / p_sym

r_orbit_classical = p_sym / (1 + e_sym * cos(phi_sym))
r_orbit_rel = p_sym / (1 + e_sym * cos(phi_sym * (1 - delta_precession)))

print("12. Кеплерова орбита в 4-мерном виде:")
print("Классическая: r =", latex(r_orbit_classical))
print("Релятивистская: r ≈", latex(r_orbit_rel))
print("Параметр прецессии: delta =", latex(delta_precession))
print()

############################
# 13. Уравнение Кеплера (сохраняется)
############################

E_sym = Symbol('E', real=True)        # эксцентрическая аномалия
M_sym = Symbol('M', real=True)        # средняя аномалия

kepler_eq = Eq(M_sym, E_sym - e_sym * sin(E_sym))

r_from_E = Eq(r_sym, a_sym * (1 - e_sym * cos(E_sym)))

print("13. Уравнение Кеплера (не меняется в СТО):")
print(latex(kepler_eq))
print("r =", latex(r_from_E))
print()

############################
# 14. Параметры эллипса
############################

b_sym = Symbol('b', positive=True)

ellipse_axes = Eq(b_sym / a_sym, sqrt(1 - e_sym**2))
ellipse_focal = Eq(p_sym, b_sym**2 / a_sym)
ellipse_area = Eq(Symbol('S'), pi * a_sym * b_sym)

print("14. Параметры эллипса:")
print("b/a =", latex(ellipse_axes))
print("p =", latex(ellipse_focal))
print("S =", latex(ellipse_area))
print()

############################
# 15. Период обращения и среднее движение
############################

period = Eq(T_sym, 2 * pi * sqrt(a_sym**3 / mu_grav))
n_sym = Symbol('n', positive=True)
mean_motion = Eq(n_sym, sqrt(mu_grav / a_sym**3))

print("15. Период и среднее движение:")
print("T =", latex(period))
print("n =", latex(mean_motion))
print()

############################
# 16. Средняя аномалия
############################

M0 = Symbol('M_0', real=True)
mean_anomaly = Eq(M_sym, M0 + n_sym * t_sym)

print("16. Средняя аномалия:")
print(latex(mean_anomaly))
print()

############################
# 17. Связь эксцентрической и истинной аномалии
############################

varphi = Symbol('varphi', real=True)

cos_true = Eq(cos(varphi), (cos(E_sym) - e_sym) / (1 - e_sym * cos(E_sym)))
sin_true = Eq(sin(varphi), sqrt(1 - e_sym**2) * sin(E_sym) / (1 - e_sym * cos(E_sym)))
true_half = Eq(Symbol('tan(varphi/2)'),
               sqrt((1 + e_sym) / (1 - e_sym)) * Symbol('tan(E/2)'))

print("17. Связь аномалий:")
print("cos(varphi) =", latex(cos_true))
print("sin(varphi) =", latex(sin_true))
print("tan(varphi/2) =", latex(true_half))
print()

############################
# 18. АКСИАЛЬНЫЙ ВЕКТОР И ЕГО КОМПОНЕНТЫ
#     Движение перигелия Меркурия
############################

print("=" * 60)
print("18. АКСИАЛЬНЫЙ ВЕКТОР И ПРЕЦЕССИЯ ПЕРИГЕЛИЯ МЕРКУРИЯ")
print("=" * 60)
print()

# Аксиальный вектор момента импульса:
# L^z = gamma * m * C  (z-компонента)
# В 4-мерном виде: L_03 = x_0 * p_3 - x_3 * p_0 (временная компонента)
#                 L_12 = x_1 * p_2 - x_2 * p_1 (пространственная, = L_z)

L_12 = Symbol('L_{12}')
L_03 = Symbol('L_{03}')

print("Компоненты тензора момента импульса L_munu:")
print("L_12 = x_1*p_2 - x_2*p_1 =", latex(L_12), "  (пространственная, = L_z)")
print("L_03 = x_0*p_3 - x_3*p_0 =", latex(L_03), "  (временно-пространственная)")
print("Для плоской орбиты (z=0): L_12 = L_z, L_03 = 0")
print()

# ---- Параметры Меркурия ----
a_Mercury = Symbol('a_M', positive=True)  # большая полуось
e_Mercury = Symbol('e_M', positive=True)  # эксцентриситет
T_Mercury = Symbol('T_M', positive=True)   # период
N_orbits = Symbol('N', positive=True)       # число оборотов

# Прецессия перигелия за один оборот (ОТО):
Delta_phi_Mercury = 6 * pi * G_const * M_sun / (c**2 * a_Mercury * (1 - e_Mercury**2))

# Прецессия за N оборотов:
Delta_phi_total = N_orbits * Delta_phi_Mercury

# Прецессия за столетие:
# N_century = (100 лет) / T_Mercury
N_century = 100 * 365.25 / T_Mercury  # в годах, если T в годах

Delta_phi_century = N_century * Delta_phi_Mercury

print("Параметры Меркурия:")
print("a_M =", latex(a_Mercury), "  (большая полуось)")
print("e_M =", latex(e_Mercury), "  (эксцентриситет)")
print("T_M =", latex(T_Mercury), "  (период обращения)")
print()

print("Прецессия перигелия за один оборот:")
print("Delta_phi =", latex(Delta_phi_Mercury))
print()

print("Прецессия за N оборотов:")
print("Delta_phi_total =", latex(Delta_phi_total))
print()

print("Прецессия за столетие:")
print("N_century =", latex(N_century))
print("Delta_phi_century =", latex(Delta_phi_century))
print()

# ---- Численные значения для Меркурия ----
G_val = 6.674e-11       # м^3/(кг*с^2)
M_sun_val = 1.989e30    # кг
c_val = 2.998e8         # м/с
a_M_val = 5.791e10      # м
e_M_val = 0.2056
T_M_val = 87.969        # дней
T_M_sec = T_M_val * 86400  # секунд

Delta_phi_val = 6 * pi * G_val * M_sun_val / (c_val**2 * a_M_val * (1 - e_M_val**2))

# В секундах дуги:
Delta_phi_arcsec = Delta_phi_val * (180 / pi) * 3600

# За столетие:
N_century_val = 100 * 365.25 / T_M_val
Delta_century_arcsec = N_century_val * Delta_phi_arcsec

print("Численные значения:")
print(f"G = {G_val} м^3/(кг*с^2)")
print(f"M_sun = {M_sun_val} кг")
print(f"c = {c_val} м/с")
print(f"a_Mercury = {a_M_val} м")
print(f"e_Mercury = {e_M_val}")
print(f"T_Mercury = {T_M_val} дней = {T_M_sec:.0f} с")
print()
print(f"Delta_phi (1 оборот) = {Delta_phi_val:.6e} рад")
print(f"Delta_phi (1 оборот) = {Delta_phi_arcsec:.4f} угл. сек.")
print(f"N (за столетие) = {N_century_val:.2f} оборотов")
print(f"Delta_phi (за столетие) = {Delta_century_arcsec:.2f} угл. сек.")
print(f"Наблюдаемое значение: 43.0 угл. сек/столетие")
print()

############################
# 19. ДВИЖЕНИЕ МЕРКУРИЯ В ТОЧКЕ ПЕРИГЕЛИЯ
############################

print("=" * 60)
print("19. ДВИЖЕНИЕ МЕРКУРИЯ В ПЕРИГЕЛИИ")
print("=" * 60)
print()

# В перигелии: phi = 0, r = a*(1 - e)
r_perihelion = a_Mercury * (1 - e_Mercury)
r_perihelion_eq = Eq(Symbol('r_peri'), r_perihelion)

print("Радиус в перигелии:")
print(latex(r_perihelion_eq))
print()

# 4-скорость в перигелии:
# v_r = 0 (радиальная скорость равна нулю в перигелии)
# v_phi = C / r_peri = sqrt(mu * (1+e) / (a*(1-e))) / (1-e) ...
# Из сохранения момента: r^2 * dphi/dt = C = sqrt(mu * a * (1 - e^2))
# v_phi(peri) = C / r_peri = sqrt(mu * (1+e) / (a * (1-e)))

v_phi_peri = sqrt(mu_grav * (1 + e_Mercury) / (a_Mercury * (1 - e_Mercury)))
v_r_peri = 0

# Лоренц-фактор в перигелии:
gamma_peri = 1 / sqrt(1 - v_phi_peri**2 / c**2)

# 4-скорость в перигелии:
u_perihelion = Matrix([
    gamma_peri * c,
    0,
    gamma_peri * v_phi_peri,
    0
])

print("4-скорость в перигелии:")
print("v_r = 0 (в перигелии радиальная скорость = 0)")
print("v_phi =", latex(v_phi_peri))
print("gamma_peri =", latex(gamma_peri))
print("u^mu(peri) =", latex(u_perihelion))
print()

# 4-импульс в перигелии:
p_perihelion = m * u_perihelion
E_perihelion = gamma_peri * m * c**2

print("4-импульс в перигелии:")
print("p^mu =", latex(p_perihelion))
print("E =", latex(E_perihelion))
print()

# Аксиальный вектор (z-компонента) в перигелии:
L_z_peri = gamma_peri * m * r_perihelion * v_phi_peri

print("Аксиальный вектор (z-компонента) в перигелии:")
print("L_z =", latex(L_z_peri))
print()

# Численные значения в перигелии:
v_phi_peri_val = sqrt(G_val * M_sun_val * (1 + e_M_val) / (a_M_val * (1 - e_M_val)))
gamma_peri_val = 1 / sqrt(1 - v_phi_peri_val**2 / c_val**2)
r_peri_val = a_M_val * (1 - e_M_val)

print("Численные значения в перигелии:")
print(f"r_peri = {r_peri_val:.4e} м")
print(f"v_phi_peri = {v_phi_peri_val:.2f} м/с")
print(f"v_phi_peri / c = {v_phi_peri_val / c_val:.6e}")
print(f"gamma_peri = {gamma_peri_val:.10f}")
print(f"gamma_peri - 1 = {gamma_peri_val - 1:.6e}")
print()

############################
# 20. Угловая скорость прецессии
############################

# Омега прецессии = Delta_phi / T
Omega_prec = Delta_phi_Mercury / T_Mercury

print("20. Угловая скорость прецессии перигелия:")
print("Omega_prec = Delta_phi / T =", latex(Omega_prec))
print()

############################
# 21. Геометрическая алгебра в пространстве Минковского
############################

print("=" * 60)
print("21. ГЕОМЕТРИЧЕСКАЯ АЛГЕБРА В ПРОСТРАНСТВЕ МИНКОВСКОГО")
print("=" * 60)
print()

# Создаём пространство с метрикой Минковского
vars_st = symbols('t x y z')
xyz_space, *basis = Ga.build('gamma*t|x|y|z', g=[1, -1, -1, -1], coords=vars_st)

g0_vector = basis[0]
I_mv = xyz_space.i

print("Базис геометрической алгебры:")
print("gamma_t =", g0_vector)
print("I (псевдоскаляр) =", I_mv)
print()

# 4-вектор позиции как мультвектор
try:
    r_mv = xyz_space.mv('r', 'vector', f=True)
    print("4-вектор позиции r =", r_mv)
except Exception as ex:
    print(f"(создание мультвектора r: {ex})")

# Бивектор момента импульса: L = r ^ p
try:
    p_mv = xyz_space.mv('p', 'vector', f=True)
    L_bivector = r_mv ^ p_mv
    print("Бивектор момента импульса: L = r ^ p =", L_bivector)
except Exception as ex:
    print(f"(бивектор момента: {ex})")

# Аксиальный вектор как дуальный бивектору:
try:
    L_axial = -I_mv * (r_mv ^ p_mv)
    print("Аксиальный вектор (дуальный): L_axial = -I * (r ^ p) =", L_axial)
except Exception as ex:
    print(f"(аксиальный вектор: {ex})")

print()

############################
# 22. ИТОГОВАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ РАСЧЁТА В 4-МЕРНОМ ВИДЕ
############################

print("=" * 60)
print("22. ИТОГОВАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ (4-МЕРНЫЙ ФОРМАЛИЗМ)")
print("=" * 60)
print()
print("1) n = sqrt(mu / a^3),  mu = G * M_sun")
print("2) M = M_0 + n * (t - t_0)")
print("3) Решить уравнение Кеплера: M = E - e*sin(E) -> E")
print("4) r = a * (1 - e * cos(E))")
print("5) tan(varphi/2) = sqrt((1+e)/(1-e)) * tan(E/2) -> varphi")
print("6) x^mu = (c*t, r*cos(varphi), r*sin(varphi), 0)")
print("7) u^mu = gamma * (c, v_r, v_phi, 0)")
print("8) p^mu = m * u^mu")
print("9) L_munu = x_mu * p_nu - x_nu * p_mu  (тензор момента)")
print("10) L_axial = -I * (r ^ p)  (аксиальный вектор)")
print("11) Прецессия перигелия:")
print("    Delta_phi = 6*pi*G*M / (c^2 * a * (1 - e^2))  за оборот")
print("    Delta_phi_century = N * Delta_phi  за столетие")
print("=" * 60)

############################
# 23. Генерация PDF
############################

xpdf(paper=(6, 7))
