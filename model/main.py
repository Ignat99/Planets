"""
Файл: main.py

Точка входа для графического интерфейса астро-калькулятора.

Реализует окно приложения на tkinter: выбор небесного тела, ввод даты,
кнопки смещения времени, отображение результатов расчёта (координаты,
дистанция, позиция в системе «Сварожьего Круга»).

Использует модуль astronomy для всех астрометрических вычислений.
При запуске как главный скрипт отображает интерфейс и обрабатывает
пользовательские действия.
"""

#import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
import io
import urllib.request
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


import astronomy
import planet4
from analemma_calc import (
    set_observer,
    set_body,
    compute_analemma,
    compute_analemma_for_time,
    BODY_MAP,
    deg_per_rad,
)

from analemma_main import (
    update_analemma_plot,
    open_analemma,
    start_real_time_analemma,
    stop_real_time_analemma,
#    PLANET_EPHEM_MAP,
)
# analemma_main.root = root


# Соответствие русских названий планет и имён в ephem.
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

anim_window = None
anim_obj = None


ICONS_DIR = "pic"
PLANET_ICONS = {
    "Солнце":   ("yarilo.jpg",       "http://homedevice.pro/wp-content/uploads/2025/12/yarilo.jpg"),
    "Меркурий": ("hors.jpg",         "http://homedevice.pro/wp-content/uploads/2025/12/hors.jpg"),
    "Венера":   ("mercana.jpg",      "http://homedevice.pro/wp-content/uploads/2025/12/mercana.jpg"),
    "Земля":    ("midgard.jpg",      "http://homedevice.pro/wp-content/uploads/2025/12/midgard.jpg"),
    "Луна":     ("lelya_mecyac.jpg", "http://homedevice.pro/wp-content/uploads/2025/12/lelya_mecyac.jpg"),
    "Марс":     ("oreya.jpg",        "http://homedevice.pro/wp-content/uploads/2025/12/oreya.jpg"),
    "Юпитер":   ("perun.jpg",        "http://homedevice.pro/wp-content/uploads/2025/12/perun.jpg"),
    "Сатурн":   ("stribog.jpg",      "http://homedevice.pro/wp-content/uploads/2025/12/stribog.jpg"),
    "Хирон":    ("indra.jpg",        "http://homedevice.pro/wp-content/uploads/2025/12/indra.jpg"),
}

ICON_SIZE = (40, 40)

# Инициализация наблюдателя (например, по умолчанию Малага)
set_observer(36.7213, -4.4214, "Malaga")

def init_analemma():
    # Открытие окна аналеммы
    analemma_main.open_analemma("Солнце")

def update_analemma():
    # Обновление аналеммы
    analemma_main.update_analemma_plot("Солнце", datetime.datetime.now())

def load_planet_icon(name):
    """Загружает иконку локально из pic/, при отсутствии — скачивает из интернета."""
    filename, url = PLANET_ICONS[name]
    local_path = os.path.join(ICONS_DIR, filename)

    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)

    if not os.path.exists(local_path):
        try:
            urllib.request.urlretrieve(url, local_path)
        except Exception:
            return None

    try:
        img = Image.open(local_path)
        img = img.resize(ICON_SIZE, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def toggle_animation():
    global anim_window, anim_obj
    if anim_window is not None and anim_window.winfo_exists():
        on_anim_close()
    else:
        try:
            start_dt = datetime.strptime(date_entry.get(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Ошибка формата", "Введите дату в формате ГГГГ-ММ-ДД ЧЧ:ММ")
            return
        anim_window, anim_obj = planet4.run_animation_in_toplevel(root, start_dt)
        anim_window.protocol("WM_DELETE_WINDOW", on_anim_close)
        btn_anim.config(text="Скрыть анимацию")


def on_anim_close():
    global anim_window, anim_obj
    if anim_obj is not None:
        anim_obj.event_source.stop()
        anim_obj = None
    if anim_window is not None:
        anim_window.destroy()
        anim_window = None
    plt.close('all')
    btn_anim.config(text="Показать анимацию")


def update_calc(days_offset=0):
    try:
        if days_offset != 0:
            current_dt = datetime.strptime(date_entry.get(), "%Y-%m-%d %H:%M")
            new_dt = current_dt + timedelta(days=days_offset)
            date_entry.delete(0, tk.END)
            date_entry.insert(0, new_dt.strftime("%Y-%m-%d %H:%M"))

        target_dt = datetime.strptime(date_entry.get(), "%Y-%m-%d %H:%M")
        selected_body = body_box.get()

        if selected_body != "Индра (Хирон(астероид))" and selected_body != "Седна (Земля Догоды)":
            lat, lon, distance = astronomy.calculate_position_planets(target_dt, selected_body)
        elif selected_body == "Седна (Земля Догоды)":
            center = 10
            target = 20090377
            lat, lon, distance = astronomy.get_spherical_coords(astronomy.sedna_eph, center, target, astronomy.jd)
            astronomy.sedna_eph.close()
        else:
            center = 10
            target = 20002060
            lat, lon, distance = astronomy.get_spherical_coords(astronomy.kernel, center, target, astronomy.jd)
            astronomy.kernel.close()

        deg, chertog, zal, stol, lavka, mesto, dist = astronomy.calculate_position_chertog(lat, lon, distance)

        lbl_deg_val.config(text=f"{deg:.4f}°")
        lbl_chertog_val.config(
            text=f"Чертог {chertog} — Зал {zal} — Стол {stol} — Лавка {lavka} — Место {mesto}"
        )
        lbl_dist_val.config(text=f"{dist:.4f} а.е.")

    except ValueError:
        messagebox.showerror("Ошибка формата", "Введите дату в формате ГГГГ-ММ-ДД ЧЧ:ММ")


def on_main_close():
    global anim_window, anim_obj
    if anim_obj is not None:
        anim_obj.event_source.stop()
    plt.close('all')
    root.destroy()

analemma_windows = {}

def open_analemma(planet_name):
    if planet_name in analemma_windows and analemma_windows[planet_name].winfo_exists():
        analemma_windows[planet_name].lift()
        return

    win = tk.Toplevel(root)
    win.title(f"Аналемма — {planet_name}")
    win.geometry(f"400x400+{root.winfo_rootx()}+{root.winfo_rooty() + root.winfo_height()}")
    win.resizable(False, False)

    fig, ax = plt.subplots(figsize=(4, 4), facecolor='#f8f9fa')
    ax.set_facecolor('#f8f9fa')
    ax.set_title(f"Аналемма {planet_name}", fontsize=11, fontweight='bold')
    ax.set_xlabel("Азимут, °")
    ax.set_ylabel("Высота, °")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-180, 180)
    ax.set_ylim(0, 90)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_close():
        plt.close(fig)
        win.destroy()
        if planet_name in analemma_windows:
            del analemma_windows[planet_name]

    win.protocol("WM_DELETE_WINDOW", _on_close)
    analemma_windows[planet_name] = win



# --- Создание графического интерфейса ---
root = tk.Tk()

# Передаём ссылку на root в analemma_main
import analemma_main
analemma_main.root = root

root.title("Астро-Калькулятор Резонансов и Чертогов")
root.geometry("640x620")
root.resizable(False, True)

style = ttk.Style()
style.theme_use('clam')

ttk.Label(root, text="Небесное тело:", font=('Helvetica', 10, 'bold')).pack(anchor="w", padx=20, pady=(15, 2))
body_box = ttk.Combobox(root, values=list(astronomy.BODIES.keys()), state="readonly", font=('Helvetica', 10))
body_box.current(4)
body_box.pack(fill="x", padx=20)

ttk.Label(root, text="Дата и время (UTC):", font=('Helvetica', 10, 'bold')).pack(anchor="w", padx=20, pady=(10, 2))
date_entry = ttk.Entry(root, font=('Helvetica', 10))
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
date_entry.pack(fill="x", padx=20)

btn_frame = ttk.Frame(root)
btn_frame.pack(fill="x", padx=20, pady=10)

ttk.Button(btn_frame, text="+1 День", command=lambda: update_calc(1)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+1 Месяц (30d)", command=lambda: update_calc(30)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+1 Год (365d)", command=lambda: update_calc(365)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+16 Лет (Круг)", command=lambda: update_calc(5844)).pack(side="left", expand=True, fill="x", padx=2)

btn_calc = ttk.Button(root, text="Рассчитать точные координаты", command=lambda: update_calc(0))
btn_calc.pack(fill="x", padx=20, pady=5)

btn_anim = ttk.Button(root, text="Показать анимацию", command=toggle_animation)
btn_anim.pack(fill="x", padx=20, pady=5)

# --- Ряд кнопок планет ---
planet_frame = tk.LabelFrame(root, text="Аналеммы планет", padx=5, pady=5)
planet_frame.pack(pady=10, padx=10, fill="x")

planet_buttons = {}
planet_icons = {}

# 1. Цикл создания кнопок для всех планет
for name in PLANET_ICONS:
    icon = load_planet_icon(name)
    if icon is not None:
        planet_icons[name] = icon
        btn = tk.Button(planet_frame, image=icon, text=name,
                        compound="top", font=("Helvetica", 8),
                        relief="raised", bd=1)
    else:
        btn = tk.Button(planet_frame, text=name,
                        compound="top", font=("Helvetica", 8),
                        relief="raised", bd=1)
    btn.pack(side="left", padx=3, pady=2, expand=True)
    planet_buttons[name] = btn
    planet_buttons[name].config(command=lambda name=name: analemma_main.open_analemma(name))

# Назначаем действие конкретно для кнопки Меркурия (из вашего кода)
#planet_buttons["Меркурий"].config(command=lambda: open_analemma("Меркурий"))

# ==============================================================================
# ШАГ 7. ПРИВЯЗКА ВСЕХ КНОПОК ПЛАНЕТ К ФУНКЦИИ ОТКРЫТИЯ ОКНА
# ==============================================================================
# Добавить сразу после цикла создания кнопок planet_buttons:

#for name in planet_buttons:
#    planet_buttons[name].config(
#        command=lambda n=name: open_analemma(n)
#    )

# 2. Добавление новых управляющих кнопок (привязываем к root, как в вашем примере)
#btn_analemma = tk.Button(root, text="Аналемма", command=init_analemma)
#btn_analemma.pack(pady=5)  # Добавил небольшой отступ для красоты

#btn_update = tk.Button(root, text="Обновить", command=update_analemma)
#btn_update.pack(pady=5)

# 3. Запуск фонового таймера реального времени
analemma_main.start_real_time_analemma()



res_frame = ttk.LabelFrame(root, text=" Точные координаты ", padding=10)
res_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

ttk.Label(res_frame, text="Эклиптическая долгота:").grid(row=0, column=0, sticky="w", pady=2)
lbl_deg_val = ttk.Label(res_frame, text="-", font=('Helvetica', 10, 'bold'))
lbl_deg_val.grid(row=0, column=1, sticky="e", pady=2)

ttk.Label(res_frame, text="Координата Сварожьего Круга:").grid(row=1, column=0, sticky="w", pady=2)
lbl_chertog_val = ttk.Label(res_frame, text="-", font=('Helvetica', 10, 'bold'), foreground="#0066cc")
lbl_chertog_val.grid(row=1, column=1, sticky="e", pady=2)

ttk.Label(res_frame, text="Дистанция от Земли:").grid(row=2, column=0, sticky="w", pady=2)
lbl_dist_val = ttk.Label(res_frame, text="-", font=('Helvetica', 10, 'bold'))
lbl_dist_val.grid(row=2, column=1, sticky="e", pady=2)

root.protocol("WM_DELETE_WINDOW", on_main_close)

root.mainloop()
