import spiceypy as spice

# Загружаем ваш SPK файл в пул SPICE
spice.furnsh('20002060.bsp')

# Пример получения координат (X, Y, Z, Vx, Vy, Vz)
# Замените target_id и observer_id на нужные ID из вашего файла (например, код астероида и 399 для Земли)
target_id = '20002060' 
observer_id = '399'     # 399 = Земля
frame = 'J2000'         # Система координат
aberration = 'NONE'     # Поправка на аберрацию

# Эпоха в формате ET (Ephemeris Time), например, на текущий момент
et = spice.str2et('2026-09-04 00:00:00 UTC')

# Получаем состояние (координаты и скорости)
state, light_time = spice.spkezr(target_id, et, frame, aberration, observer_id)

print("Позиция (км):", state[:3])
print("Скорость (км/с):", state[3:])

# Всегда выгружайте ядра по окончании работы
spice.unload('20002060.bsp')


import spiceypy as spice
et = spice.str2et('now') # или через ISO строку: spice.str2et('2026-09-04T01:24:00')

import spiceypy as spice

spice.furnsh('20002060.bsp')
# 2461287.482084482 - это JD. Переводим её в секунды ET для SPICE:
et = (jd - 2451545.0) * 86400.0 

# Получаем позицию и скорость (замените '20002060' и '399' на ваши target/center ID)
state, lt = spice.spkezr('20002060', et, 'J2000', 'NONE', '399')
position, velocity = state[:3], state[3:]



from skyfield.data import mpc
from skyfield.api import load

# Загружаем стандартное ядро для Земли и Солнца
eph = load('de421.bsp')
EARTH = eph['earth']

# Загружаем Седну (идентификатор MPC для Седны — 90377)
from skyfield.jpllib import MinorPlanet
# Подгружаем эфемериды малых тел
BODIES = {
    'Седна': eph['sun'].minor_planet(90377) # Считает позицию Седны относительно Солнца
}


# t — это объект времени Skyfield (t = ts.from_datetime(target_dt))
astrometric = EARTH.at(t).observe(BODIES[body_name])
apparent = astrometric.apparent()

# Получаем lat (dec), lon (ra) и distance
ra, dec, distance = apparent.radec()

lat = dec.degrees
lon = ra.hours * 15.0  # Переводим часы в градусы (1 час = 15 градусов)
dist_km = distance.km



position, velocity = sedna_eph.compute_type21(10, 20090377, jd)
print(sedna_eph)    # this line prints information of all segments
print(position)
print(velocity)

for segment in sedna_eph.segments:
    print(f"Target ID (Объект): {segment.target}")
    print(f"Center ID (Центр): {segment.center}")
    print(f"Начало (JD): {segment.start_jd}")
    print(f"Конец (JD): {segment.end_jd}")
