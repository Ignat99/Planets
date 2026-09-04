from skyfield.api import load, Star
from skyfield.data import constellations


# Самый популярный и чистый источник таких баз — репозиторий (D3 Celestial)[https://github.com/ofrohn/d3-celestial] (проект интерактивных карт звездного неба). Оттуда можно забрать два файла:constellations.bounds.json — координаты всех вершин официальных многоугольников-границ.constellations.lines.json — пары координат звезд (каталог Иппарха/Bright Star), между которыми нужно провести линии, чтобы получился рисунок созвездия (например, ковш Большой Медведицы).Координаты звезд-вершин из этих JSON-файлов переводятся в Skyfield через класс Star(ra_hours=..., dec_degrees=...), после чего для них можно рассчитывать локальный азимут и склонение на любую секунду времени так же, как вы делаете это для планет.


ts = load.timescale()
t = ts.now()

# Берем для примера Полярную звезду
polar_star = Star(ra_hours=(2, 31, 49.09), dec_degrees=(89, 15, 50.8))

# Считаем ее положение с Земли
eph = load('de440s.bsp')
earth = eph['earth']
astrometric = earth.at(t).observe(polar_star)

# ИСПОЛЬЗУЕМ БАЗУ СОЗВЕЗДИЙ: функция определяет созвездие по координатам
# Она возвращает сокращенное (UMi) и полное латинское название (Ursa Minor)
constellation_function = constellations.load_constellation_map()
abbreviation, name = constellation_function(astrometric)

print(f"Объект находится в созвездии: {name} ({abbreviation})")
# Выведет: Ursa Minor (UMi) - Малая Медведица
