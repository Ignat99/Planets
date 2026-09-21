"""
Файл: astronomy.py

Модуль астрометрических расчётов: эфемериды, сферические координаты,
пересчёт в систему «Сварожьего Круга» (чертоги, залы, столы и т.д.).

Содержит данные небесных тел, патчи для SPK-ядер, функции расчёта
положений относительно Земли и Солнца, а также логику пересчёта
координат в условную систему секторов.

Может использоваться как импортируемый модуль (доступны BODIES,
вспомогательные функции и константы) либо как основа для интеграции
в GUI-приложения.
"""
	

import math
import spktype21
from datetime import datetime
from skyfield.api import load, wgs84
import skyfield.data.mpc as mpc
from astropy.time import Time
from skyfield.constants import GM_SUN_DE440_km3_s2 as GM_SUN

# Ссылка на базу данных Centaurs (Кентавров) и ТНО с сайта Minor Planet Center
DISTANT_URL = 'https://minorplanetcenter.net/iau/MPCORB/Distant.txt'

# Загружаем эфемериды NASA и шкалу времени
planets = load('de422.bsp')

# --- Патч для SPKType21: корректная обработка одиночных значений ---
original_daf_init = spktype21.DAF.__init__

def patched_daf_init(self, *args, **kwargs):
    """
    Патч конструктора DAF для корректного возврата скалярного значения
    при запросе одного элемента вместо массива NumPy.
    """
    original_daf_init(self, *args, **kwargs)
    orig_map_array = self.map_array

    def patched_map_array(start, end):
        """
        Обёртка над map_array, возвращающая скаляр при запросе одного элемента.
        """
        res = orig_map_array(start, end)
        if start == end and hasattr(res, 'item'):
            return res.item()
        return res

    self.map_array = patched_map_array

spktype21.DAF.__init__ = patched_daf_init
# --- Конец исправления ---

kernel = spktype21.SPKType21.open('20002060.bsp')
sedna_eph = spktype21.SPKType21.open('20090377.bsp')

jd = Time.now().jd
ts = load.timescale()

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

with load.open(DISTANT_URL) as f:
    mpc_df = mpc.load_mpcorb_dataframe(f)


def get_spherical_coords(kernel, center, target, jd):
    """
    Вычисляет позицию объекта относительно центра и переводит её в сферические координаты.
    Возвращает (lat_deg, lon_deg, distance_km).
    """
    position, _ = kernel.compute_type21(center, target, jd)
    x, y, z = position

    distance = math.sqrt(x**2 + y**2 + z**2)
    if distance == 0:
        return 0.0, 0.0, 0.0

    lon_deg = math.degrees(math.atan2(y, x))
    if lon_deg < 0:
        lon_deg += 360.0

    sin_lat = max(-1.0, min(1.0, z / distance))
    lat_deg = math.degrees(math.asin(sin_lat))

    return lat_deg, lon_deg, distance


def calculate_position_chiron(target_date, body_name):
    """
    Рассчитывает положение астероида Хирон относительно Земли на заданную дату.
    Возвращает (latitude_deg, longitude_deg, distance_au).
    """
    t = ts.utc(
        target_date.year,
        target_date.month,
        target_date.day,
        target_date.hour,
        target_date.minute
    )

    chiron_row = mpc_df[mpc_df.designation.str.contains('Chiron', case=False)].iloc[0]
    chiron = SUN + mpc.mpcorb_orbit(chiron_row, ts, GM_SUN)

    astrometric = EARTH.at(t).observe(chiron)
    subpoint = wgs84.geographic_position_of(astrometric)

    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    distance = astrometric.distance()

    return lat, lon, distance.au


def calculate_position_planets(target_date, body_name):
    """
    Рассчитывает геоцентрическое положение планеты в эклиптических координатах.
    Возвращает (latitude_deg, longitude_deg, distance_au).
    """
    t = ts.utc(
        target_date.year,
        target_date.month,
        target_date.day,
        target_date.hour,
        target_date.minute
    )

    astrometric = EARTH.at(t).observe(BODIES[body_name])
    lat, lon, distance = astrometric.ecliptic_latlon(epoch=t)

    return lat.degrees, lon.degrees, distance.au


def calculate_position_chertog(lat, lon, distance):
    """
    Пересчитывает эклиптическую долготу в систему «Сварожьего Круга».
    Возвращает кортеж: (lon_shifted, chertog_num, zal_num, stol_num, lavka_num, mesto_num, distance).
    """
    deg = (lon - 130.0) % 360

    STEP_CHERTOG = 22.5
    STEP_ZAL = STEP_CHERTOG / 9
    STEP_STOL = STEP_ZAL / 9
    STEP_LAVKA = STEP_STOL / 72
    STEP_MESTO = STEP_LAVKA / 760

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
