import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# === 1. ДАННЫЕ ПЛАНЕТ И КАРТОЧНЫХ КОЭФФИЦИЕНТОВ ===
# Формат: (Название, Масть, Чистый коэффициент k, Сдвиг масти в градусах, Период в летах T)
planets_data = [
    ("Хорсъ (Меркурий)", "♣", 1, 0, 0.2418, "#d32f2f"),
    ("Заря-Мерцана (Венера)", "♣", 4, 0, 0.6150, "#e91e63"),
    ("Мидгардъ (Земля)", "♣", 6, 0, 1.0000, "#2196f3"),
    ("Орей (Марс)", "♣", 11, 0, 1.8810, "#f44336"),
    ("Перунъ (Юпитер)", "♠", 6, 90, 11.8600, "#ff9800"),
    ("Стрибогъ (Сатурн)", "♠", 16, 90, 29.4600, "#9c27b0"),
    ("Луна (Месяц)", "♣", 0.5, 0, 0.0808, "#78909c")
]

# === 2. ПАРАМЕТРЫ 60-СЕКТОРНОЙ МАТРИЦЫ ===
num_sectors = 60
d_theta_base = 2 * np.pi / num_sectors  # 6 градусов (2π/60)
a = 1.0
b_step = 0.8
num_frames = 360  # Количество кадров в цикле

# Настройка полярного графика
fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={'projection': 'polar'}, facecolor='#f8f9fa')
ax.set_facecolor('#ffffff')

# 60-ричная статическая сетка
sector_angles = np.linspace(0, 2 * np.pi, num_sectors, endpoint=False)
for angle in sector_angles:
    ax.plot([angle, angle], [0, 20], color='#e0e0e0', linestyle=':', linewidth=0.8, zorder=1)

# Выделение 6 главных осей (hexagon)
for main_angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
    ax.plot([main_angle, main_angle], [0, 20], color='#b0bec5', linestyle='--', linewidth=1.2, zorder=2)

# Списки объектов для анимации
scatters = []
lines = []
texts = []

# Инициализация графических элементов для каждой планеты
for name, suit, k, phase_shift_deg, T, color in planets_data:
    line, = ax.plot([], [], color=color, alpha=0.5, linestyle='-', linewidth=1.5)
    scatter = ax.scatter([], [], color=color, s=120, zorder=5, edgecolors='black', linewidth=1)
    text = ax.text(0, 0, '', fontsize=8, fontweight='bold', ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.85, edgecolor=color))
    
    lines.append(line)
    scatters.append(scatter)
    texts.append(text)

# Настройка осей
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_ylim(0, 22)
ax.set_yticklabels([])

# === 3. ФУНКЦИЯ ОБНОВЛЕНИЯ КАДРА (АНИМАЦИЯ) ===
def update(frame):
    # Время t меняется от 0 до 5 лет за полный цикл анимации
    t = (frame / num_frames) * 5.0
    
    for i, (name, suit, k, phase_shift_deg, T, color) in enumerate(planets_data):
        phase_shift_rad = np.radians(phase_shift_deg)
        
        # Угловое движение: базовая позиция на спирали + вращение со скоростью (2π / T) * t
        omega = (2 * np.pi) / T
        current_theta = (k * d_theta_base) + phase_shift_rad + (omega * t)
        
        # Небольшая пульсация радиуса по спиральной функции
        r = a + b_step * (k + (phase_shift_deg / 360.0) * num_sectors)
        
        # Обновление вектора связи с центром
        lines[i].set_data([phase_shift_rad, current_theta], [0, r])
        
        # Обновление точки планеты
        scatters[i].set_offsets([[current_theta, r]])
        
        # Обновление текста и позиции метки
        texts[i].set_position((current_theta, r + 1.2))
        texts[i].set_text(f"{name}\n[{k} {suit}]")
        
    ax.set_title(f"Спиральная Луланьская Матрица в движении\nВремя: {t:.2f} лет | 60 секторов", 
                 fontsize=11, fontweight='bold', pad=20)
    
    return lines + scatters + texts

# Запуск анимации (интервал 30 мс на кадр)
ani = FuncAnimation(fig, update, frames=num_frames, interval=30, blit=False, repeat=True)

plt.tight_layout()
plt.show()