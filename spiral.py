import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# === 1. ПАРАМЕТРЫ МОДЕЛИ (как в ячейках Excel) ===
b = 1.281      # Коэффициент масштаба
c = 1.000      # Начальный радиус (r0)
d_theta = 3.903 # Шаг по углу в радианах (~223.6 градусов)
step_r = 5.0   # Прирост радиуса на каждом шаге (как в столбце r: 1, 6, 11, 16...)
num_points = 60 # Количество отрезков/точек (доходит до 60 для точности)

# === 2. РАСЧЕТ ТАБЛИЦЫ КООРДИНАТ (Аналог столбцов theta, r, x, y) ===
indices = np.arange(num_points)
theta = indices * d_theta
r = c + indices * step_r

# Перевод в декартовы координаты (x = r*cos(theta), y = r*sin(theta))
x = r * np.cos(theta)
y = r * np.sin(theta)

# === 3. ОТРИСОВКА ГРАФИКА (Статический фазовый узор) ===
fig, ax = plt.subplots(figsize=(8, 8), facecolor='white')
ax.set_facecolor('white')

# Рисуем ломаную линию, соединяющую точки
line, = ax.plot(x, y, color='#2b2b2b', linewidth=1, alpha=0.85)

# Настройка осей и сетки
ax.axhline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
ax.axvline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
ax.set_aspect('equal', 'box')
ax.set_title(f"Архимедова спираль из {num_points} отрезков (dθ = {d_theta} rad)", fontsize=12)
ax.grid(True, linestyle=':', alpha=0.3)

plt.tight_layout()
plt.show()

# === 4. АНИМАЦИЯ (Пошаговое построение, как кнопка Animate в Excel) ===
fig_anim, ax_anim = plt.subplots(figsize=(8, 8))
ax_anim.set_aspect('equal', 'box')
ax_anim.grid(True, linestyle=':', alpha=0.3)
ax_anim.set_xlim(np.min(x) - 10, np.max(x) + 10)
ax_anim.set_ylim(np.min(y) - 10, np.max(y) + 10)

anim_line, = ax_anim.plot([], [], color='#1a1a1a', linewidth=1.2)
point_dot, = ax_anim.plot([], [], 'ro', markersize=4) # Текущая вершина

def init():
    anim_line.set_data([], [])
    point_dot.set_data([], [])
    return anim_line, point_dot

def update(frame):
    anim_line.set_data(x[:frame+1], y[:frame+1])
    point_dot.set_data([x[frame]], [y[frame]])
    ax_anim.set_title(f"Шаг {frame + 1} из {num_points} | r = {r[frame]:.1f}")
    return anim_line, point_dot

ani = FuncAnimation(fig_anim, update, frames=num_points, init_func=init, interval=150, blit=True, repeat=True)

# Чтобы запустить анимацию в Jupyter Notebook или отдельном окне:
plt.show()