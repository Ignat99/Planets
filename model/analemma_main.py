# ==============================================================================
# ИНТЕГРАЦИЯ АНАЛЕММЫ В main.py
# Добавить после импортов, до создания главного окна
# ==============================================================================
import ephem
import tkinter as tk
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analemma_calc import (
    set_observer, set_body, 
    analemma_xy, drawAnalemma,
    BODY_MAP
)
import datetime

# Наблюдатель по умолчанию — Малага (Андалусия, Испания)
set_observer(36.7213, -4.4214, "Malaga")



from analemma_array import (
    PLANET_EPHEM_MAP,
    analemma_state,
    CONTRAST_LEVELS,
    show_five_curves,
    show_lines
)


real_time_timer_id = None       # ID таймера реального времени
analemma_throttle_ms = 100      # минимальный интервал обновления (мс)
#simulated_hour = None    # «обучающий» час для кривой — растёт на 1 каждую секунду
simulated_time = None    # дробный час (например, 20.85 = 20:51)


# ------------------------------------------------------------------------------
# Нарисовать график аналемму
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# ОСНОВНАЯ ФУНКЦИЯ ПЕРЕРИСОВКИ
# ------------------------------------------------------------------------------

def update_analemma_plot(planet_name, dt, curve_hour=None):
    global show_five_curves

    if planet_name not in analemma_state:
        return
    state = analemma_state[planet_name]
    if not state['win'].winfo_exists():
        return

    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    if now_ms - state['last_update_ms'] < analemma_throttle_ms:
        return
    state['last_update_ms'] = now_ms

    eng_name = PLANET_EPHEM_MAP.get(planet_name)
    if eng_name is None:
        return
    set_body(eng_name)

    ax = state['ax']
    ax.clear()
    ax.set_facecolor('#f8f9fa')

    center_hour = int(curve_hour) if curve_hour is not None else dt.hour

    if show_five_curves:
        hour_offsets = [-2, -1, 0, 1, 2]
    else:
        hour_offsets = [0]

    for i, offset in enumerate(hour_offsets):
        h = (center_hour + offset) % 24
        contrast = CONTRAST_LEVELS[i] if show_five_curves else 0.90

        curve = state['hourly_data'][h]
        if curve is not None:
            _draw_curve_on_ax(ax, curve, contrast)

    # Маркер
    if 'marker_pos' in state and state['marker_pos'] is not None:
        cur_x, cur_y = state['marker_pos']
        marker_dt = state.get('marker_dt', dt)
        if cur_y > 0:
            ax.plot(cur_x, cur_y, 'ro', markersize=8, zorder=5)
            ax.annotate(
                marker_dt.strftime('%d.%m %H:%M'),
                xy=(cur_x, cur_y),
                xytext=(8, 8),
                textcoords='offset points',
                fontsize=8, color='red', fontweight='bold'
            )
        else:
            ax.plot(cur_x, cur_y, 'bx', markersize=8, zorder=5)

    # Сетка
    ax.axvline(180, color="black", linewidth=1)
    ax.axhline(0, color="black", linewidth=2)
    ax.axhline(45, color="black", linewidth=1)
    ax.axhline(-45, color="black", linewidth=1)

    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_yticks([-90, -45, 0, 45, 90])
    ax.set_xlabel("Азимут, °")
    ax.set_ylabel("Высота, °")
    ax.grid(True, alpha=0.3)
    ax.set_aspect('auto')

    curve_label = "5 кривых" if show_five_curves else "1 кривая"
    render_label = "линии" if show_lines else "точки"
    ax.set_title(
        f"Аналемма — {planet_name}\n{dt.strftime('%d.%m.%Y %H:%M:%S')}  |  {center_hour:02d}:00  |  {curve_label}  |  {render_label}",
        fontsize=9
    )


    state['canvas'].draw()




# ------------------------------------------------------------------------------
# СОЗДАНИЕ ОКНА АНАЛЕММЫ
# ------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def _get_current_hour():
    """Возвращает текущий час — из симуляции или системного времени."""
    return simulated_time if simulated_time is not None else datetime.datetime.now().hour


def _draw_curve_on_ax(ax, curve, contrast):
    """Рисует одну кривую на оси — линиями или точками, в зависимости от show_lines."""
    if show_lines:
        xs = [p[0] for p in curve]
        ys = [p[1] for p in curve]

        xs_above, ys_above = [], []
        xs_below, ys_below = [], []
        for x, y in zip(xs, ys):
            if y > 0:
                if xs_below:
                    ax.plot(xs_below, ys_below, '-', color='blue',
                            alpha=contrast, linewidth=1.5)
                    xs_below, ys_below = [], []
                xs_above.append(x)
                ys_above.append(y)
            else:
                if xs_above:
                    ax.plot(xs_above, ys_above, '-', color='gold',
                            alpha=contrast, linewidth=1.5)
                    xs_above, ys_above = [], []
                xs_below.append(x)
                ys_below.append(y)

        if xs_above:
            ax.plot(xs_above, ys_above, '-', color='gold',
                    alpha=contrast, linewidth=1.5)
        if xs_below:
            ax.plot(xs_below, ys_below, '-', color='blue',
                    alpha=contrast, linewidth=1.5)
    else:
        for x, y in curve:
            if y > 0:
                ax.plot(x, y, 'o', markersize=2, color='gold', alpha=contrast)
            else:
                ax.plot(x, y, 'o', markersize=2, color='blue', alpha=contrast)


def toggle_curves(planet_name):
    global show_five_curves
    show_five_curves = not show_five_curves
    update_analemma_plot(planet_name, datetime.datetime.now(),
                         curve_hour=_get_current_hour())


def toggle_render_mode(planet_name):
    global show_lines
    show_lines = not show_lines
    update_analemma_plot(planet_name, datetime.datetime.now(),
                         curve_hour=_get_current_hour())



def open_analemma(planet_name):
    if planet_name in analemma_state and \
            analemma_state[planet_name]['win'].winfo_exists():
        analemma_state[planet_name]['win'].lift()
        return

    win = tk.Toplevel(root)
    win.title(f"Аналемма — {planet_name}")
    win.geometry(
        f"520x620+{root.winfo_rootx()}+{root.winfo_rooty() + root.winfo_height()}"
    )
    win.resizable(False, False)

    fig, ax = plt.subplots(figsize=(5.2, 5.2), facecolor='#f8f9fa')
    ax.set_facecolor('#f8f9fa')
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    ax.grid(True, alpha=0.3)
#    fig.tight_layout()
    # Оставляем отступы: сверху под заголовок, снизу под кнопку
    fig.subplots_adjust(top=0.85, bottom=0.15, left=0.12, right=0.95)

    canvas = FigureCanvasTkAgg(fig, master=win)

    analemma_state[planet_name] = {
        'win':            win,
        'fig':            fig,
        'ax':             ax,
        'canvas':         canvas,
        'hourly_data':    [None] * 25,
        'cached_year':    -1,
        'last_update_ms': 0,
    }

    drawAnalemma(
        planet_name,
        ax,
        year=datetime.datetime.now().year
    )

    # Кнопки в одну строку: слева — 1/5 кривых, справа — линии/точки
    btn_frame = tk.Frame(win)
    btn_frame.pack(side="bottom", pady=6)
#    btn_toggle = tk.Button(win, text="1 / 5 кривых", command=toggle_curves)

#----
    btn_toggle = tk.Button(btn_frame, text="1 / 5 кривых",
                           command=lambda: toggle_curves(planet_name))

    btn_toggle.pack(side="left", padx=8)


    btn_render = tk.Button(btn_frame, text="линии / точки",
                           command=lambda: toggle_render_mode(planet_name))
    btn_render.pack(side="right", padx=8)


#    canvas.draw()
#    canvas.get_tk_widget().pack(fill="both", expand=True)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)


    # Переключатель 1 / 5 кривых
#    def toggle_curves():
#        global show_five_curves
#        show_five_curves = not show_five_curves
#        update_analemma_plot(planet_name, datetime.datetime.now(),
#                             curve_hour=simulated_time if simulated_time is not None
#                             else datetime.datetime.now().hour)

#    btn_toggle = tk.Button(win, text="1 / 5 кривых", command=toggle_curves)
#    btn_toggle.pack(side="bottom", pady=2)

    update_analemma_plot(planet_name, datetime.datetime.now(), curve_hour=datetime.datetime.now().hour)

    def _on_close():
        plt.close(fig)
        win.destroy()
        if planet_name in analemma_state:
            del analemma_state[planet_name]

    win.protocol("WM_DELETE_WINDOW", _on_close)



# ------------------------------------------------------------------------------
# ТАЙМЕР РЕАЛЬНОГО ВРЕМЕНИ (пауза / анимация не запущена)
# ------------------------------------------------------------------------------
def start_real_time_analemma():
    global real_time_timer_id, simulated_time

    # Фиксируем время старта один раз — маркер и дата не будут двигаться
    if simulated_time is None:
        simulated_time = datetime.datetime.now().hour

    # Используем одно и то же зафиксированное время для всех тиков
    if not hasattr(start_real_time_analemma, 'fixed_dt'):
        start_real_time_analemma.fixed_dt = datetime.datetime.now()

    fixed_dt = start_real_time_analemma.fixed_dt

    for pname in list(analemma_state.keys()):
        update_analemma_plot(pname, fixed_dt, curve_hour=simulated_time)

    simulated_time = (simulated_time + 1) % 24

    real_time_timer_id = root.after(1000, start_real_time_analemma)


def stop_real_time_analemma():
    global real_time_timer_id
    if real_time_timer_id is not None:
        root.after_cancel(real_time_timer_id)
        real_time_timer_id = None
    # Сбрасываем зафиксированное время, чтобы при следующем запуске взять новое
    if hasattr(start_real_time_analemma, 'fixed_dt'):
        del start_real_time_analemma.fixed_dt


# ==============================================================================
# ТОЧКИ ИНТЕГРАЦИИ В СУЩЕСТВУЮЩИЙ КОД
# ==============================================================================
#
# 1. В функции toggle_pause():
#
#    При постановке на паузу (is_paused становится True):
#        start_real_time_analemma()
#
#    При снятии паузы (is_paused становится False):
#        stop_real_time_analemma()
#
# -------------------------------------------------------------------------
#
# 2. В функции _update() внутри run_animation_in_toplevel():
#
#    После вычисления текущего времени анимации (переменная current_dt
#    типа datetime.datetime) добавить:
#
#        if analemma_state:
#            stop_real_time_analemma()
#            for pname in list(analemma_state.keys()):
#                update_analemma_plot(pname, current_dt)
#
# -------------------------------------------------------------------------
#
# 3. Если в _update() время хранится как t_years (float, годы от старта),
#    преобразование в datetime:
#
#        start_date = datetime.datetime(int(my_year), 1, 1)
#        current_dt = start_date + datetime.timedelta(days=t_years * 365.25)
#
# -------------------------------------------------------------------------
#
# 4. При закрытии окна анимации (если анимация была запущена):
#
#        stop_real_time_analemma()
#        start_real_time_analemma()  # если есть открытые окна аналемм
#                                   # и выбрано текущее время
#
# ==============================================================================
# ШАГ 5. ДОБАВЛЕНИЕ ХИРОНА В analemma_calc.py
# ==============================================================================
# В файле analemma_calc.py заменить словарь BODY_MAP на:

BODY_MAP = {
    "Sun":     ephem.Sun,
    "Moon":    ephem.Moon,
    "Mercury": ephem.Mercury,
    "Venus":   ephem.Venus,
    "Mars":    ephem.Mars,
    "Jupiter": ephem.Jupiter,
    "Saturn":  ephem.Saturn,
    "Neptune": ephem.Neptune,
#    "Chiron":  ephem.Chiron,      # добавлено
}


# ==============================================================================
# ШАГ 6. ОБНОВЛЁННЫЙ PLANET_EPHEM_MAP (в main.py, заменить прежний)
# ==============================================================================

PLANET_EPHEM_MAP = {
    "Солнце":   "Sun",
    "Меркурий": "Mercury",
    "Венера":   "Venus",
    "Земля":    "Sun",
    "Луна":     "Moon",
    "Марс":     "Mars",
    "Юпитер":   "Jupiter",
    "Сатурн":   "Saturn",
    "Хирон":    "Chiron",
}




# ==============================================================================
# ШАГ 8. ИЗМЕНЕНИЯ В toggle_pause() — запуск/остановка таймера
# ==============================================================================
# Заменить существующую функцию toggle_pause на:

def toggle_pause():
#    nonlocal is_paused
    global is_paused
    if is_paused:
        # Снимаем паузу — анимация продолжается
        btn_pause.config(text="||")
        ani.event_source.start()
        is_paused = False
        # Останавливаем таймер реального времени
        stop_real_time_analemma()
    else:
        # Ставим паузу — анимация останавливается
        btn_pause.config(text="▶")
        ani.event_source.stop()
        is_paused = True
        # Запускаем таймер реального времени для аналемм
        start_real_time_analemma()


# ==============================================================================
# ШАГ 9. ВСТАВКА В _update() ВНУТРИ run_animation_in_toplevel()
# ==============================================================================
# Найти функцию _update(frame) внутри run_animation_in_toplevel()
# и добавить блок обновления аналемм ПОСЛЕ вычисления current_dt:

def _update(frame):
    # ... существующий код расчёта current_dt ...

    # --- Обновление окон аналемм синхронно с анимацией ---
    if analemma_state:
        # Таймер реального времени не нужен — время идёт из анимации
        stop_real_time_analemma()
        for pname in list(analemma_state.keys()):
            update_analemma_plot(pname, current_dt)

    # ... остальной существующий код ...


# ==============================================================================
# ШАГ 10. ПРИ ЗАКРЫТИИ ОКНА АНИМАЦИИ
# ==============================================================================
# В функции закрытия окна анимации (в _on_close или аналогичной) добавить:

def _on_anim_close():
    ani.event_source.stop()
    stop_real_time_analemma()
    # Если есть открытые окна аналемм — запускаем реальное время
    if analemma_state:
        start_real_time_analemma()
    # ... остальной код закрытия ...


# ==============================================================================
# ШАГ 11. ПРИ ЗАКРЫТИИ ГЛАВНОГО ОКНА — ОЧИСТКА
# ==============================================================================
# Добавить в root.protocol("WM_DELETE_WINDOW", ...) или on_closing():

def on_closing():
    stop_real_time_analemma()
    for pname in list(analemma_state.keys()):
        if analemma_state[pname]['win'].winfo_exists():
            plt.close(analemma_state[pname]['fig'])
            analemma_state[pname]['win'].destroy()
    root.destroy()

