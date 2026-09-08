import numpy as np
import matplotlib.pyplot as plt
from scipy.special import gamma

# 1. Расширенный диапазон для непрерывных кривых от -10 до 10
x = np.linspace(-10.0, 10.0, 1000)

# Формулы 9 полиномов Паскаля (симплициальных чисел)
y1 = np.ones_like(x)
y2 = x
y3 = x * (x + 1) / 2
y4 = x * (x + 1) * (x + 2) / 6
y5 = x * (x + 1) * (x + 2) * (x + 3) / 24
y6 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) / 120
y7 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) / 720
y8 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) * (x + 6) / 5040
y9 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) * (x + 6) * (x + 7) / 40320

# 2. Дискретные узлы из вашей таблицы (полностью восстановлены)
nodes_x1 = [1, 2, 3, 4, 5, 6]
nodes_y1 = [1, 1, 1, 1, 1, 1]

nodes_x2 = [1, 2, 3, 4, 5]
nodes_y2 = [2, 3, 4, 5, 6]

nodes_x3 = [1, 2, 3, 4]
nodes_y3 = [6, 10, 15, 21]

nodes_x4 = [1, 2, 3]
nodes_y4 = [20, 35, 56]

nodes_x5 = [1, 2]
nodes_y5 = [70, 126]

nodes_x6 = [1]
nodes_y6 = [252]

# 3. ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ НЕПРЕРЫВНЫХ КРИВЫХ ФИБОНАЧЧИ
def fibonacci_trajectory(x_range, const_val):
    y_res = []
    for xi in x_range:
        # Вычисляем непрерывный номер столбца c для данной диагонали
        c_val = (const_val - xi) / 2.0
        
        # Защита от выхода за пределы сетки полиномов (работаем в диапазоне 1 <= c <= 9)
        if 1.0 <= c_val <= 9.0:
            # Обобщенная формула P_c(x) через Гамма-функции Г(n+1) = n!
            try:
                val = gamma(xi + c_val - 1) / (gamma(c_val) * gamma(xi + 1))
                y_res.append(val)
            except:
                y_res.append(np.nan)
        else:
            y_res.append(np.nan)
    return np.array(y_res)

# 4. Визуализация
plt.figure(figsize=(14, 10), facecolor='white')

# Отрисовка исходных 9 полиномов
plt.plot(x, y1, label='c=1: Точки', color='gray', linewidth=1.0, alpha=0.5)
plt.plot(x, y2, label='c=2: Линейные', color='red', linewidth=1.0, alpha=0.5)
plt.plot(x, y3, label='c=3: Треугольные', color='blue', linewidth=1.2, alpha=0.6)
plt.plot(x, y4, label='c=4: Тетраэдральные', color='orange', linewidth=1.2, alpha=0.6)
plt.plot(x, y5, label='c=5: Пентатопные', color='green', linewidth=1.2, alpha=0.6)
plt.plot(x, y6, label='c=6: 5D-симплексы', color='purple', linewidth=1.2, alpha=0.6)
plt.plot(x, y7, label='c=7: 6D-симплексы', color='brown', linewidth=1.0, alpha=0.4)
plt.plot(x, y8, label='c=8: 7D-симплексы', color='cyan', linewidth=1.0, alpha=0.4)
plt.plot(x, y9, label='c=9: 8D-симплексы', color='magenta', linewidth=1.0, alpha=0.4)

# НАЛОЖЕНИЕ КРИВЫХ ДИАГОНАЛЕЙ ФИБОНАЧЧИ (через диапазон range без скобок)
x_fib = np.linspace(-10.0, 10.0, 2000) 
for k in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
    y_fib = fibonacci_trajectory(x_fib, const_val=k)
    plt.plot(x_fib, y_fib, color='black', linestyle='--', linewidth=1.5, zorder=4,
             label=f'Траектория Фибоначчи (K={k})' if k==5 else "")

# Нанесение дискретных точек пересечений
plt.scatter(nodes_x1, nodes_y1, color='gray', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x2, nodes_y2, color='red', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x3, nodes_y3, color='blue', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x4, nodes_y4, color='orange', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x5, nodes_y5, color='green', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x6, nodes_y6, color='purple', edgecolor='black', s=45, zorder=5)

# Оси координат Ox и Oy
plt.axhline(0, color='black', linewidth=1.0, alpha=0.5)
plt.axvline(0, color='black', linewidth=1.0, alpha=0.5)

# Настройка осей и сетки
plt.xlabel('Шаг / Размерность (x)', fontsize=11)
plt.ylabel('Результат полинома (y)', fontsize=11)
plt.title('9 полиномов Юпаны с наложением волновых траекторий Фибоначчи', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(loc='upper left', fontsize=9, ncol=2)

# Ограничение осей
plt.xlim(-10.5, 10.5)
plt.ylim(-300, 300)

plt.show()
