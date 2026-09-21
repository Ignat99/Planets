"""
Файл: planet4.py

Спиральная Луланьская Матрица — модуль визуализации движения планет
на 60-секторной полярной сетке с карточными коэффициентами.

Может использоваться как импортируемый модуль (доступны planets_data,
параметры сетки и функция run_animation) либо как самостоятельный скрипт.
"""

import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# === 1. ДАННЫЕ ПЛАНЕТ И КАРТОЧНЫХ КОЭФФИЦИЕНТОВ ===
# Формат: (Название, Масть, Чистый коэффициент k, Сдвиг масти в градусах,
#          Период в годах T, Цвет)
planets_data = [
    ("Хорсъ (Меркурий)",      "♣", 1,    0, 0.2418, "#d32f2f"),
    ("Заря-Мерцана (Венера)", "♣", 4,    0, 0.6150, "#e91e63"),
    ("Мидгардъ (Земля)",      "♣", 6,    0, 1.0000, "#2196f3"),
    ("Орей (Марс)",           "♣", 11,   0, 1.8810, "#f44336"),
    ("Перунъ (Юпитер)",       "♠", 6,   90, 11.860, "#ff9800"),
    ("Стрибогъ (Сатурн)",     "♠", 16,  90, 29.460, "#9c27b0"),
    ("Луна (Месяц)",          "♣", 0.5,  0, 0.0808, "#78909c"),
]


# === 2. ПАРАМЕТРЫ 60-СЕКТОРНОЙ МАТРИЦЫ ===
NUM_SECTORS = 60
D_THETA_BASE = 2 * np.pi / NUM_SECTORS   # 6 градусов (2π/60)
A = 1.0
B_STEP = 0.8
NUM_FRAMES = 360                        # Количество кадров в цикле
ANIM_INTERVAL_MS = 30                    # Интервал кадра в миллисекундах
ANIM_DURATION_YEARS = 5.0               # Длительность цикла в годах


def _setup_axes(ax):
    """
    Настраивает полярную ось: 60-ричная статическая сетка,
    6 главных осей (гексаграмма), нулевая точка на «Севере».

    Args:
        ax (matplotlib.axes.Axes): Полярная ось для настройки.
    """
    ax.set_facecolor('#ffffff')

    # 60-ричная статическая сетка
    sector_angles = np.linspace(0, 2 * np.pi, NUM_SECTORS, endpoint=False)
    for angle in sector_angles:
        ax.plot([angle, angle], [0, 20], color='#e0e0e0',
                linestyle=':', linewidth=0.8, zorder=1)

    # Выделение 6 главных осей (гексаграмма)
    for main_angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        ax.plot([main_angle, main_angle], [0, 20], color='#b0bec5',
                linestyle='--', linewidth=1.2, zorder=2)

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 22)
    ax.set_yticklabels([])


def _init_elements(ax):
    """
    Создаёт графические элементы (линии, точки, подписи) для каждой планеты.

    Args:
        ax (matplotlib.axes.Axes): Полярная ось, на которой размещаются элементы.

    Returns:
        tuple[list, list, list]: Кортеж (lines, scatters, texts) — списки
        графических объектов matplotlib, по одному на каждую планету.
    """
    lines = []
    scatters = []
    texts = []

    for name, suit, k, phase_shift_deg, T, color in planets_data:
        line, = ax.plot([], [], color=color, alpha=0.5,
                        linestyle='-', linewidth=1.5)
        scatter = ax.scatter([], [], color=color, s=120, zorder=5,
                             edgecolors='black', linewidth=1)
        text = ax.text(0, 0, '', fontsize=8, fontweight='bold',
                       ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.2",
                                 facecolor='white', alpha=0.85,
                                 edgecolor=color))

        lines.append(line)
        scatters.append(scatter)
        texts.append(text)

    return lines, scatters, texts


def _update(frame, lines, scatters, texts):
    """
    Функция обновления кадра анимации.

    Рассчитывает угловое положение и радиус каждой планеты для текущего
    момента времени и обновляет соответствующие графические элементы.

    Args:
        frame (int): Номер текущего кадра.
        lines (list): Список объектов-линий связи с центром.
        scatters (list): Список объектов-точек планет.
        texts (list): Список объектов-подписей.

    Returns:
        list: Все обновлённые графические элементы (для FuncAnimation).
    """
    # Время t меняется от 0 до ANIM_DURATION_YEARS за полный цикл анимации
    t = (frame / NUM_FRAMES) * ANIM_DURATION_YEARS

    for i, (name, suit, k, phase_shift_deg, T, color) in enumerate(planets_data):
        phase_shift_rad = np.radians(phase_shift_deg)

        # Угловое движение: базовая позиция на спирали + вращение со скоростью (2π / T) * t
        omega = (2 * np.pi) / T
        current_theta = (k * D_THETA_BASE) + phase_shift_rad + (omega * t)

        # Радиус по спиральной функции
        r = A + B_STEP * (k + (phase_shift_deg / 360.0) * NUM_SECTORS)

        # Обновление вектора связи с центром
        lines[i].set_data([phase_shift_rad, current_theta], [0, r])

        # Обновление точки планеты
        scatters[i].set_offsets([[current_theta, r]])

        # Обновление текста и позиции метки
        texts[i].set_position((current_theta, r + 1.2))
        texts[i].set_text(f"{name}\n[{k} {suit}]")

    ax = lines[0].axes
    ax.set_title(
        f"Спиральная Луланьская Матрица в движении\n"
        f"Время: {t:.2f} лет | 60 секторов",
        fontsize=11, fontweight='bold', pad=20
    )

    return lines + scatters + texts


def run_animation():
    """
    Создаёт и запускает анимацию спиральной Луланьской матрицы.

    Инициализирует фигуру, настраивает ось, создаёт графические элементы
    и запускает FuncAnimation с последующим отображением окна.

    Returns:
        matplotlib.animation.FuncAnimation: Объект анимации (необходим,
        чтобы сборщик мусора не уничтожил его до закрытия окна).
    """
    fig, ax = plt.subplots(figsize=(9, 9),
                            subplot_kw={'projection': 'polar'},
                            facecolor='#f8f9fa')

    _setup_axes(ax)
    lines, scatters, texts = _init_elements(ax)

    ani = FuncAnimation(
        fig, _update, fargs=(lines, scatters, texts),
        frames=NUM_FRAMES, interval=ANIM_INTERVAL_MS,
        blit=False, repeat=True
    )

    plt.tight_layout()
    plt.show()

    return ani



def run_animation_in_toplevel(parent):
    """
    Создаёт анимацию внутри tkinter Toplevel-окна.

    Встраивает фигуру matplotlib в окно Toplevel через FigureCanvasTkAgg.
    При закрытии окна корректно останавливает анимацию и освобождает
    ресурсы matplotlib, чтобы не блокировать консоль.

    Args:
        parent (tk.Tk или tk.Toplevel): Родительское окно tkinter.

    Returns:
        tuple[tk.Toplevel, FuncAnimation]: (окно, объект анимации).
    """
    top = tk.Toplevel(parent)
    top.title("Спиральная Луланьская Матрица")
#    top.geometry("700x700")
    top.geometry(f"700x700+{parent.winfo_rootx() + parent.winfo_width()}+{parent.winfo_rooty()}")

    top.resizable(True, True)

    fig, ax = plt.subplots(figsize=(7, 7),
                            subplot_kw={'projection': 'polar'},
                            facecolor='#f8f9fa')

    _setup_axes(ax)
    lines, scatters, texts = _init_elements(ax)

    ani = FuncAnimation(
        fig, _update, fargs=(lines, scatters, texts),
        frames=NUM_FRAMES, interval=ANIM_INTERVAL_MS,
        blit=False, repeat=True
    )

    canvas = FigureCanvasTkAgg(fig, master=top)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_close():
        ani.event_source.stop()
        plt.close(fig)
        top.destroy()

    top.protocol("WM_DELETE_WINDOW", _on_close)

    return top, ani



# === 4. ТОЧКА ВХОДА ПРИ ЗАПУСКЕ КАК ГЛАВНЫЙ СКРИПТ ===
if __name__ == "__main__":
    run_animation()
