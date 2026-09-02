import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from astropy.coordinates import get_body
import astropy.units as u

# Противостояние 2016 года (Марс проходит вблизи восходящего узла)
# В этот период ретроградная петля вырождается в S-образный зигзаг
t_start = Time("2016-02-01")
t_end = Time("2016-09-15")

times = []
curr = t_start
while curr < t_end:
    times.append(curr)
    # Динамический шаг: во время стояний и ретрограда (апрель - июнь 2016)
    # делаем плотную дискретизацию в 1.5 дня, в остальное время — 6 дней
    if Time("2016-04-01") < curr < Time("2016-07-01"):
        curr += 1.5 * u.day
    else:
        curr += 6.0 * u.day

ra_list, dec_list = [], []

for t in times:
    mars = get_body('mars', t)
    # Используем wrap_at для корректной непрерывной проекции
    ra_list.append(mars.ra.wrap_at(360*u.deg).deg)
    dec_list.append(mars.dec.deg)

plt.figure(figsize=(10, 5))

# Отрисовка непрерывной траектории
plt.plot(ra_list, dec_list, color='gray', linestyle='--', alpha=0.6, label='Сплайн траектории')

# Отрисовка расчетных точек
plt.scatter(ra_list, dec_list, color='crimson', s=22, zorder=3, label='Динамическая дискретизация')

# Разворачиваем ось RA (астрономический вид: восток слева)
plt.gca().invert_xaxis()

plt.xlabel('Прямое восхождение $\\alpha$ (градусы)')
plt.ylabel('Склонение $\\delta$ (градусы)')
plt.title('S-образная (зигзагообразная) траектория Марса вблизи драконова узла (2016 год)')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='upper right')

plt.tight_layout()
plt.show()