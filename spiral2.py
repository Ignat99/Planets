import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# === 1. ПАРАМЕТРЫ МОДЕЛИ ===
a = 1.0
c = 1.000      # Степень 1/c = 1.0 (классическая архимедова спираль)
num_points = 60 # 60 отрезков в фазовом узоре
num_frames = 200 # Количество кадров анимации

# Диапазон изменения dθ: от π до 2π
d_theta_values = np.linspace(np.pi, 2 * np.pi, num_frames)

# Подготовка фигуры
fig, ax = plt.subplots(figsize=(8, 8), facecolor='white')
ax.set_aspect('equal', 'box')
ax.grid(True, linestyle=':', alpha=0.3)

line, = ax.plot([], [], color='#1a1a1a', linewidth=1.0, alpha=0.85)

# Фиксируем масштабы осей, чтобы анимация не "скакала"
max_r = a + (1.0 / np.pi) * ((num_points - 1) * 2 * np.pi) ** (1.0 / c)
ax.set_xlim(-max_r * 0.7, max_r * 0.7)
ax.set_ylim(-max_r * 0.7, max_r * 0.7)

def update(frame):
    d_theta = d_theta_values[frame]
    b = 1.0 / d_theta  # Зависимость b = 1 / dθ
    
    # 1. Итерация по углу θ с шагом dθ
    indices = np.arange(num_points)
    theta = indices * d_theta
    
    # 2. Полярная функция: r = a + b * θ^(1/c)
    r = a + b * (theta ** (1.0 / c))
    
    # 3. Перевод в декартовы координаты
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    line.set_data(x, y)
    ax.set_title(f"dθ = {d_theta:.3f} rad | b = 1/dθ = {b:.3f} | 60 отрезков", fontsize=11)
    return line,

ani = FuncAnimation(fig, update, frames=num_frames, interval=50, blit=True, repeat=True)

plt.show()