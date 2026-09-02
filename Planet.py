import numpy as np
import matplotlib.pyplot as plt

# === 1. ДАННЫЕ ПЛАНЕТ И КАРТОЧНЫХ КОЭФФИЦИЕНТОВ ===
# Формат: (Название, Масть, Чистый коэффициент k, Сдвиг масти в градусах)
planets_data = [
    # ♣ Черви (Старт: 0°)
    ("Хорсъ (Меркурий)", "♣", 1, 0, "#d32f2f"),
    ("Заря-Мерцана (Венера)", "♣", 4, 0, "#e91e63"),
    ("Мидгардъ (Земля)", "♣", 6, 0, "#2196f3"),
    ("Орей (Марс)", "♣", 11, 0, "#f44336"),
    
    # ♠ Бубны (Старт: 90° - фазовый сдвиг масти)
    ("Перунъ (Юпитер)", "♠", 6, 90, "#ff9800"),
    ("Стрибогъ (Сатурн)", "♠", 16, 90, "#9c27b0"),
    
    # Спутник Земли
    ("Луна (Месяц)", "♣", 0.5, 0, "#78909c")
]

# === 2. ПАРАМЕТРЫ 60-СЕКТОРНОЙ СПИРАЛИ ===
num_sectors = 60
d_theta_base = 2 * np.pi / num_sectors  # Базовый дискретный шаг (6° или 2π/60)
a = 1.0  # Начальный радиус
b_step = 0.8  # Шаг прироста радиуса на виток

# Настройка фигуры
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'}, facecolor='#f8f9fa')
ax.set_facecolor('#ffffff')

# === 3. ОТРИСОВКА 60-РИЧНОЙ СЕТКИ СЕКТОРОВ ===
sector_angles = np.linspace(0, 2 * np.pi, num_sectors, endpoint=False)
for angle in sector_angles:
    ax.plot([angle, angle], [0, 20], color='#e0e0e0', linestyle=':', linewidth=0.8, zorder=1)

# Выделение ключевых 6-угольных и 10-угольных осей (узоры 6 и 10)
for main_angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
    ax.plot([main_angle, main_angle], [0, 20], color='#b0bec5', linestyle='--', linewidth=1.2, zorder=2)

# === 4. ПОСТРОЕНИЕ СПИРАЛИ И РАССТАНОВКА ПЛАНЕТ ===
for name, suit, k, phase_shift_deg, color in planets_data:
    phase_shift_rad = np.radians(phase_shift_deg)
    
    # Расчет угла на спирали: базовый шаг отрезка + фазовый сдвиг масти
    theta = (k * d_theta_base) + phase_shift_rad
    
    # Полярная функция радиуса: r = a + b * theta
    r = a + b_step * (k + (phase_shift_deg / 360.0) * num_sectors)
    
    # Отрисовка луча-вектора от центра к планете
    ax.plot([phase_shift_rad, theta], [0, r], color=color, alpha=0.4, linestyle='-', linewidth=1.5)
    
    # Точка планеты на матрице
    ax.scatter(theta, r, color=color, s=120, zorder=5, edgecolors='black', linewidth=1)
    
    # Подпись планеты и её карты
    label = f"{name}\n[{k} {suit}]"
    ax.text(theta, r + 0.8, label, fontsize=8, fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8, edgecolor=color))

# === 5. ОФОРМЛЕНИЕ МАТРИЦЫ ===
ax.set_theta_zero_location("N")  # 0 градусов вверху (Север)
ax.set_theta_direction(-1)       # Вращение по часовой стрелке
ax.set_rticks([5, 10, 15, 20])
ax.set_yticklabels([])           # Убираем числовые метки радиусов
ax.set_title("Спиральная Луланьская Матрица (60 секторов)\nРазвертка карточных коэффициентов орбит", 
             fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.show()