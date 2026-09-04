import math
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from skyfield.api import load, wgs84
import skyfield.data.mpc as mpc
# Импортируем стандартное значение гравитационного параметра Солнца
from skyfield.constants import GM_SUN_DE440_km3_s2 as GM_SUN
#from spktype21 import SPKType21
import spktype21
from astropy.time import Time

# 1. Ссылка на базу данных Centaurs (Кентавров) и ТНО с сайта Minor Planet Center
DISTANT_URL = 'https://minorplanetcenter.net/iau/MPCORB/Distant.txt'


# Загружаем эфемериды NASA и шкалу времени
# https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/
# https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp
# https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de442.bsp
# https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de442t.bsp

# Загружаем эфемериды NASA и шкалу времени
planets = load('de422.bsp')

# Корректное исправление map_array: возвращаем скаляр только при запросе 1 элемента
original_daf_init = spktype21.DAF.__init__
def patched_daf_init(self, *args, **kwargs):
    original_daf_init(self, *args, **kwargs)
    orig_map_array = self.map_array
    
    def patched_map_array(start, end):
        res = orig_map_array(start, end)
        # Если запрашивали ровно один элемент (start == end) и вернулся массив NumPy
        if start == end and hasattr(res, 'item'):
            return res.item()  # Превращаем строго в одиночное число Python
        return res  # В остальных случаях возвращаем массив как есть
        
    self.map_array = patched_map_array

spktype21.DAF.__init__ = patched_daf_init
# --- Конец исправления ---


kernel = spktype21.SPKType21.open('20002060.bsp')
sedna_eph = spktype21.SPKType21.open('20090377.bsp')

# Получаем текущее время в UTC и переводим в Julian Date
jd = Time.now().jd

ts = load.timescale()
# t = ts.now()




# Словарь небесных тел (NASA ID / Имена)
BODIES = {
    "Солнце": planets[10],
    "Луна (Месяцъ)": planets[301],
    "Меркурий (Хорсъ)": planets[1],
    "Венера (Заря-Мерцана)": planets[2],
    "Земля (Мидгардъ)": planets[3],
    "Марс (Орей)": planets[4],
    "Юпитер (Перун)": planets[5],
    "Сатурн (Стрибогъ)": planets[6],
    "Индра (Хирон(астероид))": 20002060,
    "Уран (Варуна)": planets[7],
    "Нептун (Ний)": planets[8],
    "Плутон (Вий)": planets[9],
    "Седна (Земля Догоды)": 20090377
}


SUN = planets[10]
EARTH = planets[399]

# 3. Загружаем базу данных малых тел и ищем Хирон по названию
with load.open(DISTANT_URL) as f:
    mpc_df = mpc.load_mpcorb_dataframe(f)

def get_spherical_coords(kernel, center, target, jd):
    """
    Вычисляет позицию объекта и переводит её в сферические координаты.
    
    Возвращает:
        lat (float): Широта (склонение) в градусах от -90 до 90
        lon (float): Долгота (прямое восхождение) в градусах от 0 до 360
        distance (float): Расстояние в километрах
    """
    # 1. Получаем прямоугольные декартовы координаты (X, Y, Z в км)
    position, _ = kernel.compute_type21(center, target, jd)
    x, y, z = position
    
    # 2. Вычисляем расстояние (Distance)
    distance = math.sqrt(x**2 + y**2 + z**2)
    
    # Защита от деления на ноль, если координаты объекта совпали с центром
    if distance == 0:
        return 0.0, 0.0, 0.0
        
    # 3. Вычисляем долготу (Lon) в градусах от 0° до 360°
    lon_deg = math.degrees(math.atan2(y, x))
    if lon_deg < 0:
        lon_deg += 360.0
        
    # 4. Вычисляем широту (Lat) в градусах от -90° до +90°
    # Ограничиваем значение для функции asin в пределах [-1.0, 1.0]
    sin_lat = max(-1.0, min(1.0, z / distance))
    lat_deg = math.degrees(math.asin(sin_lat))
    
    return lat_deg, lon_deg, distance

def calculate_position_chiron(target_date, body_name):
    # 1. Используем точное динамическое время (TT) вместо гражданского UTC для эфемерид
    t = ts.utc(target_date.year, target_date.month, target_date.day, target_date.hour, target_date.minute)

    # Хирон ищется по имени в колонке designation
    chiron_row = mpc_df[mpc_df.designation.str.contains('Chiron', case=False)].iloc[0]

    # 1. Создаем орбиту Хирона относительно Солнца
    chiron = SUN + mpc.mpcorb_orbit(chiron_row, ts, GM_SUN)


    # 5. Вычисляем положение Хирона относительно Земли
    astrometric = EARTH.at(t).observe(chiron)

    # 1. Задаем ВАШИ координаты на Земле (например, Москва: 55.75, 37.61)
    # your_location = EARTH + wgs84.latlon(55.7558, 37.6173)
    subpoint = wgs84.geographic_position_of(astrometric)

    # 2. Смотрим на объект с этой точки
    # apparent = your_location.at(t).observe(chiron).apparent()

    # 3. Получаем горизонтальные координаты!
    # alt, az, distance = apparent.altaz()

    # Вытаскиваем чистые градусы широты и долготы
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    
    # Расстояние можно вытащить в Астрономических единицах (.au) или километрах (.km)
    distance = astrometric.distance() 


    # sreturn alt.degrees, az.degrees, distance
    return lat, lon, distance.au

def calculate_position_planets(target_date, body_name):
    # 1. Используем точное динамическое время (TT) вместо гражданского UTC для эфемерид
    t = ts.utc(target_date.year, target_date.month, target_date.day, target_date.hour, target_date.minute)
    
    # 2. Вычисляем положение планеты из центра Земли (геоцентрически)
    astrometric = EARTH.at(t).observe(BODIES[body_name])
    
    # 3. Получаем чистую эклиптическую долготу J2000
    lat, lon, distance = astrometric.ecliptic_latlon(epoch=t)
    # lat, lon, distance = astrometric.ecliptic_latlon()
    raw_deg = lon.degrees

    return lat, raw_deg, distance.au
    
def calculate_position_chertog(lat, lon, distance):    
    # 4. Применяем базовый сдвиг системы (130 градусов)
    # Используем % 360 ПОСЛЕ вычитания, чтобы избежать отрицательных углов
    deg = (lon - 130.0) % 360
    
    # 5. Константы шагов для каждого уровня деления
    STEP_CHERTOG = 22.5                 # 360 / 16
    STEP_ZAL = STEP_CHERTOG / 9         # 2.5 градуса
    STEP_STOL = STEP_ZAL / 9            # ~0.2777... градуса
    STEP_LAVKA = STEP_STOL / 72         # ~0.003858... градуса
    STEP_MESTO = STEP_LAVKA / 760       # ~0.00000507... градуса

    # 6. Расчет номеров (индексы начинаются с 1 для соответствия традиции)
    chertog_num = int(deg // STEP_CHERTOG)
    rem_chertog = deg % STEP_CHERTOG
    
    zal_num = int(rem_chertog // STEP_ZAL)
    rem_zals = rem_chertog % STEP_ZAL
    
    stol_num = int(rem_zals // STEP_STOL)
    rem_stol = rem_zals % STEP_STOL
    
    lavka_num = int(rem_stol // STEP_LAVKA)
    rem_lavka = rem_stol % STEP_LAVKA
    
    mesto_num = int(rem_lavka // STEP_MESTO)

    return lon, chertog_num, zal_num, stol_num, lavka_num, mesto_num, distance



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
            lat, lon, distance = calculate_position_planets(target_dt, selected_body)
        elif selected_body == "Седна (Земля Догоды)":       
            center = 10
            target = 20090377
            lat, lon, distance = get_spherical_coords(sedna_eph, center, target, jd)
            sedna_eph.close()
        else:
            # lat, lon, distance = calculate_position_chiron(target_dt, selected_body)
            center = 10
            target = 20002060
            lat, lon, distance = get_spherical_coords(kernel, center, target, jd)
            kernel.close()

        deg, chertog, zal, stol, lavka, mesto, dist = calculate_position_chertog(lat, lon, distance)

        
        # Вывод результатов
        lbl_deg_val.config(text=f"{deg:.4f}°")
        lbl_chertog_val.config(text=f"Чертог {chertog} — Зал {zal} — Стол {stol} — Лавка {lavka} — Место {mesto}")
        lbl_dist_val.config(text=f"{dist:.4f} а.е.")
        
    except ValueError:
        messagebox.showerror("Ошибка формата", "Введите дату в формате ГГГГ-ММ-ДД ЧЧ:ММ")

# --- Создание графического интерфейса ---
root = tk.Tk()
root.title("Астро-Калькулятор Резонансов и Чертогов")
root.geometry("640x380")
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
