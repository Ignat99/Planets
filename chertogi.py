import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from skyfield.api import load

# Загружаем эфемериды NASA и шкалу времени
planets = load('de421.bsp')
ts = load.timescale()

# Словарь небесных тел (NASA ID / Имена)
BODIES = {
    "Солнце": planets['sun'],
    "Луна (Месяцъ)": planets['moon'],
    "Меркурий (Хорсъ)": planets['mercury'],
    "Венера (Заря-Мерцана)": planets['venus'],
    "Марс (Орей)": planets['mars'],
    "Юпитер (Перун)": planets['jupiter_barycenter'],
    "Сатурн (Стрибогъ)": planets['saturn_barycenter'],
    "Уран (Варуна)": planets['uranus_barycenter'],
    "Нептун (Ний)": planets['neptune_barycenter'],
    "Плутон (Вий)": planets['pluto_barycenter']
}

EARTH = planets['earth']

def calculate_position(target_date, body_name):
    """Вычисляет эклиптическую долготу и конвертирует в Чертоги (0-15)"""
    t = ts.utc(target_date.year, target_date.month, target_date.day, 
               target_date.hour, target_date.minute)
    
    # Положение относительно Земли
    astrometric = EARTH.at(t).observe(BODIES[body_name])
    
    # Геоцентрическая эклиптическая долгота (в градусах 0..360)
    lat, lon, distance = astrometric.ecliptic_lat_lon()
    deg = lon.degrees % 360
    
    # Перевод в Сварожий Круг (16 Чертогов по 22.5 градусов)
    chertog_num = int(deg // 22.5)
    zal_num = int((deg % 22.5) // 2.5)  # 9 Залов в Чертоге (по 2.5 deg)
    
    return deg, chertog_num, zal_num, distance.au

def update_calc(days_offset=0):
    try:
        if days_offset != 0:
            current_dt = datetime.strptime(date_entry.get(), "%Y-%m-%d %H:%M")
            new_dt = current_dt + timedelta(days=days_offset)
            date_entry.delete(0, tk.END)
            date_entry.insert(0, new_dt.strftime("%Y-%m-%d %H:%M"))
        
        target_dt = datetime.strptime(date_entry.get(), "%Y-%m-%d %H:%M")
        selected_body = body_box.get()
        
        deg, chertog, zal, dist = calculate_position(target_dt, selected_body)
        
        # Вывод результатов
        lbl_deg_val.config(text=f"{deg:.4f}°")
        lbl_chertog_val.config(text=f"Чертог {chertog} — Зал {zal}")
        lbl_dist_val.config(text=f"{dist:.4f} а.е.")
        
    except ValueError:
        messagebox.showerror("Ошибка формата", "Введите дату в формате ГГГГ-ММ-ДД ЧЧ:ММ")

# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Астро-Калькулятор Резонансов и Чертогов")
root.geometry("440 x 380")
root.resizable(False, False)

style = ttk.Style()
style.theme_use('clam')

# Выбор планеты
ttk.Label(root, text="Небесное тело:", font=('Helvetica', 10, 'bold')).pack(anchor="w", padx=20, pady=(15, 2))
body_box = ttk.Combobox(root, values=list(BODIES.keys()), state="readonly", font=('Helvetica', 10))
body_box.current(4) # По умолчанию Марс
body_box.pack(fill="x", padx=20)

# Поле ввода даты
ttk.Label(root, text="Дата и время (UTC):", font=('Helvetica', 10, 'bold')).pack(anchor="w", padx=20, pady=(10, 2))
date_entry = ttk.Entry(root, font=('Helvetica', 10))
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
date_entry.pack(fill="x", padx=20)

# Быстрые кнопки смещения времени
btn_frame = ttk.Frame(root)
btn_frame.pack(fill="x", padx=20, pady=10)

ttk.Button(btn_frame, text="+1 День", command=lambda: update_calc(1)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+1 Месяц (30d)", command=lambda: update_calc(30)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+1 Год (365d)", command=lambda: update_calc(365)).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(btn_frame, text="+16 Лет (Круг)", command=lambda: update_calc(5844)).pack(side="left", expand=True, fill="x", padx=2)

# Главная кнопка Расчета
btn_calc = ttk.Button(root, text="Рассчитать точные координаты", command=lambda: update_calc(0))
btn_calc.pack(fill="x", padx=20, pady=5)

# Блок вывода результатов
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

root.mainloop()