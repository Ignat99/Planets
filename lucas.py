import numpy as np
import matplotlib.pyplot as plt

# 1. Диапазон для непрерывных кривых полиномов Лукаса
x = np.linspace(-2.5, 2.5, 1000)

# Формулы первых 10 полиномов Лукаса L_0(x) - L_9(x) по вашей таблице
y0 = 2 * np.ones_like(x)
y1 = x
y2 = x**2 + 2
y3 = x**3 + 3*x
y4 = x**4 + 4*x**2 + 2
y5 = x**5 + 5*x**3 + 5*x
y6 = x**6 + 6*x**4 + 9*x**2 + 2     # Коэффициенты строго по вашей таблице
y7 = x**7 + 7*x**5 + 14*x**3 + 7*x
y8 = x**8 + 8*x**6 + 20*x**4 + 16*x**2 + 2
y9 = x**9 + 9*x**7 + 30*x**5 + 27*x**3 + 9*x

# 2. Дискретные узлы (значения полиномов Лукаса в целых точках x = 1 и x = 2)
# При x=1 полиномы Лукаса дают классическую последовательность Лукаса: 2, 1, 3, 4, 7, 11, 18, 29, 47, 76...
nodes_x_1 = np.ones(10)
nodes_y_1 = [2, 1, 3, 4, 7, 11, 18, 29, 47, 76]

# При x=2 получаем последовательность: 2, 2, 6, 14, 34, 82, 198...
nodes_x_2 = np.ones(8) * 2
nodes_y_2 = [2, 2, 6, 14, 34, 82, 198, 478]

# 3. ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ НЕПРЕРЫВНЫХ ТРАЕКТОРИЙ ЛУКАСА
# Использует обобщенную формулу Бине для полиномов Лукаса: L_n(x) = Ф^n + (-1)^n * Ф^(-n)
def lucas_trajectory(x_val, n_continuous):
    # Дискриминант для золотого сечения полиномов
    D = x_val**2 + 4
    # Корни характеристического уравнения (аналоги фи-чисел)
    phi1 = (x_val + np.sqrt(D)) / 2.0
    phi2 = (x_val - np.sqrt(D)) / 2.0
    
    # Непрерывная формула с учетом знака (-1)^n через комплексную экспоненту / cos
    # L_n(x) = phi1^n + cos(pi * n) * phi2^n (для вещественной плоскости)
    return phi1**n_continuous + np.cos(np.pi * n_continuous) * (np.abs(phi2)**n_continuous)

# 4. Визуализация
plt.figure(figsize=(14, 10), facecolor='white')

# Отрисовка полиномов Лукаса L_0 - L_9
plt.plot(x, y0, label='$L_0(x) = 2$', color='gray', linewidth=1.2, alpha=0.7)
plt.plot(x, y1, label='$L_1(x) = x$', color='red', linewidth=1.5, alpha=0.7)
plt.plot(x, y2, label='$L_2(x) = x^2 + 2$', color='blue', linewidth=1.5, alpha=0.7)
plt.plot(x, y3, label='$L_3(x) = x^3 + 3x$', color='orange', linewidth=1.5, alpha=0.7)
plt.plot(x, y4, label='$L_4(x) = x^4 + 4x^2 + 2$', color='green', linewidth=1.5, alpha=0.7)
plt.plot(x, y5, label='$L_5(x) = x^5 + 5x^3 + 5x$', color='purple', linewidth=1.5, alpha=0.7)
plt.plot(x, y6, label='$L_6(x) = x^6 + 6x^4 + 9x^2 + 2$', color='brown', linewidth=1.5, alpha=0.7)
plt.plot(x, y7, label='$L_7(x) = x^7 + 7x^5 + 14x^3 + 7x$', color='cyan', linewidth=1.2, alpha=0.6)
plt.plot(x, y8, label='$L_8(x) = x^8 + 8x^6 + 20\dots$', color='magenta', linewidth=1.2, alpha=0.6)
plt.plot(x, y9, label='$L_9(x) = x^9 + 9x^7 + 30\dots$', color='olive', linewidth=1.2, alpha=0.6)

# НАЛОЖЕНИЕ ВОЛНОВЫХ ТРАЕКТОРИЙ ЛУКАСА (для фиксированных значений "индекса" n)
# Мы берем x_fib как область полушага, чтобы показать, как ведут себя траектории
x_lucas = np.linspace(-2.5, 2.5, 1000)
for n_val in np.arange(0, 9.5, 0.5):
    y_track = lucas_trajectory(x_lucas, n_val)
    plt.plot(x_lucas, y_track, color='black', linestyle='--', linewidth=1.0, alpha=0.5, zorder=3,
             label='Траектории Лукаса ($n$)' if n_val == 0 else "")

# Нанесение дискретных точек пересечений (целочисленные значения)
plt.scatter(nodes_x_1, nodes_y_1, color='red', edgecolor='black', s=50, zorder=5, label='Узлы Лукаса при x=1')
plt.scatter(nodes_x_2, nodes_y_2, color='blue', edgecolor='black', s=50, zorder=5, label='Узлы Лукаса при x=2')

# Оси координат Ox и Oy
plt.axhline(0, color='black', linewidth=1.0, alpha=0.5)
plt.axvline(0, color='black', linewidth=1.0, alpha=0.5)

# Настройка осей и сетки
plt.xlabel('Значение аргумента (x)', fontsize=11)
plt.ylabel('Результат полинома $L_n(x)$', fontsize=11)
plt.title('Полиномы Лукаса $L_0(x) - L_9(x)$ и их непрерывные волновые траектории', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper center', fontsize=9, ncol=3)

# Ограничение осей для наглядности (так как степени растут быстро)
plt.xlim(-2.5, 2.5)
plt.ylim(-50, 100)

plt.show()
