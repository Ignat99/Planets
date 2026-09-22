"""
Файл: analemma_array.py

Глобальные структурированные константы
"""

# Хранилище состояний открытых окон аналемм
analemma_state = {}


# Соответствие русских названий планет и имён в ephem.
# «Земля» показывает аналемму Солнца, видимую с Земли.
PLANET_EPHEM_MAP = {
    "Солнце":   "Sun",
    "Меркурий": "Mercury",
    "Венера":   "Venus",
    "Земля":    "Sun",
    "Луна":     "Moon",
    "Марс":     "Mars",
    "Юпитер":   "Jupiter",
    "Сатурн":   "Saturn",
    "Хирон":    None,   # Требует добавления ephem.Chiron() в BODY_MAP
}


CONTRAST_LEVELS = [0.15, 0.40, 0.90, 0.40, 0.15]
show_five_curves = True   # True — 5 кривых, False — 1 кривая
show_lines = True         # True — линии, False — точки
