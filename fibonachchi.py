import numpy as np
import matplotlib.pyplot as plt
from scipy.special import gamma

# Константы для аналитического уравнения
PHI = (1 + np.sqrt(5)) / 2

# 1. Расширенный диапазон для базовых непрерывных кривых
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

# 2. Дискретные узлы таблицы Юпаны
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

nodes_y1 = [1, 1, 1, 1, 1, 1]
nodes_y2 = [2, 3, 4, 5, 6]
nodes_y3 = [6, 10, 15, 21]
nodes_y4 = [20, 35, 56]
nodes_y5 = [70, 126]
nodes_y6 = [252]

# 3. Визуализация
plt.figure(figsize=(14, 10), facecolor='white')

# Отрисовка исходных 9 полиномов
plt.plot(x, y1, label='c=1: Точки', color='gray', linewidth=1.0, alpha=0.4)
plt.plot(x, y2, label='c=2: Линейные', color='red', linewidth=1.0, alpha=0.4)
plt.plot(x, y3, label='c=3: Треугольные', color='blue', linewidth=1.2, alpha=0.4)
plt.plot(x, y4, label='c=4: Тетраэдральные', color='orange', linewidth=1.2, alpha=0.4)
plt.plot(x, y5, label='c=5: Пентатопные', color='green', linewidth=1.2, alpha=0.4)
plt.plot(x, y6, label='c=6: 5D-симплексы', color='purple', linewidth=1.2, alpha=0.4)
plt.plot(x, y7, label='c=7: 6D-симплексы', color='brown', linewidth=1.0, alpha=0.3)
plt.plot(x, y8, label='c=8: 7D-симплексы', color='cyan', linewidth=1.0, alpha=0.3)
plt.plot(x, y9, label='c=9: 8D-симплексы', color='magenta', linewidth=1.0, alpha=0.3)

# 4. ПОСТРОЕНИЕ ПАРАМЕТРИЧЕСКИХ КРИВЫХ ЗАКРУЧИВАНИЯ (МОДЕЛЬ ВАКУУМА)
# t - параметр траектории движения планеты (время / развертка)
t_param = np.linspace(-10.0, 10.0, 2500)

# Задаем физические параметры анизотропной среды
omega_x = 0.5   # Частота фазовых колебаний Лиссажу по Ox
delta_x = 0.0   # Начальный сдвиг фазы
omega_t = 0.3   # Модуляция изменения волнового потенциала со временем

# Генерируем семейство траекторий для различных базовых квантовых уровней N0
for N0 in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]:
    # Динамический волновой потенциал N(t), совершающий колебания вокруг базового уровня N0
    N_t = N0 + 2.0 * np.sin(omega_t * t_param)
    
    # Уравнение координаты x(t) из вашего условия
    x_t = t_param * np.cos(omega_x * t_param + delta_x)
    
    # Уравнение фазового сдвига из вашего условия (соответствует пространственной Oy_модели)
    # Используем логарифм по основанию PHI: log_phi(v) = log(v) / log(PHI)
    inner_sqrt = np.sqrt(5.0 * N_t**2 + 4.0 * (-1.0)**np.round(N_t))
    numerator = (np.sqrt(5.0) * N_t + inner_sqrt) / 2.0
    
    # Защита от отрицательных значений под логарифмом
    numerator = np.clip(numerator, 1e-5, None)
    y_model_t = 0.5 * (np.log(numerator) / np.log(PHI) - x_t)
    
    # Перевод пространственной фазовой координаты y_model_t в номер столбца c для вашего графика:
    # Так как по определению диагоналей Фибоначчи: x_t + 2*c = N_t, а из формулы y_model_t — это шаг сдвига c.
    c_t = y_model_t 
    
    # Рассчитываем вертикальную координату графика Y_graph через Гамма-поле Паскаля
    y_graph = []
    for xi, ci in zip(x_t, c_t):
        if 1.0 <= ci <= 9.0: # Коридор видимости ваших 9 полиномов
            try:
                val = gamma(xi + ci - 1) / (gamma(ci) * gamma(xi + 1))
                y_graph.append(val)
            except:
                y_graph.append(np.nan)
        else:
            y_graph.append(np.nan)
            
    y_graph = np.array(y_graph)
    
    # Отрисовка непрерывного закрученного фазового фронта
    plt.plot(x_t, y_graph, color='black', linestyle='-', linewidth=1.8, zorder=4,
             label=f'Вихревая волна (N0={N0})' if N0==7 else "")

# Нанесение дискретных точек пересечений Юпаны
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
plt.title('Параметрические волны закручивания Фибоначчи на поле полиномов Юпаны', fontsize=13, fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.5)
plt.legend(loc='upper left', fontsize=9, ncol=2)

# Ограничение осей под масштаб вашей таблицы
plt.xlim(-10.5, 10.5)
plt.ylim(-300, 300)

plt.show()

