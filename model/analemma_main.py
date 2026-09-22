# ==============================================================================
# ИНТЕГРАЦИЯ АНАЛЕММЫ В main.py
# Добавить после импортов, до создания главного окна
# ==============================================================================
import calendar
import ephem
import tkinter as tk
import numpy as np          # <-- добавить
#import matplotlib.pyplot as plt
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analemma_calc import (
    set_observer, set_body, 
    analemma_xy, drawAnalemma,
    compute_analemma_for_time,
    BODY_MAP
)
import datetime

# Наблюдатель по умолчанию — Малага (Андалусия, Испания)
set_observer(36.7213, -4.4214, "Malaga")



from analemma_array import (
    PLANET_EPHEM_MAP,
    analemma_state
)


real_time_timer_id = None       # ID таймера реального времени
analemma_throttle_ms = 100      # минимальный интервал обновления (мс)
#simulated_hour = None    # «обучающий» час для кривой — растёт на 1 каждую секунду
simulated_time = None    # дробный час (например, 20.85 = 20:51)


# ------------------------------------------------------------------------------
# Нарисовать график аналемму
# ------------------------------------------------------------------------------




# ------------------------------------------------------------------------------
# Посчитать 24 аналеммы
# ------------------------------------------------------------------------------
def initial_analemma_plot(planet_name, dt, curve_hour=None):
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

    # 1. Загрузка всех 24 кривых (если год сменился или кэш пуст)
    if state['all_hourly_curves'] is None or state['cached_year'] != dt.year:
        # Используем функцию для единоразового подсчтека 24 аналемм. 
        # Она вернет список: [(0, points), (1, points), ..., (23, points)]
        hourly_data = compute_hourly_analemmas(
            year=dt.year,
            days=list(range(1, 32)),
            use_cable=False,
            above_horizon_only=False
        )

        curves_map = {}


        for h, points in hourly_data:
            if not points:
                continue
        
            xs = np.array([p[0] for p in points], dtype=float)
            ys = np.array([p[1] for p in points], dtype=float)

            curves_map[h] = (ys, xs)
        
        # Заполняем пропуски (если для какого-то часа точек нет, копируем соседний или оставляем None)
        state['hourly_data'] = [curves_map.get(h, None) for h in range(24)]
        state['cached_year'] = dt.year
        return state['hourly_data']


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

    # 1. Загрузка всех 24 кривых (если год сменился или кэш пуст)
#    if state['all_hourly_curves'] is None or state['cached_year'] != dt.year:

#    if state['hourly_data'] is None or state['cached_year'] != dt.year:
        # Используем вашу новую функцию! Она вернет список: [(0, points), (1, points), ..., (23, points)]
#        all_hourly_curves = state['hourly_data']
#        hourly_data =  state['hourly_data']
#        curves_map = {}


#        for h, points in hourly_data:
 #           if not points:
  #              continue
        
        # Преобразуем в удобный список индексов 0..23
        # Структура all_hourly_data: [(hour_int, [(x,y),...]), ...]
   #         xs = np.array([p[0] for p in points], dtype=float)
    #        ys = np.array([p[1] for p in points], dtype=float)

                # Unwrap азимута
                # Убираем скачок азимута через 0°/360°
#            xs = np.degrees(np.unwrap(np.radians(xs)))
#            curves_map[h] = (xs, ys)
        
        # Заполняем пропуски (если для какого-то часа точек нет, копируем соседний или оставляем None)
 #       state['hourly_data'] = [curves_map.get(h, None) for h in range(24)]
  #      state['cached_year'] = dt.year


    # 2. Определяем, какую кривую рисовать
    # Если передан конкретный час (для анимации) — берем его. Иначе — текущий реальный час.
    target_hour = int(curve_hour) if curve_hour is not None else dt.hour
    target_hour = target_hour % 24  # защита от переполнения

    current_curve = state['hourly_data'][target_hour]

    # 3. Отрисовка кривой
    if current_curve is not None:
#        xs, ys = current_curve
        xs = [p[0] for p in current_curve]
        ys = [p[1] for p in current_curve]
        ax.plot(xs, ys, color='#4a90d9', alpha=0.5, linewidth=1.2)
    else:
        # Если для этого часа нет данных (например, Солнце не восходило), можно нарисовать пустую рамку
        pass


    # 4. Маркер — зафиксированная позиция из state
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


    # 5. Оформление
    # Показываем, какая именно "часовая аналемма" сейчас активна
    display_hour = int(curve_hour) if curve_hour is not None else dt.hour
    hour_label = f"активная кривая: {display_hour:02d}:00"

    ax.set_title(
        f"Аналемма — {planet_name}\n{dt.strftime('%d.%m.%Y %H:%M:%S')}  |  {hour_label}",
        fontsize=9
    )

    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)

    ax.set_xlabel("Азимут, °")
    ax.set_ylabel("Высота, °")


    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_yticks([-90, -45, 0, 45, 90])

    ax.axvline(180, color="black", linewidth=1)
    ax.axhline(0, color="black", linewidth=2)
    ax.axhline(45, color="black", linewidth=1)
    ax.axhline(-45, color="black", linewidth=1)


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

    analemma_state[planet_name] = {
        'win':            win,
        'fig':            fig,
        'ax':             ax,
        'canvas':         canvas,
        'cached_curve':   None,
        'all_hourly_curves': None,   # <-- Сюда сохраним 24 кривые сразу
        'hourly_data': [None] * 25,
        'cached_hour':    -1,
        'cached_year':    -1,
        'last_update_ms': 0,
    }

    drawAnalemma(
        planet_name,
        ax,
        year=datetime.datetime.now().year
    )

    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_close():
        plt.close(fig)
        win.destroy()
        if planet_name in analemma_state:
            del analemma_state[planet_name]

    win.protocol("WM_DELETE_WINDOW", _on_close)



    # Первичная отрисовка — текущее системное время
#    analemma_state[planet_name]['all_hourly_curves'] = initial_analemma_plot(planet_name, datetime.datetime.now())


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

