from sympy.abc import x, y, z
from sympy.abc import i, j, k
from sympy.abc import r, n
from sympy.abc import alpha, beta, gamma
from sympy.abc import mu, epsilon

# Из sympy импортируем необходимые функции.
from sympy import (
    var, symbols, sin, cos, sqrt, exp, Matrix, Symbol, Function,
    I, eye, simplify, latex, expand, solve, Eq, pi, diff, atan
)

# Геометрическая алгебра и генерация PDF/TeX.
from galgebra.printer import Format, xpdf
from galgebra.mv import Mv
from galgebra.ga import Ga

############### Geometric Algebra & Format of out pdf file ##############

# Инициализация принтера формул.
Format()

##########################################################################
# РАСЧЕТ ПОЛОЖЕНИЯ НЕБЕСНЫХ ТЕЛ
#
# Формулы собраны по статье:
# «Расчет положения небесных тел».
#
# Модель статьи:
#   - задача двух тел;
#   - неподвижное Солнце;
#   - центральное ньютоновское поле;
#   - кеплерова орбита;
#   - средняя, эксцентрическая и истинная аномалии.
##########################################################################


############################
# 1. Основные обозначения
############################

t, T = symbols('t T', real=True)
m1, m2 = symbols('m_1 m_2', positive=True)
R = Symbol('R', positive=True)
G = Symbol('G', positive=True)

r = Symbol('r', positive=True)
phi = Symbol('phi', real=True)
omega = Symbol('omega', real=True)
mu = Symbol('mu', positive=True)
C = Symbol('C', positive=True)

a = Symbol('a', positive=True)
b = Symbol('b', positive=True)
e = Symbol('e', positive=True)
p = Symbol('p', positive=True)

E = Symbol('E', real=True)       # эксцентрическая аномалия
M = Symbol('M', real=True)       # средняя аномалия
varphi = Symbol('varphi', real=True)  # истинная аномалия
phi0 = Symbol('phi_0', real=True)

L = Symbol('L', real=True)       # средняя долгота
w = Symbol('w', real=True)       # долгота перигея

r_dot = Symbol('r_dot')
r_ddot = Symbol('r_ddot')
u = Symbol('u', positive=True)


############################
# 2. Закон всемирного тяготения
############################

F_gravity = G * m1 * m2 / R**2

print("1. Закон всемирного тяготения:")
print("F =", F_gravity)
print(latex(Eq(Symbol('F'), F_gravity)))
print()


############################
# 3. Импульс и второй закон Ньютона
############################

v = Symbol('v')
F = Symbol('F')

momentum = m2 * v
newton_momentum = Eq(Symbol('d_p/dt'), F)
newton_force = Eq(F, m2 * Symbol('a'))

print("2. Импульс:")
print("p =", momentum)
print(latex(Eq(Symbol('p'), momentum)))

print("Второй закон Ньютона:")
print("dp/dt =", F)
print("F =", m2, "* dv/dt")
print("F =", m2, "* a")
print()


############################
# 4. Сохранение момента импульса
############################

# Векторные выражения записываются символически.
r_vec = Symbol('r_vec')
p_vec = Symbol('p_vec')
v_vec = Symbol('v_vec')
F_vec = Symbol('F_vec')

angular_momentum = Symbol('[r,p]')
angular_momentum_const = Eq(angular_momentum, Symbol('const'))

r_cross_v = Symbol('[r,v]')
r_cross_v_const = Eq(r_cross_v, Symbol('const'))

print("3. Закон сохранения момента импульса:")
print("[r,p] = const")
print("[r,v] = const")
print()


############################
# 5. Секториальная скорость
############################

dS_dt = Eq(
    Symbol('dS/dt'),
    Symbol('1/2') * Symbol('|[r,v]|')
)

# В скалярной записи статьи:
dS_dt_explicit = Eq(
    Symbol('dS/dt'),
    r**2 * omega / 2
)

C_definition = Eq(C, r**2 * omega)

print("4. Секториальная скорость:")
print("dS/dt = 1/2 |[r,v]|")
print("dS/dt =", r**2 * omega / 2)
print("C =", r**2 * omega)
print()


############################
# 6. Полярный базис
############################

# r_vec = r * e_r
# v_vec = dr/dt * e_r + r * de_r/dt
#
# de_r/dt = omega * e_phi

er = Symbol('e_r')
ephi = Symbol('e_phi')
ez = Symbol('e_z')

v_polar = (
    Symbol('dr/dt') * er
    + r * omega * ephi
)

print("5. Радиус-вектор и скорость:")
print("r_vec = r * e_r")
print("v_vec =", v_polar)
print("de_r/dt = omega * e_phi")
print()


############################
# 7. Векторное произведение r x v
############################

r_cross_v_polar = r**2 * omega * ez
r_cross_v_module = r**2 * omega

print("6. Векторное произведение:")
print("[r,v] =", r_cross_v_polar)
print("|[r,v]| =", r_cross_v_module)
print("r^2 * omega = C")
print()


############################
# 8. Ускорение в полярных координатах
############################

a_radial = (
    Symbol('d2r/dt2') - r * omega**2
)

acceleration_equation = Eq(
    Symbol('a'),
    a_radial * er
)

print("7. Радиальная составляющая ускорения:")
print("a =", a_radial, "* e_r")
print()


############################
# 9. Гравитационное ускорение
############################

# После сокращения массы планеты:
#
#     a = -e_r * mu/r^2
#
# где mu = G*M_sun.

mu = Symbol('mu', positive=True)

gravity_acceleration = Eq(
    Symbol('a'),
    -mu / r**2
)

print("8. Гравитационное ускорение:")
print("a = -mu/r^2")
print("mu = G * M_sun")
print()


############################
# 10. Замена u = 1/r
############################

u = Symbol('u', positive=True)

u_definition = Eq(u, 1/r)

print("9. Замена переменной:")
print("u = 1/r")
print()


############################
# 11. Производная r через u и phi
############################

du_dphi = Symbol('du/dphi')

dr_dt = Eq(
    Symbol('dr/dt'),
    -C * du_dphi
)

print("10. Первая производная:")
print("dr/dt = -C * du/dphi")
print()


############################
# 12. Вторая производная
############################

d2u_dphi2 = Symbol('d2u/dphi2')

d2r_dt2 = Eq(
    Symbol('d2r/dt2'),
    -C**2 * u**2 * d2u_dphi2
)

print("11. Вторая производная:")
print("d2r/dt2 = -C^2*u^2*d2u/dphi2")
print()


############################
# 13. Дифференциальное уравнение орбиты
############################

orbit_ode = Eq(
    d2u_dphi2 + u,
    mu / C**2
)

print("12. Дифференциальное уравнение орбиты:")
print(orbit_ode)
print(latex(orbit_ode))
print()


############################
# 14. Решение дифференциального уравнения
############################

A = Symbol('A', real=True)

u_homogeneous = Eq(
    u,
    A * cos(phi + phi0)
)

u_particular = Eq(
    u,
    mu / C**2
)

u_general = Eq(
    u,
    A * cos(phi + phi0) + mu / C**2
)

print("13. Общее решение:")
print(u_general)
print(latex(u_general))
print()


############################
# 15. Орбита в полярных координатах
############################

# Вводим:
#
#     p = C^2/mu
#     e = A*p
#
# Тогда:
#
#     r = p/(1 + e*cos(phi + phi0))

p_definition = Eq(p, C**2 / mu)
e_definition = Eq(e, A * p)

orbit_polar_general = Eq(
    r,
    p / (1 + e * cos(phi + phi0))
)

print("14. Фокальный параметр:")
print(p_definition)
print("Эксцентриситет:")
print(e_definition)

print("Уравнение орбиты:")
print(orbit_polar_general)
print(latex(orbit_polar_general))
print()


############################
# 16. Общепринятая ориентация эллипса
############################

orbit_polar = Eq(
    r,
    p / (1 + e * cos(phi))
)

print("15. Орбита при phi_0 = 0:")
print(orbit_polar)
print(latex(orbit_polar))
print()


############################
# 17. Параметры эллипса
############################

ellipse_area = Eq(
    Symbol('S'),
    pi * a * b
)

ellipse_axes = Eq(
    b / a,
    sqrt(1 - e**2)
)

ellipse_eccentricity = Eq(
    e,
    sqrt(1 - b**2 / a**2)
)

ellipse_focal_parameter = Eq(
    p,
    b**2 / a
)

print("16. Площадь эллипса:")
print(ellipse_area)

print("Отношение полуосей:")
print(ellipse_axes)

print("Эксцентриситет:")
print(ellipse_eccentricity)

print("Фокальный параметр:")
print(ellipse_focal_parameter)
print()


############################
# 18. Период обращения
############################

# Из:
#     dS/dt = C/2
#
# и площади эллипса:
#     pi*a*b = C*T/2
#
# с учетом:
#     b^2 = p*a
#     p = C^2/mu
#
# получаем:

period = Eq(
    T,
    2 * pi * sqrt(a**3 / mu)
)

print("17. Период обращения:")
print(period)
print(latex(period))
print()


############################
# 19. Среднее движение
############################

mean_motion = Eq(
    n,
    2 * pi / T
)

mean_motion_reduced = Eq(
    n,
    sqrt(mu / a**3)
)

print("18. Среднее движение:")
print(mean_motion)
print(mean_motion_reduced)
print()


############################
# 20. Средняя аномалия
############################

M0 = Symbol('M_0', real=True)

mean_anomaly = Eq(
    M,
    M0 + n * t
)

print("19. Средняя аномалия:")
print(mean_anomaly)
print(latex(mean_anomaly))
print()


############################
# 21. Площадь сектора эллипса
############################

delta_t = Symbol('Delta_t', positive=True)

sector_elliptic = Eq(
    Symbol('S_OPS'),
    delta_t * sqrt(a * mu * (1 - e**2)) / 2
)

sector_transformed = Eq(
    Symbol('S_OPT'),
    delta_t * sqrt(a * mu) / 2
)

print("20. Площадь сектора:")
print(sector_elliptic)
print(sector_transformed)
print()


############################
# 22. Сектор круга и уравнение Кеплера
############################

sector_circle_minus_triangle = Eq(
    Symbol('S_OPT'),
    a**2 / 2 * (E - e * sin(E))
)

kepler_equation = Eq(
    M,
    E - e * sin(E)
)

print("21. Сектор круга минус треугольник:")
print(sector_circle_minus_triangle)

print("Уравнение Кеплера:")
print(kepler_equation)
print(latex(kepler_equation))
print()


############################
# 23. Связь эксцентрической и истинной аномалии
############################

x_E = Eq(
    Symbol('x'),
    a * (cos(E) - e)
)

y_E = Eq(
    Symbol('y'),
    a * sqrt(1 - e**2) * sin(E)
)

x_phi = Eq(
    Symbol('x'),
    r * cos(varphi)
)

y_phi = Eq(
    Symbol('y'),
    r * sin(varphi)
)

radius_from_E = Eq(
    r,
    a * (1 - e * cos(E))
)

cos_true_anomaly = Eq(
    cos(varphi),
    (cos(E) - e) / (1 - e * cos(E))
)

sin_true_anomaly = Eq(
    sin(varphi),
    sqrt(1 - e**2) * sin(E) / (1 - e * cos(E))
)

print("22. Параметрические координаты эллипса:")
print(x_E)
print(y_E)

print("Полярные координаты:")
print(x_phi)
print(y_phi)

print("Радиус:")
print(radius_from_E)

print("cos(varphi):")
print(cos_true_anomaly)

print("sin(varphi):")
print(sin_true_anomaly)
print()


############################
# 24. Истинная аномалия через E
############################

true_anomaly_half_angle = Eq(
    Symbol('tan(varphi/2)'),
    sqrt((1 + e) / (1 - e)) * Symbol('tan(E/2)')
)

# Форма для непосредственного вычисления:
true_anomaly = Eq(
    varphi,
    2 * atan(sqrt((1 + e) / (1 - e)) * Symbol('tan(E/2)'))
)

print("23. Связь истинной и эксцентрической аномалии:")
print("tan(varphi/2) = sqrt((1+e)/(1-e)) * tan(E/2)")
print(latex(true_anomaly_half_angle))
print()


############################
# 25. Средняя долгота и долгота перигея
############################

# По статье:
#
#     M = L - w
#
# где L — средняя долгота, w — долгота перигея.

mean_longitude_relation = Eq(
    M,
    L - w
)

print("24. Средняя долгота:")
print(mean_longitude_relation)
print(latex(mean_longitude_relation))
print()


############################
# 26. Средняя аномалия на произвольный момент времени
############################

t_J2000 = Symbol('t_J2000', real=True)
M_J2000 = Symbol('M_J2000', real=True)

M_J2000_relation = Eq(
    M_J2000,
    L - w
)

M_time = Eq(
    M,
    M_J2000 + n * (t - t_J2000)
)

print("25. Средняя аномалия на эпоху J2000:")
print(M_J2000_relation)

print("Средняя аномалия на произвольное время:")
print(M_time)
print(latex(M_time))
print()


############################
# 27. Итоговая последовательность расчета
############################

print("============================================================")
print("ИТОГОВАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ")
print("============================================================")
print("1) n = sqrt(mu/a^3)")
print("2) M = M_J2000 + n*(t - t_J2000)")
print("3) Решить M = E - e*sin(E) относительно E")
print("4) r = a*(1 - e*cos(E))")
print("5) tan(phi/2) = sqrt((1+e)/(1-e))*tan(E/2)")
print("6) Получить heliocentric position из r и phi")
print("============================================================")


############################
# 28. Минимальный вычислительный блок
############################

# Символьная форма Kepler equation.
M_input = Symbol('M_input', real=True)
E_solution = Symbol('E_solution', real=True)

kepler_equation_for_solver = Eq(
    M_input,
    E_solution - e * sin(E_solution)
)

print("Уравнение Кеплера для численного решения:")
print(kepler_equation_for_solver)
print()


############################
# 29. Геометрическая алгебра
############################

# Небольшая проверка ортонормированного базиса в стиле исходного скрипта.

vars = symbols('t x y z')

xyz_space, *basis = Ga.build(
    'gamma*t|x|y|z',
    g=[1, -1, -1, -1],
    coords=vars
)

g0_vector = basis[0]
I_mv = xyz_space.i

# Временной и пространственный базис задаются самой Ga.
print("Geometric Algebra basis:")
print("gamma_t =", g0_vector)
print("I =", I_mv)


############################
# 30. Генерация итогового PDF/TeX документа
############################

xpdf(paper=(6, 7))
