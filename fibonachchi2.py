import numpy as np
import matplotlib.pyplot as plt

# Константа Золотого Сечения
PHI = (1 + np.sqrt(5)) / 2

# 1. Диапазон для полиномов
x = np.linspace(-10.0, 10.0, 1000)

# 9 полиномов Паскаля из вашей модели
y1 = np.ones_like(x)
y2 = x
y3 = x * (x + 1) / 2
y4 = x * (x + 1) * (x + 2) / 6
y5 = x * (x + 1) * (x + 2) * (x + 3) / 24
y6 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) / 120
y7 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) / 720
y8 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) * (x + 6) / 5040
y9 = x * (x + 1) * (x + 2) * (x + 3) * (x + 4) * (x + 5) * (x + 6) * (x + 7) / 40320

# 2. Дискретные узлы
nodes_x1 = [1, 2, 3, 4, 5, 6]; nodes_y1 = [1, 1, 1, 1, 1, 1]
nodes_x2 = [1, 2, 3, 4, 5];    nodes_y2 = [2, 3, 4, 5, 6]
nodes_x3 = [1, 2, 3, 4];       nodes_y3 = [6, 10, 15, 21]
nodes_x4 = [1, 2, 3];          nodes_y4 = [20, 35, 56]
nodes_x5 = [1, 2];             nodes_y5 = [70, 126]
nodes_x6 = [1];                nodes_y6 = [252]

plt.figure(figsize=(14, 10), facecolor='white')

# Отрисовка исходных 9 полиномов
plt.plot(x, y1, color='gray', linewidth=1.0, alpha=0.4, label='c=1: Точки')
plt.plot(x, y2, color='red', linewidth=1.0, alpha=0.4, label='c=2: Линейные')
plt.plot(x, y3, color='blue', linewidth=1.2, alpha=0.4, label='c=3: Треугольные')
plt.plot(x, y4, color='orange', linewidth=1.2, alpha=0.4, label='c=4: Тетраэдральные')
plt.plot(x, y5, color='green', linewidth=1.2, alpha=0.4, label='c=5: Пентатопные')
plt.plot(x, y6, color='purple', linewidth=1.2, alpha=0.4, label='c=6: 5D-симплексы')
plt.plot(x, y7, color='brown', linewidth=1.0, alpha=0.3, label='c=7: 6D-симплексы')
plt.plot(x, y8, color='cyan', linewidth=1.0, alpha=0.3, label='c=8: 7D-симплексы')
plt.plot(x, y9, color='magenta', linewidth=1.0, alpha=0.3, label='c=9: 8D-симплексы')

# 3. ПРЯМОЙ ВЫВОД АНАЛИТИЧЕСКИХ КРИВЫХ ФИБОНАЧЧИ БЕЗ ГАММА-ФУНКЦИИ
# Строим траектории инварианта Бине напрямую в декартовых координатах графика
x_fib = np.linspace(-10.0, 10.0, 2000)

# Константы K, определяющие волновые фронты Фибоначчи
for K in [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
    # Аналитическое решение уравнения Бине для плоскости полиномов:
    # Вычисляется непрерывный силовой сдвиг, определяющий высоту y в зависимости от шага x и константы K
    power_arg = (K - x_fib) / 2.0
    
    # Прямая аналитическая функция без комбинаторных факториалов
    y_analytic = (PHI**power_arg - np.cos(np.pi * power_arg) * (PHI**(-power_arg))) / np.sqrt(5)
    
    # Ограничиваем область прорисовки физическим коридором, чтобы линии не уходили в бесконечность
    visible_mask = (x_fib >= -5) & (x_fib <= K - 2)
    
    plt.plot(x_fib[visible_mask], y_analytic[visible_mask], color='black', linestyle='--', linewidth=1.6, zorder=4,
             label=f'Аналитическая кривая (K={K})' if K==7 else "")

# Нанесение дискретных точек пересечений
plt.scatter(nodes_x1, nodes_y1, color='gray', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x2, nodes_y2, color='red', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x3, nodes_y3, color='blue', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x4, nodes_y4, color='orange', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x5, nodes_y5, color='green', edgecolor='black', s=45, zorder=5)
plt.scatter(nodes_x6, nodes_y6, color='purple', edgecolor='black', s=45, zorder=5)

plt.axhline(0, color='black', linewidth=1.0, alpha=0.5)
plt.axvline(0, color='black', linewidth=1.0, alpha=0.5)
plt.xlabel('Шаг / Размерность (x)', fontsize=11)
plt.ylabel('Результат полинома (y)', fontsize=11)
plt.title('Анаморфическая проекция аналитических кривых Фибоначчи на полиномы Паскаля', fontsize=12, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(loc='upper left', fontsize=9, ncol=2)

plt.xlim(-10.5, 10.5)
plt.ylim(-50, 300)  # Скорректированный масштаб отображения

plt.show()
