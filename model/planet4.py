"""
Файл: planet4.py

Спиральная Луланьская Матрица — модуль визуализации движения планет
на 60-секторной полярной сетке с реальными эфемеридными данными NASA SPK.

Использует модуль astronomy для получения координат из bsp-файлов.
Анимация отображает реальные траектории с эффектами Кеплеровского
движения: ускорение вблизи перигелия, замедление вблизи афелия,
эллиптичность и возмущения орбит. Для каждой планеты рисуется полная
орбита (полупрозрачная линия) и яркий след за последние N кадров,
что делает переменную скорость движения хорошо различимой.

При отсутствии модуля astronomy переходит на упрощённую модель
равномерного вращения. Может использоваться как импортируемый модуль
(доступны planets_data, параметры сетки и функции run_animation /
run_animation_in_toplevel) либо как самостоятельный скрипт.
"""

import numpy as np
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import astronomy
    USE_REAL_EPHEMERIS = True
except ImportError:
    USE_REAL_EPHEMERIS = False


# === 1. ДАННЫЕ ПЛАНЕТ ===
# Формат: (Название, Масть, Коэффициент k, Сдвиг масти в градусах,
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
D_THETA_BASE = 2 * np.pi / NUM_SECTORS
A = 1.0
B_STEP = 0.8
NUM_FRAMES = 360
ANIM_INTERVAL_MS = 30
ANIM_DURATION_YEARS = 5.0
R_SCALE = 5.0          # Масштаб расстояния (sqrt-компрессия)
TRAIL_LENGTH = 30      # Длина яркого следа в кадрах


# === 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def _find_astronomy_name(display_name, bodies_keys):
    """
    Находит ключ в astronomy.BODIES по современному названию планеты.
    planet4 использует формат «Славянское (Современное)»,
    astronomy.BODIES — «Современное (Славянское)» или подобный.
    """
    if "(" in display_name:
        modern = display_name.split("(")[1].rstrip(")").strip()
    else:
        modern = display_name
    for key in bodies_keys:
        if modern in key:
            return key
    return None


def _scale_distance(r_au):
    """
    Масштабирует расстояние в а.е. для полярного графика.
    Использует квадратичный корень для компрессии: внутренние
    планеты остаются различимыми, а внешние не уходят за пределы графика.
    """
    return A + B_STEP * np.sqrt(max(r_au, 0.001)) * R_SCALE


def _simple_position(i, frame):
    """
    Позиция по упрощённой модели равномерного вращения (fallback).
    """
    name, suit, k, phase_shift_deg, T, color = planets_data[i]
    t = (frame / NUM_FRAMES) * ANIM_DURATION_YEARS
    omega = (2 * np.pi) / T
    theta = (k * D_THETA_BASE) + np.radians(phase_shift_deg) + (omega * t)
    r = A + B_STEP * (k + (phase_shift_deg / 360.0) * NUM_SECTORS)
    return theta, r


# === 4. ПРЕДВАРИТЕЛЬНЫЙ РАСЧЁТ ПОЗИЦИЙ ===

def precompute_positions(start_date=None, progress_callback=None):
    """
    Предварительно вычисляет координаты всех планет для всех кадров.

    При наличии модуля astronomy использует реальные эфемеридные данные
    из bsp-файлов NASA. Иначе — упрощённая модель равномерного вращения.

    Args:
        start_date (datetime): Начальная дата. По умолчанию — J2000.
        progress_callback (callable): Функция (done, total) для индикатора.

    Returns:
        list[np.ndarray]: Список массивов (NUM_FRAMES+1, 2) — (theta, r)
                          для каждой планеты.
    """
    if start_date is None:
        start_date = datetime(2000, 1, 1, 12, 0)

    total = len(planets_data) * (NUM_FRAMES + 1)
    done = 0
    positions = []

    bodies_keys = list(astronomy.BODIES.keys()) if USE_REAL_EPHEMERIS else []

    for i, (name, suit, k, phase_shift_deg, T, color) in enumerate(planets_data):
        planet_pos = np.zeros((NUM_FRAMES + 1, 2))

        astro_name = _find_astronomy_name(name, bodies_keys) if USE_REAL_EPHEMERIS else None

        if astro_name is not None:
            for frame in range(NUM_FRAMES + 1):
                t_days = (frame / NUM_FRAMES) * ANIM_DURATION_YEARS * 365.25
                dt = start_date + timedelta(days=t_days)
                try:
                    lat, lon, distance = astronomy.calculate_position_planets(dt, astro_name)
                    theta = np.radians(lon)
                    r = _scale_distance(distance)
                except Exception:
                    theta, r = _simple_position(i, frame)
                planet_pos[frame] = [theta, r]

                done += 1
                if progress_callback and done % 50 == 0:
                    progress_callback(done, total)
        else:
            for frame in range(NUM_FRAMES + 1):
                theta, r = _simple_position(i, frame)
                planet_pos[frame] = [theta, r]
                done += 1
                if progress_callback and done % 50 == 0:
                    progress_callback(done, total)

        positions.append(planet_pos)
        if progress_callback:
            progress_callback(done, total)

    return positions


# === 5. НАСТРОЙКА ГРАФИКА ===

def _setup_axes(ax):
    """
    Настраивает полярную ось: 60-ричная сетка, 6 главных осей,
    нулевая точка на «Севере».
    """
    ax.set_facecolor('#ffffff')

    sector_angles = np.linspace(0, 2 * np.pi, NUM_SECTORS, endpoint=False)
    for angle in sector_angles:
        ax.plot([angle, angle], [0, 20], color='#e0e0e0',
                linestyle=':', linewidth=0.8, zorder=1)

    for main_angle in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        ax.plot([main_angle, main_angle], [0, 20], color='#b0bec5',
                linestyle='--', linewidth=1.2, zorder=2)

    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 22)
    ax.set_yticklabels([])


def _init_elements(ax):
    """
    Создаёт графические элементы для каждой планеты:
    линию полной орбиты, линию яркого следа, точку и подпись.

    Returns:
        tuple: (orbit_lines, trail_lines, scatters, texts)
    """
    orbit_lines = []
    trail_lines = []
    scatters = []
    texts = []

    for name, suit, k, phase_shift_deg, T, color in planets_data:
        orbit_line, = ax.plot([], [], color=color, alpha=0.15,
                               linestyle='-', linewidth=1, zorder=1)
        trail_line, = ax.plot([], [], color=color, alpha=0.6,
                              linestyle='-', linewidth=2, zorder=3)
        scatter = ax.scatter([], [], color=color, s=120, zorder=5,
                             edgecolors='black', linewidth=1)
        text = ax.text(0, 0, '', fontsize=8, fontweight='bold',
                       ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.2",
                                 facecolor='white', alpha=0.85,
                                 edgecolor=color))

        orbit_lines.append(orbit_line)
        trail_lines.append(trail_line)
        scatters.append(scatter)
        texts.append(text)

    return orbit_lines, trail_lines, scatters, texts


# === 6. ФУНКЦИЯ ОБНОВЛЕНИЯ КАДРА ===

def _update(frame, orbit_lines, trail_lines, scatters, texts, positions):
    """
    Обновляет кадр анимации, используя предвычисленные позиции.

    Для каждой планеты:
    — рисует полную орбиту (полупрозрачная линия);
    — рисует яркий след за последние TRAIL_LENGTH кадров;
    — помещает точку текущего положения и подпись.

    Неравномерность движения видна по переменной плотности точек
    на ярком следе: вблизи перигелия след длиннее (быстрее),
    вблизи афелия — короче (медленнее).
    """
    t_years = (frame / NUM_FRAMES) * ANIM_DURATION_YEARS

    for i, (name, suit, k, phase_shift_deg, T, color) in enumerate(planets_data):
        pos = positions[i]

        # Полная орбита
        thetas = pos[:, 0]
        rs = pos[:, 1]
        thetas_unwrapped = np.unwrap(thetas)
        orbit_lines[i].set_data(thetas_unwrapped, rs)

        # Яркий след (последние TRAIL_LENGTH позиций)
        start = max(0, frame - TRAIL_LENGTH)
        trail_thetas = pos[start:frame + 1, 0]
        trail_rs = pos[start:frame + 1, 1]
        trail_thetas_unwrapped = np.unwrap(trail_thetas)
        trail_lines[i].set_data(trail_thetas_unwrapped, trail_rs)

        # Текущая позиция
        theta, r = pos[frame]
        scatters[i].set_offsets([[theta, r]])

        # Подпись
        texts[i].set_position((theta, r + 1.2))
        texts[i].set_text(f"{name}\n[{k} {suit}]")

    ax = orbit_lines[0].axes
    mode = "реальные эфемериды NASA" if USE_REAL_EPHEMERIS else "упрощённая модель"
    ax.set_title(
        f"Спиральная Луланьская Матрица — {mode}\n"
        f"Время: +{t_years:.2f} лет от J2000 | 60 секторов",
        fontsize=11, fontweight='bold', pad=20
    )

    return orbit_lines + trail_lines + scatters + texts


# === 7. ЗАПУСК АНИМАЦИИ ===

def run_animation():
    """
    Создаёт и запускает анимацию в отдельном окне matplotlib.
    Предварительно вычисляет позиции всех планет.
    """
    print("Предварительный расчёт позиций планет...")
    positions = precompute_positions()
    print("Готово, запуск анимации.")

    fig, ax = plt.subplots(figsize=(9, 9),
                            subplot_kw={'projection': 'polar'},
                            facecolor='#f8f9fa')

    _setup_axes(ax)
    orbit_lines, trail_lines, scatters, texts = _init_elements(ax)

    ani = FuncAnimation(
        fig, _update,
        fargs=(orbit_lines, trail_lines, scatters, texts, positions),
        frames=NUM_FRAMES, interval=ANIM_INTERVAL_MS,
        blit=False, repeat=True
    )

    plt.tight_layout()
    plt.show()

    return ani


def run_animation_in_toplevel(parent):
    """
    Создаёт анимацию внутри tkinter Toplevel-окна.

    Предварительно вычисляет позиции планет с индикатором прогресса.
    Встраивает фигуру matplotlib через FigureCanvasTkAgg.
    При закрытии корректно останавливает анимацию и освобождает ресурсы.

    Args:
        parent (tk.Tk или tk.Toplevel): Родительское окно tkinter.

    Returns:
        tuple[tk.Toplevel, FuncAnimation]: (окно, объект анимации).
    """
    # --- Окно индикатора прогресса ---
    progress_win = tk.Toplevel(parent)
    progress_win.title("Расчёт эфемерид")
    progress_win.geometry("320x120")
    progress_win.transient(parent)
    tk.Label(progress_win, text="Вычисление позиций планет из bsp-файлов...",
             font=('Helvetica', 10)).pack(pady=(15, 5))
    progress_bar = ttk.Progressbar(progress_win, maximum=100, mode='determinate')
    progress_bar.pack(pady=5, padx=30, fill='x')
    status_label = tk.Label(progress_win, text="Подготовка...",
                            font=('Helvetica', 9))
    status_label.pack(pady=5)
    progress_win.update()

    def on_progress(done, total):
        pct = int((done / total) * 100) if total > 0 else 0
        progress_bar['value'] = pct
        status_label.config(text=f"Обработано {done} из {total} позиций")
        progress_win.update()

    positions = precompute_positions(progress_callback=on_progress)
    progress_win.destroy()

    # --- Окно анимации ---
    top = tk.Toplevel(parent)
    top.title("Спиральная Луланьская Матрица")
    top.geometry(f"700x700+{parent.winfo_rootx() + parent.winfo_width()}+{parent.winfo_rooty()}")
    top.resizable(True, True)

    fig, ax = plt.subplots(figsize=(7, 7),
                            subplot_kw={'projection': 'polar'},
                            facecolor='#f8f9fa')

    _setup_axes(ax)
    orbit_lines, trail_lines, scatters, texts = _init_elements(ax)

    ani = FuncAnimation(
        fig, _update,
        fargs=(orbit_lines, trail_lines, scatters, texts, positions),
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


# === 8. ТОЧКА ВХОДА ===
if __name__ == "__main__":
    run_animation()
