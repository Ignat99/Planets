import numpy as np
import matplotlib.pyplot as plt

# Задаем диапазон изменения параметра t от -3 до 3
t = np.linspace(-3, 3, 1000)

# Вычисляем координаты x, y, z по заданным формулам
x = t**5 - 5*t**3 + 4*t
y = 5*t**4 - 20*t**2 + 16
z = t

# Создаем трехмерный график
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Строим кривую
ax.plot(x, y, z, label='Параметрическая кривая', color='b', lw=2)

# Настраиваем подписи осей
ax.set_xlabel('Ось X')
ax.set_ylabel('Ось Y')
ax.set_zlabel('Ось Z (t)')
ax.set_title('Трехмерный график кривой на отрезке [-3; 3]')
ax.grid(True)
ax.legend()

# Отображаем график
plt.show()
