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

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

import astronomy
import planet4

anim_window = None
anim_obj = None


def toggle_animation():
    global anim_window, anim_obj
    if anim_window is not None and anim_window.winfo_exists():
        on_anim_close()
    else:
        anim_window, anim_obj = planet4.run_animation_in_toplevel(root)
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


# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Астро-Калькулятор Резонансов и Чертогов")
root.geometry("640x380")
root.resizable(False, False)

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
