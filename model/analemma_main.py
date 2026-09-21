# ==============================================================================
# ИНТЕГРАЦИЯ АНАЛЕММЫ В main.py
# Добавить после импортов, до создания главного окна
# ==============================================================================

import ephem
import tkinter as tk
import numpy as np          # <-- добавить
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analemma_calc import (
    set_observer, set_body, compute_analemma,
    compute_analemma_for_time, BODY_MAP
)
import datetime

# Наблюдатель по умолчанию — Малага (Андалусия, Испания)
set_observer(36.7213, -4.4214, "Malaga")

# Соответствие русских названий планет и имён в ephem.
# «Земля» показывает аналемму Солнца, видимую с Земли.
PLANET_EPHEM_MAP = {
    "Солнце":   "Sun",
    "Меркурий": "Mercury",
    "Венера":   "Venus",
    "Земля":    "Sun",
    "Луна":     "Moon",
    "Марс":     "Mars",
    "Юпитер":   "Jupiter",
    "Сатурн":   "Saturn",
    "Хирон":    None,   # Требует добавления ephem.Chiron() в BODY_MAP
}

# Хранилище состояний открытых окон аналемм
analemma_state = {}
real_time_timer_id = None       # ID таймера реального времени
analemma_throttle_ms = 100      # минимальный интервал обновления (мс)
#simulated_hour = None    # «обучающий» час для кривой — растёт на 1 каждую секунду
simulated_time = None    # дробный час (например, 20.85 = 20:51)



# ------------------------------------------------------------------------------
# ОСНОВНАЯ ФУНКЦИЯ ПЕРЕРИСОВКИ
# ------------------------------------------------------------------------------
def update_analemma_plot(planet_name, dt, curve_hour=None):
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

    effective_hour = curve_hour if curve_hour is not None else dt.hour

    # 1. Пересчёт кривой при смене часа или года
    if state['cached_hour'] != effective_hour or state['cached_year'] != dt.year:
        full_data = compute_analemma(
            year=dt.year,
            hours=[effective_hour],
            days=list(range(1, 32)),
            use_cable=True,
            above_horizon_only=False
        )
        if full_data:
            for _, points in full_data:
                if points:
                    xs = np.array([p[0] for p in points])
                    ys = np.array([p[1] for p in points])
                    # Unwrap азимута — убирает скачки на 0°/360°
                    xs = np.degrees(np.unwrap(np.radians(xs)))
                    state['cached_curve'] = (xs, ys)
        else:
            state['cached_curve'] = None
        state['cached_hour'] = effective_hour
        state['cached_year'] = dt.year

    # 2. Отрисовка кэшированной кривой
    if state['cached_curve'] is not None:
        xs, ys = state['cached_curve']
        ax.plot(xs, ys, color='#4a90d9', alpha=0.5, linewidth=1.2)

    # 3. Маркер — по реальному времени
    cur_x, cur_y = compute_analemma_for_time(dt, use_cable=True)

    # Unwrap для маркера — найти ближайший развёрнутый аналог
    if state['cached_curve'] is not None:
        xs_cached = state['cached_curve'][0]
        if len(xs_cached) > 0:
            # Подбираем представление cur_x, ближайшее к медиане кривой
            ref = np.median(xs_cached)
            cur_x = ref + ((cur_x - ref + 180) % 360) - 180

    if cur_y > 0:
        ax.plot(cur_x, cur_y, 'ro', markersize=8, zorder=5)
        ax.annotate(
            dt.strftime('%d.%m %H:%M'),
            xy=(cur_x, cur_y),
            xytext=(8, 8),
            textcoords='offset points',
            fontsize=8, color='red', fontweight='bold'
        )
    else:
        ax.plot(cur_x, cur_y, 'bx', markersize=8, zorder=5)

    # 4. Оформление
    hour_label = f"наблюдение: {int(simulated_time):02d}:{int(round((simulated_time % 1) * 60)):02d}"

    ax.set_title(
        f"Аналемма — {planet_name}\n{dt.strftime('%d.%m.%Y %H:%M:%S')}  |  {hour_label}",
        fontsize=9
    )

    ax.set_xlabel("Азимут, °")
    ax.set_ylabel("Высота, °")

    ax.relim()
    ax.autoscale_view()
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.set_xlim(xlim[0] - (xlim[1] - xlim[0]) * 0.1, xlim[1] + (xlim[1] - xlim[0]) * 0.1)
    ax.set_ylim(ylim[0] - (ylim[1] - ylim[0]) * 0.1, ylim[1] + (ylim[1] - ylim[0]) * 0.1)

    ax.grid(True, alpha=0.3)
    ax.set_aspect('auto')

    state['canvas'].draw()




# ------------------------------------------------------------------------------
# СОЗДАНИЕ ОКНА АНАЛЕММЫ
# ------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def open_analemma(planet_name):
    """
    Открывает окно аналеммы для выбранной планеты.
    Окно размещается под главным окном, плотно прилегая к нему.
    Первичная отрисовка — по текущему системному времени.
    """
    if planet_name in analemma_state and \
            analemma_state[planet_name]['win'].winfo_exists():
        analemma_state[planet_name]['win'].lift()
        return

    win = tk.Toplevel(root)
    win.title(f"Аналемма — {planet_name}")
    win.geometry(
        f"400x400+{root.winfo_rootx()}+{root.winfo_rooty() + root.winfo_height()}"
    )
    win.resizable(False, False)

    fig, ax = plt.subplots(figsize=(4, 4), facecolor='#f8f9fa')
    ax.set_facecolor('#f8f9fa')
    ax.set_title(f"Аналемма — {planet_name}", fontsize=11, fontweight='bold')
    ax.set_xlabel("Азимут, °")
    ax.set_ylabel("Высота, °")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_close():
        plt.close(fig)
        win.destroy()
        if planet_name in analemma_state:
            del analemma_state[planet_name]

    win.protocol("WM_DELETE_WINDOW", _on_close)

    analemma_state[planet_name] = {
        'win':            win,
        'fig':            fig,
        'ax':             ax,
        'canvas':         canvas,
        'cached_curve':   None,
        'cached_hour':    -1,
        'cached_year':    -1,
        'last_update_ms': 0,
    }

    # Первичная отрисовка — текущее системное время
    update_analemma_plot(planet_name, datetime.datetime.now())


# ------------------------------------------------------------------------------
# ТАЙМЕР РЕАЛЬНОГО ВРЕМЕНИ (пауза / анимация не запущена)
# ------------------------------------------------------------------------------
def start_real_time_analemma1():
    global real_time_timer_id, simulated_hour
    now = datetime.datetime.now()

    # Инициализация обучающего часа — текущий реальный час
    if simulated_hour is None:
        simulated_hour = now.hour

    for pname in list(analemma_state.keys()):
        update_analemma_plot(pname, now, curve_hour=simulated_hour)

    # Сдвигаем час на +1 для следующего тика (цикл 0..23)
    simulated_hour = (simulated_hour + 1) % 24

    real_time_timer_id = root.after(1000, start_real_time_analemma)

def start_real_time_analemma():
    global real_time_timer_id, simulated_time
    now = datetime.datetime.now()

    if simulated_time is None:
        # Инициализация от текущего реального времени (с минутами и секундами)
        simulated_time = now.hour + now.minute / 60.0 + now.second / 3600.0

    for pname in list(analemma_state.keys()):
        update_analemma_plot(pname, now, curve_hour=simulated_time)

    # Шаг: 1 час + 1 минута = 61/60 часа
    # 24*60 / 61 ≈ 23.6 — НЕ кратно, поэтому возникает биение
    simulated_time = (simulated_time + 61.0 / 60.0) % 24

    real_time_timer_id = root.after(1000, start_real_time_analemma)


def stop_real_time_analemma():
    """Останавливает таймер реального времени."""
    global real_time_timer_id
    if real_time_timer_id is not None:
        root.after_cancel(real_time_timer_id)
        real_time_timer_id = None


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
# ШАГ 7. ПРИВЯЗКА ВСЕХ КНОПОК ПЛАНЕТ К ФУНКЦИИ ОТКРЫТИЯ ОКНА
# ==============================================================================
# Добавить сразу после цикла создания кнопок planet_buttons:

# Перенесено в main
#for name in planet_buttons:
#    planet_buttons[name].config(
#        command=lambda n=name: open_analemma(n)
#    )


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

