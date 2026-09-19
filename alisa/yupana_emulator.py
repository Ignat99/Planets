"""
yupana_emulator.py
Tkinter GUI эмулятор юпаны с полной поддержкой вычислений и умножения.
Версия с действиями 0-16 и отладочными сообщениями для действий 15 и 16.
Часть 1: модель, действия, вычисления.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import os
import sys

# Гарантируем импорт из текущей папки
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import yupana_emulator_gui as yeg
except Exception as e:
    print(f"[ОТЛАДКА ИМПОРТА] Ошибка импорта yupana_emulator_gui: {e}")




try:
    from yupana_math import (
        stirling_second_kind, format_cell_display, compute_a391838_sequence
    )
except ImportError:
    def compute_a391838_sequence(n): return [1, 6, 40, 336, 3456][:n]
    def stirling_second_kind(n, k): return 1

try:
    from yupana_lattice import (
        emulator_lattice_action, emulator_lattice_action_old,
        emulator_inca_lattice_action, emulator_stirling_diagonal_action,
        emulator_a391838_action, emulator_column_lift_action,
        emulator_column_lower_action
    )
except ImportError as e:
    print(f"[ОТЛАДКА ИМПОРТА] Ошибка импорта yupana_lattice: {e}")
    def emulator_lattice_action(a, b): return {"result": a * b}
    def emulator_lattice_action_old(a, b): return {"result": a * b, "left_yupana": {}, "right_yupana": {}, "lattice_str": ""}
    def emulator_inca_lattice_action(a, b): return {"result": a * b, "steps": [], "lattice_str": ""}
    def emulator_stirling_diagonal_action(n): return {"result": 0, "steps": [], "lattice_str": ""}
    def emulator_a391838_action(n): return {"result": 0, "steps": [], "lattice_str": ""}
    def emulator_column_lift_action(n): return {"result": 0, "steps": [], "lattice_str": ""}
    def emulator_column_lower_action(n): return {"result": 0, "steps": [], "lattice_str": ""}

# Пытаемся импортировать новые функции сдвига строк из yupana_lattice
try:
    from yupana_lattice import (
        emulator_shift_rows_right_action, emulator_shift_rows_left_action
    )
    _HAS_SHIFT_ROW_ACTIONS = True
except ImportError as e:
    print(f"[ОТЛАДКА ИМПОРТА] emulator_shift_rows_right/left_action не найдены: {e}")
    _HAS_SHIFT_ROW_ACTIONS = False
    def emulator_shift_rows_right_action(n): return {"result": 0, "steps": [], "lattice_str": ""}
    def emulator_shift_rows_left_action(n): return {"result": 0, "steps": [], "lattice_str": ""}

try:
    from yupana_oscillator import generate_sine_on_triangular_grid
except ImportError:
    def generate_sine_on_triangular_grid(s, a, sb): return []

# Импорт функции рефакторинга Действия 1 из yupana_core
try:
    from yupana_core import execute_action_refactoring_act1
except ImportError:
    def execute_action_refactoring_act1(action_id, model_a, model_b, params=None):
        pass


PHASANT_COLORS = ["красный", "оранжевый", "жёлтый", "зелёный", "голубой", "синий", "фиолетовый", "белый", "чёрный"]
COLOR_MAP = {
    "красный": "#E53935", "оранжевый": "#FB8C00", "жёлтый": "#FDD835", "зелёный": "#43A047",
    "голубой": "#039BE5", "синий": "#1E88E5", "фиолетовый": "#8E24AA", "белый": "#FAFAFA", "чёрный": "#212121"
}


class YupanaModel:
    def __init__(self, rows=4, cols=5):
        self.rows = rows
        self.cols = cols
        self.cells = [[0 for _ in range(cols)] for _ in range(rows)]
        self.bottom_row = [0] * cols
        self.metadata = {}

    def reset(self):
        self.cells = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.bottom_row = [0] * self.cols
        self.metadata = {}

    def set_cell(self, row, col, value):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.cells[row][col] = value

    def get_cell(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.cells[row][col]
        return 0

    def set_bottom(self, col, value):
        if 0 <= col < self.cols:
            self.bottom_row[col] = value

    def get_bottom(self, col):
        if 0 <= col < self.cols:
            return self.bottom_row[col]
        return 0

    def set_bottom_row(self, values):
        for i, v in enumerate(values):
            if i < self.cols:
                self.bottom_row[i] = v

    def get_bottom_row(self):
        return list(self.bottom_row)

    def to_dict(self):
        return {"rows": self.rows, "cols": self.cols, "cells": self.cells, "bottom_row": self.bottom_row, "metadata": self.metadata}

    def from_dict(self, d):
        self.rows = d.get("rows", self.rows)
        self.cols = d.get("cols", self.cols)
        self.cells = d.get("cells", self.cells)
        self.bottom_row = d.get("bottom_row", self.bottom_row)
        self.metadata = d.get("metadata", {})


ACTIONS = {
    0: {"name": "A391838 (авто)", "desc": "Последовательность A391838 в нижнюю строку"},
    1: {"name": "Stirling S(n,k)", "desc": "Числа Стирлинга 2-го рода"},
    2: {"name": "Сложение", "desc": "Сложение камешков по строкам"},
    3: {"name": "Вычитание", "desc": "Вычитание камешков по строкам"},
    4: {"name": "Сдвиг", "desc": "Сдвиг камешков вправо"},
    5: {"name": "Зеркало", "desc": "Зеркальное отражение матрицы"},
    6: {"name": "Транспонирование", "desc": "Транспонирование матрицы"},
    7: {"name": "Обращение", "desc": "Обращение последовательности"},
    8: {"name": "Умножение (решётка)", "desc": "Умножение методом 4 клеток / 3x3 юпана"},
    9: {"name": "Синус (NCO)", "desc": "Генерация синуса на треугольной сетке"},
    10: {"name": "Умножение инков", "desc": "Поклеточное умножение на 9 клетках (палочки и камешки)"},
    11: {"name": "Диагонали A391838", "desc": "Косые диагонали Стирлинга I рода для формулы OEIS"},
    12: {"name": "A391838 (строка)", "desc": "A391838 через строку Стирлинга: 2^n * (2n+1) * n!"},
    13: {"name": "Поднятие столбцов", "desc": "Сдвиг столбца k вверх на k: косые диагонали -> столбцы"},
    14: {"name": "Опускание столбцов", "desc": "Сдвиг столбца k вниз на k: столбцы -> косые диагонали"},
    15: {"name": "Сдвиг строк вправо", "desc": "Сдвиг строки r вправо на r: верхнетреугольная матрица"},
    16: {"name": "Сдвиг строк влево", "desc": "Обратный сдвиг строк: треугольная -> поднятая"},
}


def execute_action(action_id, model_a, model_b, params=None):
    params = params or {}

    if action_id in (8, 10):
        model_a.reset()
        model_b.reset()
    elif action_id == 11:
        model_a.reset()
    elif action_id in (13, 14, 15, 16):
        model_a.reset()
        model_b.reset()

    if action_id == 0:
        seq = compute_a391838_sequence(model_b.cols)
        model_b.set_bottom_row(seq)
        model_b.metadata = {"action": "A391838", "sequence": seq}

    # Начало блока Действие 1
#    elif action_id == 1:
#        n = params.get("n", 5)
        # Вызов функции из yupana_core
#        execute_action_refactoring_act1(action_id, model_a, model_b, params)
        # Размещение результата в нижней строке Юпаны (последняя строка сетки)
 #       last_row = model_b.rows - 2
 #       for j in range(model_b.cols):
 #           val = stirling_second_kind(last_row + 1, j + 1)
#            model_b.set_cell(last_row, j, val)
        # Остальные строки — нули
#        for i in range(last_row - 2):
#            for j in range(model_b.cols):
#                model_b.set_cell(i, j, 0)
        # Нижняя строка (вне сетки) — нули
#        for j in range(model_b.cols):
#            model_b.set_bottom(j, 0)
#        model_b.metadata = {"action": "Stirling", "n": n}
    # Конец блока Действие 1

    elif action_id == 2:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, j) * 2)
        model_b.metadata = {"action": "add"}

    elif action_id == 3:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "sub"}

    elif action_id == 4:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j > 0:
                    model_b.set_cell(i, j, model_a.get_cell(i, j - 1))
                else:
                    model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "shift"}

    elif action_id == 5:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, model_a.cols - 1 - j))
        model_b.metadata = {"action": "mirror"}

    elif action_id == 6:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j < model_b.rows and i < model_b.cols:
                    model_b.set_cell(j, i, model_a.get_cell(i, j))
        model_b.metadata = {"action": "transpose"}

    elif action_id == 7:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(model_a.rows - 1 - i, model_a.cols - 1 - j, model_a.get_cell(i, j))
        model_b.metadata = {"action": "inverse"}

    elif action_id == 8:
        a = params.get("a", 23)
        b = params.get("b", 41)
        try:
            state = emulator_lattice_action_old(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.set_bottom(0, result)
            model_b.metadata = {
                "action": "lattice_multiply", "a": a, "b": b, "result": result,
                "lattice_viz": state.get("lattice_str", "Сетка решётки построена успешно.")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "lattice_multiply", "a": a, "b": b, "result": result, "error": str(e)}

    elif action_id == 9:
        steps = params.get("steps", 9)
        amplitude = params.get("amplitude", 100000)
        shift_bit = params.get("shift_bit", 6)
        try:
            results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
            sine_values = [r[2] for r in results]
            model_b.set_bottom_row(sine_values[:model_b.cols])
            model_b.metadata = {"action": "sine_nco", "steps": steps, "amplitude": amplitude, "sine_values": sine_values}
        except Exception as e:
            model_b.metadata = {"action": "sine_nco", "error": str(e)}

    elif action_id == 10:
        a = params.get("a", 11)
        b = params.get("b", 22)
        try:
            state = emulator_inca_lattice_action(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.metadata = {
                "action": "inca_multiply",
                "a": a, "b": b,
                "result": state.get("result", a * b),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "inca_multiply", "a": a, "b": b, "result": result, "error": str(e)}

    elif action_id == 11:
        n_val = params.get("a", 3)
        try:
            state = emulator_stirling_diagonal_action(n_val)
            model_b.metadata = {
                "action": "stirling_diagonal",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "stirling_diagonal", "error": str(e)}

    elif action_id == 12:
        n_val = params.get("a", 3)
        try:
            state = emulator_a391838_action(n_val)
            model_b.metadata = {
                "action": "a391838_row",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "a391838_row", "error": str(e)}

    elif action_id == 13:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lift_action(n_val)
            model_b.metadata = {
                "action": "column_lift",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lift", "error": str(e)}

    elif action_id == 14:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lower_action(n_val)
            model_b.metadata = {
                "action": "column_lower",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lower", "error": str(e)}

    elif action_id == 15:
        n_val = params.get("a", 7)
        print(f"[ОТЛАДКА GUI] Действие 15: вызов emulator_shift_rows_right_action(n={n_val})")
        print(f"[ОТЛАДКА GUI] _HAS_SHIFT_ROW_ACTIONS = {_HAS_SHIFT_ROW_ACTIONS}")
        try:
            state = emulator_shift_rows_right_action(n_val)
            print(f"[ОТЛАДКА GUI] Действие 15: state получен, ключи={list(state.keys())}")
            print(f"[ОТЛАДКА GUI] Действие 15: steps_history содержит {len(state.get('steps', []))} шагов")
            model_b.metadata = {
                "action": "shift_rows_right",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
            print(f"[ОТЛАДКА GUI] Действие 15: метаданные записаны, steps_history в метаданных: {'steps_history' in model_b.metadata}")
        except Exception as e:
            print(f"[ОТЛАДКА GUI] Действие 15: ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            model_b.metadata = {"action": "shift_rows_right", "error": str(e)}

    elif action_id == 16:
        n_val = params.get("a", 7)
        print(f"[ОТЛАДКА GUI] Действие 16: вызов emulator_shift_rows_left_action(n={n_val})")
        print(f"[ОТЛАДКА GUI] _HAS_SHIFT_ROW_ACTIONS = {_HAS_SHIFT_ROW_ACTIONS}")
        try:
            state = emulator_shift_rows_left_action(n_val)
            print(f"[ОТЛАДКА GUI] Действие 16: state получен, ключи={list(state.keys())}")
            print(f"[ОТЛАДКА GUI] Действие 16: steps_history содержит {len(state.get('steps', []))} шагов")
            model_b.metadata = {
                "action": "shift_rows_left",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
            print(f"[ОТЛАДКА GUI] Действие 16: метаданные записаны, steps_history в метаданных: {'steps_history' in model_b.metadata}")
        except Exception as e:
            print(f"[ОТЛАДКА GUI] Действие 16: ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            model_b.metadata = {"action": "shift_rows_left", "error": str(e)}

    return model_a, model_b


# Импорт GUI из второго модуля
try:
    from yupana_emulator_gui import YupanaEmulatorGUI
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_emulator_gui: {e}")
    YupanaEmulatorGUI = None


if __name__ == "__main__":
    if YupanaEmulatorGUI is not None:
        root = tk.Tk()
        app = YupanaEmulatorGUI(root)
        root.mainloop()
    else:
        print("Ошибка: GUI модуль недоступен")
