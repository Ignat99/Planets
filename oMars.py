import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from astropy.coordinates import get_body, SkyCoord
import astropy.units as u

# Временной интервал противостояния 2018 года (как на втором фото)
# Прямой ход берем редким шагом (5 дней), а ретроград — частым (1 день)
t_start = Time("2018-04-01")
t_end = Time("2018-11-01")

times = []
curr = t_start
while curr < t_end:
    times.append(curr)
    # Динамический шаг: во время стояний и ретрограда (май-август) учащаем точки
    if Time("2018-06-01") < curr < Time("2018-09-01"):
        curr += 1.5 * u.day  # Плотная дискретизация петли
    else:
        curr += 6.0 * u.day  # Редкие интервалы между сезонами

# Расчет геоцентрических координат Марса
ra_list, dec_list = [], []
for t in times:
    mars = get_body('mars', t)
    # Перевод в относительный сдвиг от центра петли
    ra_list.append(mars.ra.wrap_at(180*u.deg).deg)
    dec_list.append(mars.dec.deg)

# Отрисовка с непрерывной линией и точками дискретизации
plt.figure(figsize=(10, 5))
plt.plot(ra_list, dec_list, color='gray', linestyle='--', alpha=0.5, label='Траектория')
plt.scatter(ra_list, dec_list, color='red', s=20, label='Положения (с динамическим шагом)')

plt.gca().invert_xaxis() # Восток слева
plt.xlabel('Прямое восхождение (градусы)')
plt.ylabel('Склонение (градусы)')
plt.title('Точная проекция ретроградной петли Марса 2018 года')
plt.grid(True, linestyle=':')
plt.show()
