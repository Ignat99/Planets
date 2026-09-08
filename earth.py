import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 1. Определение констант и параметров модели
phi = (1 + 5**0.5) / 2  # Золотое сечение (~1.618)
R0 = 10.0               # Начальный радиус
Z0 = 3.0                # Максимальная амплитуда по оси Z
alpha = 0.04            # Коэффициент "намотки" спирали к центру

# Частоты и фазовые сдвиги для генерации "восьмерки" (Лиссажу)
omega1 = 1.0
omega2 = 2.0            # Соотношение частот 1:2 создает классическую фигуру-8
omega3 = 1.0            # Частота вертикального колебания
delta = np.pi / 4       # Фазовый сдвиг для раскрытия проекции
c = 0.0                 # Узел квантования (для визуализации cos^2(pi * c) = 1)

# 2. Генерация фазового параметра lambda (волновой фронт Фибоначчи)
# Генерируем диапазон от 0 до 8*pi (несколько полных витков)
lambdas = np.linspace(0, 8 * np.pi, 2000)

# 3. Вычисление компонент 3D-вектора R(lambda)ตาม заданным уравнениям
X = R0 * (phi ** (-alpha * lambdas)) * np.cos(omega1 * lambdas)
Y = R0 * (phi ** (-alpha * lambdas)) * np.sin(omega2 * lambdas + delta)
Z = Z0 * np.sin(omega3 * lambdas) * (np.cos(np.pi * c) ** 2)

# 4. Визуализация в 3D-пространстве
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Отображение основной 3D-спирали (с градиентом цвета по ходу движения волны)
sc = ax.scatter(X, Y, Z, c=lambdas, cmap='plasma', s=4, label='3D Аналемма $R(\\lambda)$')

# Для наглядности добавим проекцию на плоскость эклиптики (X, Y) на "дне" графика
ax.plot(X, Y, np.full_like(Z, -Z0), color='gray', linestyle='--', alpha=0.5, label='Проекция Лиссажу (эклиптика)')

# Оформление осей и графика
ax.set_title('3D-аналемма планетарной пары в детерминированном каркасе Фибоначчи', fontsize=12)
ax.set_xlabel('X (Эклиптика)')
ax.set_ylabel('Y (Эклиптика)')
ax.set_zlabel('Z (Орбитальный наклон)')

# Настройка лимитов осей
ax.set_zlim(-Z0 - 1, Z0 + 1)

# Добавление цветовой шкалы времени/фазы lambda
cbar = fig.colorbar(sc, ax=ax, pad=0.1, shrink=0.6)
cbar.set_label('Фаза волнового фронта ($\\lambda$)')

ax.legend()
plt.show()
