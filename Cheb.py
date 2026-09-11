import numpy as np
import matplotlib.pyplot as plt

# Задаем диапазон изменения параметра t от -3 до 3
t = np.linspace(-3, 3, 1000)

# Вычисляем координаты x и y по заданным формулам
x = t**5 - 5*t**3 + 4*t
y = 5*t**4 - 20*t**2 + 16

# Добавляем аксиальное ускорение по оси Z: z = t * |t|
# Это сохраняет знак t, но заставляет шаг по Z увеличиваться (ускоряться) при удалении от нуля
z = t * np.abs(t)

# Создаем трехмерный график
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Строим кривую
ax.plot(x, y, z, label='Кривая с ускорением по Z', color='r', lw=2)

# Настраиваем подписи осей
ax.set_xlabel('Ось X')
ax.set_ylabel('Ось Y')
ax.set_zlabel('Ось Z (ускоренная)')
ax.set_title('3D график с аксиальным ускорением по оси Z')
ax.grid(True)
ax.legend()

# Отображаем график
plt.show()
