import numpy as np
import matplotlib.pyplot as plt
from scipy.special import gamma

# 1. Расширенный диапазон для непрерывных кривых от -10 до 10
x = np.linspace(-10.0, 10.0, 1000)
# 1. Расширенный диапазон для непрерывных кривых от -10 до 10 (настоящий)
xd = np.linspace(-10.0, 10.0, 20)


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

# Формулы 9 полиномов Паскаля (симплициальных чисел) (настоящих)
y1d = np.ones_like(xd)
y2d = xd
y3d = xd * (xd + 1) / 2
y4d = xd * (xd + 1) * (xd + 2) / 6
y5d = xd * (xd + 1) * (xd + 2) * (xd + 3) / 24
y6d = xd * (xd + 1) * (xd + 2) * (xd + 3) * (xd + 4) / 120
y7d = xd * (xd + 1) * (xd + 2) * (xd + 3) * (xd + 4) * (xd + 5) / 720
y8d = xd * (xd + 1) * (xd + 2) * (xd + 3) * (xd + 4) * (xd + 5) * (xd + 6) / 5040
y9d = xd * (xd + 1) * (xd + 2) * (xd + 3) * (xd + 4) * (xd + 5) * (xd + 6) * (xd + 7) / 40320


# Базовые массивы (так как ypana строится на их основе)
nodes_y1 = np.array([1, 1, 1, 1, 1, 1])
nodes_x1 = np.array([1, 2, 3, 4, 5, 6])
nodes_y3 = np.array([6, 10, 15, 21])
nodes_y4 = np.array([20, 35, 56])
nodes_y5 = np.array([70, 126])
nodes_y6 = np.array([252])

# Сборка строк ypana чисто через функции NumPy (hstack объединяет массивы горизонтально)
ypana_y1 = np.hstack(([1], nodes_y1))
ypana_y2 = np.hstack((nodes_x1, [7]))
ypana_y3 = np.hstack(([1, 3], nodes_y3, [28]))
ypana_y4 = np.hstack(([1, 4, 10], nodes_y4, [84]))
ypana_y5 = np.hstack(([1, 5, 15, 35], nodes_y5, [210]))
ypana_y6 = np.hstack(([1, 6, 21, 56, 126], nodes_y6, [462]))
ypana_y7 = np.array([1, 7, 28, 84, 210, 462, 924])

# Создаем пустую матрицу 7x7 из нулей
ypana = np.zeros((7, 7), dtype=int)

# Заполняем каждую строку (первая строка ypana_y1 имеет длину 7, остальные тоже)
ypana[0, :] = ypana_y1
ypana[1, :] = ypana_y2
ypana[2, :] = ypana_y3
ypana[3, :] = ypana_y4
ypana[4, :] = ypana_y5
ypana[5, :] = ypana_y6
ypana[6, :] = ypana_y7

print(ypana)

fib_1 = ypana[0,0]
fib_1_list = [
    [0, 0]
] # 1

fib_2 = ypana[1,0]
fib_2_list = [[1, 0]]  # 1

fib_3 = ypana[2,0] + ypana[0,1]
fib_3_list = [[2.0],[0,1]] # 2

fib_4 = ypana[3,0] + ypana[1,1]
fib_4_list = [[3,0], [1,1]] # 3

fib_5 = ypana[4,0] + ypana[2,1] + ypana[0,2]
fib_5_list = [[4,0], [2,1], [0,2]] # 5

fib_6 = ypana[5,0] + ypana[3,1] + ypana[1,3]
fib_6_list = [[5,0],[3,1], [1,2]] # 8

fib_7 = ypana[6,0] + ypana[4,1] + ypana[2,2] + ypana[0,3]
fib_7_list = [[6,0],[4,1],[2,2],[0,3]] # 13

#fib_8 = ypana[7,0] + ypana[5,1] + ypana[3,2] + ypana[1,4]
#fib_8_list = [[7,0],[5,1],[3,2],[1,3]] # 21

#fib_9 = ypana[8.0] + ypana[6,1] + ypana[4,2] + ypana[2,3] + ypana[0,4]
#fib_9_list = [[8.0], [6,1], [4,2],[2,3],[0,4]] # 34

# 1. Генерируем расширенную матрицу ypana (треугольник Паскаля) размером 9x9 через NumPy
# Это необходимо, чтобы работали индексы из fib_8 и fib_9 (строки 7 и 8)
ypana = np.zeros((9, 9), dtype=int)
for i in range(9):
    for j in range(9):
        if i == 0:
            ypana[i, j] = 1
        elif j == 0:
            ypana[i, j] = 1
        else:
            ypana[i, j] = ypana[i-1, j] + ypana[i, j-1]

print(ypana)

# 2. Автоматическая генерация координат и значений Фибоначчи на NumPy
fib_values = {}
fib_coords = {}

for n in range(1, 10):  # Для fib_1 ... fib_9
    # Для каждого n сумма индексов строки (r) и столбца (c) равна n - 1.
    # При этом строка уменьшается на 2, а столбец увеличивается на 1.
    
    # Генерируем массив строк: от (n-1) вниз до 0 с шагом -2
    rows = np.arange(n - 1, -1, -2)
    # Генерируем массив столбцов: от 0 вверх с шагом 1
    cols = np.arange(0, len(rows))
    
    # Объединяем их в двумерную матрицу координат (размерность К x 2)
    coords_matrix = np.column_stack((rows, cols))
    
    # Извлекаем значения из ypana по сгенерированным координатам и суммируем их
    value = np.sum(ypana[rows, cols])
    
    # Сохраняем в словари (для удобства работы)
    fib_coords[f"fib_{n}_coords"] = coords_matrix
    fib_values[f"fib_{n}_value"] = value

# ==========================================
# ДЕМОНСТРАЦИЯ РЕЗУЛЬТАТОВ (Вывод на экран)
# ==========================================

# Выведем конкретный пример, например для fib_5 и fib_9, как в вашем запросе:
for n in range(1, 10):
    print(f"--- fib_{n} ---")
    print(f"Значение Фибоначчи: {fib_values[f'fib_{n}_value']}")
    print("Матрица координат NumPy:")
    print(fib_coords[f"fib_{n}_coords"])
    print(f"Тип объекта координат: {type(fib_coords[f'fib_{n}_coords'])}\n")


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

# Нанесение дискретных точек пересечений (настоящих)
plt.scatter(xd, y1d, color='gray', edgecolor='black', s=45, zorder=5)
plt.scatter(xd, y2d, color='red', edgecolor='black', s=45, zorder=5)
plt.scatter(xd, y3d, color='blue', edgecolor='black', s=45, zorder=5)
plt.scatter(xd, y4d, color='orange', edgecolor='black', s=45, zorder=5)
plt.scatter(xd, y5d, color='green', edgecolor='black', s=45, zorder=5)
plt.scatter(xd, y6d, color='purple', edgecolor='black', s=45, zorder=5)

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
