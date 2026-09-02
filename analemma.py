import numpy as np
import matplotlib.pyplot as plt

# https://homedevice.pro/analemma-solntsa/

N = np.arange(1, 366)
B = (2 * np.pi / 365) * (N-81)

# Уравнение времени в минутах и перевод в градусы смещения (X)
EoT = 9.87 * np.sin(2 * B) - 7.67 * np.cos(B) - 1.5 * np.sin(B)
X = -EoT / 4 # 1 градус = 4 минуты

# Склонение в градусах (Y)
Y = 23.44 * np.sin((2 * np.pi / 365) * (N - 80))

plt.figure(figsize=(6, 8))
plt.plot(X, Y, 'r-', label='Аналемма Солнца')gi
plt.title('Математическая аналемма')
plt.xlabel('Смещение по горизонтали (градусы)')
plt.ylabel('Склонение / Высота (градусы)')
plt.grid(True)
plt.axvline(0, color='black', linewidth=0.5)
plt.axhline(0, color='black', linewidth=0.5)
plt.show()
