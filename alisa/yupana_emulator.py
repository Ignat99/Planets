"""
yupana_emulator.py
Tkinter GUI эмулятор юпаны с полной поддержкой вычислений и умножения.
Версия с действиями 0-16 и отладочными сообщениями для действий 15 и 16.
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
        self.cols = d.get("cols", d.get("cols", self.cols))
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

    elif action_id == 1:
        n = params.get("n", 5)
        for i in range(model_b.rows):
            for j in range(model_b.cols):
                model_b.set_cell(i, j, stirling_second_kind(i + 1, j + 1))
        model_b.metadata = {"action": "Stirling", "n": n}

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


class YupanaEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Юпана — Эмулятор")
        self.root.geometry("1200x850")

        # Размер сетки: 8x8 для действий со Стирлингом, но 4x5 для умножения
        self.model_a = YupanaModel(rows=8, cols=8)
        self.model_b = YupanaModel(rows=8, cols=8)
        self.current_action = tk.IntVar(value=0)

        self.lattice_a = tk.StringVar(value="7")
        self.lattice_b = tk.StringVar(value="41")
        self.sine_steps = tk.StringVar(value="9")
        self.sine_amp = tk.StringVar(value="100000")
        self.sine_shift = tk.StringVar(value="6")

        self.animation_speed = tk.IntVar(value=1500)

        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Действие:").pack(side=tk.LEFT, padx=(0, 5))
        action_combo = ttk.Combobox(top_frame, textvariable=self.current_action, values=list(ACTIONS.keys()), width=5, state="readonly")
        action_combo.pack(side=tk.LEFT, padx=(0, 10))
        action_combo.bind("<<ComboboxSelected>>", self._on_action_change)

        self.action_label = ttk.Label(top_frame, text=ACTIONS[0]["name"])
        self.action_label.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_frame, text="Выполнить", command=self._execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Сброс", command=self._reset).pack(side=tk.LEFT, padx=5)

        ttk.Button(top_frame, text="CSV", command=self._export_csv).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top_frame, text="JSON", command=self._export_json).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top_frame, text="SPICE", command=self._export_spice).pack(side=tk.RIGHT, padx=2)

        self.param_frame = ttk.LabelFrame(self.root, text="Параметры", padding="5")
        self.param_frame.pack(fill=tk.X, padx=10, pady=5)
        self._build_params(0)

        tables_frame = ttk.Frame(self.root, padding="10")
        tables_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(tables_frame, text="Таблица A (вход)", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_cells = self._build_table(left_frame, self.model_a)

        right_frame = ttk.LabelFrame(tables_frame, text="Таблица B (результат)", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_cells = self._build_table(right_frame, self.model_b)

        self.info_text = tk.Text(self.root, height=10, state=tk.DISABLED, font=("Consolas", 10))
        self.info_text.pack(fill=tk.X, padx=10, pady=5)

    def _build_table(self, parent, model):
        cells = []
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        for i in range(model.rows):
            row_cells = []
            for j in range(model.cols):
                cell_frame = tk.Frame(frame, relief=tk.RAISED, borderwidth=2, width=65, height=55, bg="#F0E68C")
                cell_frame.grid(row=i, column=j, padx=1, pady=1)
                cell_frame.pack_propagate(False)

                label = tk.Label(cell_frame, text="0", font=("Arial", 10, "bold"), bg="#F0E68C")
                label.pack(expand=True)
                row_cells.append((cell_frame, label))
            cells.append(row_cells)

        bottom_frame = ttk.Frame(frame)
        bottom_frame.grid(row=model.rows, column=0, columnspan=model.cols, pady=5)
        bottom_cells = []
        for j in range(model.cols):
            blabel = ttk.Label(bottom_frame, text="0", font=("Arial", 10, "bold"), foreground="blue")
            blabel.grid(row=0, column=j, padx=10)
            bottom_cells.append(blabel)
        cells.append(bottom_cells)

        return cells

    def _build_params(self, action_id):
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        if action_id in (8, 10, 11, 12, 13, 14, 15, 16):
            label_text = "Параметр n:" if action_id in (11, 12, 13, 14, 15, 16) else "Число A:"
            ttk.Label(self.param_frame, text=label_text).grid(row=0, column=0, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.lattice_a, width=10).grid(row=0, column=1, padx=5)

            if action_id in (8, 10):
                ttk.Label(self.param_frame, text="Число B:").grid(row=0, column=2, padx=5)
                ttk.Entry(self.param_frame, textvariable=self.lattice_b, width=10).grid(row=0, column=3, padx=5)

            if action_id in (10, 11, 12, 13, 14, 15, 16):
                col_offset = 2 if action_id in (11, 12, 13, 14, 15, 16) else 4
                ttk.Label(self.param_frame, text="Задержка (мс):").grid(row=0, column=col_offset, padx=(20, 5))
                speed_scale = ttk.Scale(self.param_frame, from_=100, to=3000, variable=self.animation_speed, orient=tk.HORIZONTAL, length=150)
                speed_scale.grid(row=0, column=col_offset+1, padx=5)
                speed_label = ttk.Label(self.param_frame, text=f"{self.animation_speed.get()} мс")
                speed_label.grid(row=0, column=col_offset+2, padx=5)
                speed_scale.config(command=lambda val: speed_label.config(text=f"{int(float(val))} мс"))

        elif action_id == 9:
            ttk.Label(self.param_frame, text="Шагов:").grid(row=0, column=0, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.sine_steps, width=5).grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="Амплитуда:").grid(row=0, column=2, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.sine_amp, width=10).grid(row=0, column=3, padx=5)
        else:
            ttk.Label(self.param_frame, text="Дополнительных параметров не требуется").grid(row=0, column=0, padx=5)

    def _on_action_change(self, event=None):
        action_id = self.current_action.get()
        if action_id in ACTIONS:
            self.action_label.config(text=ACTIONS[action_id]["name"])
            self._build_params(action_id)

    def _execute(self):
        action_id = self.current_action.get()
        params = {}
        if action_id in (8, 10, 11, 12, 13, 14, 15, 16):
            try:
                params["a"] = int(self.lattice_a.get())
                if action_id in (8, 10):
                    params["b"] = int(self.lattice_b.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целые числа")
                return

        elif action_id == 9:
            try:
                params["steps"] = int(self.sine_steps.get())
                params["amplitude"] = int(self.sine_amp.get())
                params["shift_bit"] = int(self.sine_shift.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Проверьте параметры генератора синуса")
                return

        print(f"[ОТЛАДКА GUI] Нажата кнопка Выполнить. Действие: {action_id}, параметры: {params}")
        self.model_a, self.model_b = execute_action(action_id, self.model_a, self.model_b, params)

        meta = self.model_b.metadata
        print(f"[ОТЛАДКА GUI] Метаданные после вычислений: {list(meta.keys()) if meta else 'Пусто'}")

        has_history = "steps_history" in meta
        print(f"[ОТЛАДКА GUI] steps_history в метаданных: {has_history}")
        if has_history:
            print(f"[ОТЛАДКА GUI] Количество шагов: {len(meta['steps_history'])}")

        if action_id in (10, 11, 12, 13, 14, 15, 16) and has_history:
            print(f"[ОТЛАДКА GUI] Запуск анимации для действия {action_id}")
            self._run_steps_animation(0)
        else:
            print(f"[ОТЛАДКА GUI] Анимация не запущена. Переходим к стандартному отображению.")
            self._refresh_display()
            self._show_info()

    def _run_steps_animation(self, current_step_idx, history=None):
        if history is None:
            history = list(self.model_b.metadata.get("steps_history", []))

        print(f"[ОТЛАДКА АНИМАЦИИ] Шаг {current_step_idx} из {len(history)}")

        if current_step_idx >= len(history):
            print(f"[ОТЛАДКА АНИМАЦИИ] Достигнут конец истории. Завершение.")
            self.info_text.config(state=tk.NORMAL)
            self.info_text.insert(tk.END, f"\n\n{self.model_b.metadata.get('lattice_viz', '')}")
            self.info_text.config(state=tk.DISABLED)
            return

        step_data = history[current_step_idx]
        action_id = self.current_action.get()

        saved_result = self.model_b.metadata.get("result", 0)
        saved_viz = self.model_b.metadata.get("lattice_viz", "")

        # Для Действия 11 — накопление правой таблицы
        accumulated_right_cells = {}
        if action_id == 11:
            for r in range(self.model_b.rows):
                for j in range(self.model_b.cols):
                    v = self.model_b.get_cell(r, j)
                    if v > 0:
                        accumulated_right_cells[(r, j)] = v

        self.model_a.reset()

        if action_id != 11:
            self.model_b.reset()
        else:
            self.model_b.metadata = {}

        self.model_b.metadata = {
            "action": ACTIONS[action_id]["name"],
            "result": saved_result,
            "lattice_viz": saved_viz,
            "steps_history": history,
            "highlight_cells_current": step_data.get("highlight", [])
        }

        # Заполняем левую таблицу
        left_data = step_data.get("left", {})
        print(f"[ОТЛАДКА АНИМАЦИИ] left_data: {len(left_data)} ячеек -> {dict(list(left_data.items())[:5])}...")

        for (r, c), val in left_data.items():
            self.model_a.set_cell(r, c, val)

        # Заполняем правую таблицу
        if action_id == 11:
            if step_data.get("use_accumulation", True):
                for (r, c), val in accumulated_right_cells.items():
                    self.model_b.set_cell(r, c, val)
                for (r, c), val in step_data.get("temporary_right", {}).items():
                    self.model_b.set_cell(r, c, val)
            else:
                for (r, c), val in accumulated_right_cells.items():
                    self.model_b.set_cell(r, c, val)
                for (r, c), val in step_data.get("temporary_right", {}).items():
                    self.model_b.set_cell(r, c, val)
        elif action_id in (13, 14, 15, 16):
            # Действия 13-16: right = текущее состояние целевой матрицы
            right_data = step_data.get("right", {})
            print(f"[ОТЛАДКА АНИМАЦИИ] right_data: {len(right_data)} ячеек -> {dict(list(right_data.items())[:5])}...")
            for (r, c), val in right_data.items():
                self.model_b.set_cell(r, c, val)
        else:
            # Действие 10 и другие
            right_data = step_data.get("right", {})
            for (r, c), val in right_data.items():
                self.model_b.set_cell(r, c, val)

        if current_step_idx == len(history) - 1:
            self.model_b.set_bottom(0, saved_result)

        self._refresh_display()

        self.info_text.config(state=tk.NORMAL)
        if current_step_idx == 0:
            self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, step_data.get("text", "") + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

        next_idx = current_step_idx + 1
        current_delay = self.animation_speed.get()
        self.root.after(current_delay, lambda idx=next_idx, hist=history: self._run_steps_animation(idx, hist))

    def _reset(self):
        self.model_a.reset()
        self.model_b.reset()
        self._refresh_display()
        self._show_info()

    def _refresh_display(self):
        action_id = self.current_action.get()

        for model, cells in [(self.model_a, self.left_cells), (self.model_b, self.right_cells)]:
            is_right_table = (model == self.model_b)
            is_left_table = (model == self.model_a)

            for i in range(model.rows):
                for j in range(model.cols):
                    if i < len(cells) - 1:
                        cell_frame, label = cells[i][j]

                        val = model.get_cell(i, j)
                        label.config(text=str(val))

                        # Подсветка для действия 10 (умножение инков)
                        if action_id == 10 and is_left_table:
                            if 0 <= i <= 2 and 0 <= j <= 2:
                                if (i, j) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                                    cell_frame.config(bg="#9E9E9E")
                                    fg_color = "#FAFAFA" if j == 0 else "#212121"
                                    label.config(bg="#9E9E9E", foreground=fg_color)
                                elif (i, j) in [(0, 1), (2, 1)]:
                                    cell_frame.config(bg="#FAFAFA")
                                    label.config(bg="#FAFAFA", foreground="black")
                                elif (i, j) in [(1, 0), (1, 2)]:
                                    cell_frame.config(bg="#212121")
                                    label.config(bg="#212121", foreground="white")
                                elif (i, j) == (1, 1):
                                    cell_frame.config(bg="#D4AF37")
                                    label.config(bg="#D4AF37", foreground="#1E88E5")
                                else:
                                    cell_frame.config(bg="#F0E68C")
                                    label.config(bg="#F0E68C", foreground="black")
                            else:
                                cell_frame.config(bg="#F0E68C")
                                label.config(bg="#F0E68C", foreground="black")

                        # Подсветка для действий 11-16 (левая таблица — выделение)
                        elif action_id in (11, 12, 13, 14, 15, 16) and is_left_table:
                            highlight_cells = self.model_b.metadata.get("highlight_cells_current", [])
                            if (i, j) in highlight_cells:
                                cell_frame.config(bg="#8E24AA")
                                label.config(bg="#8E24AA", foreground="white")
                            else:
                                cell_frame.config(bg="#F0E68C")
                                label.config(bg="#F0E68C", foreground="black")

                        # Подсветка для правой таблицы (фазановые цвета)
                        elif is_right_table and 0 < val < len(PHASANT_COLORS):
                            color_name = PHASANT_COLORS[val]
                            hex_color = COLOR_MAP.get(color_name, "#F0E68C")
                            fg_color = "white" if color_name == "чёрный" else "black"
                            cell_frame.config(bg=hex_color)
                            label.config(bg=hex_color, foreground=fg_color)
                        else:
                            cell_frame.config(bg="#F0E68C")
                            label.config(bg="#F0E68C", foreground="black")

            bottom_cells = cells[-1]
            for j in range(model.cols):
                if j < len(bottom_cells):
                    bottom_cells[j].config(text=str(model.get_bottom(j)))

    def _show_info(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        action_id = self.current_action.get()
        info_lines = [f"Действие {action_id}: {ACTIONS[action_id]['desc']}"]

        if self.model_b.metadata:
            meta = self.model_b.metadata
            if "lattice_viz" in meta:
                if "a" in meta and "b" in meta:
                    info_lines.append(f"\nРезультат: {meta['a']} x {meta['b']} = {meta['result']}\n")
                elif "a" in meta:
                    info_lines.append(f"\nРезультат для n={meta['a']}: {meta['result']}\n")
                info_lines.append(meta["lattice_viz"])
            else:
                info_lines.append(f"\nМетаданные:\n{json.dumps(meta, ensure_ascii=False, indent=2)}")

        self.info_text.insert("1.0", "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)

    def _export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if filename:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Table", "Row", "Col", "Value"])
                for i in range(self.model_b.rows):
                    for j in range(self.model_b.cols):
                        writer.writerow(["B", i, j, self.model_b.get_cell(i, j)])
            messagebox.showinfo("Успех", "Данные экспортированы")

    def _export_json(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"table_a": self.model_a.to_dict(), "table_b": self.model_b.to_dict()}, f, indent=2)
            messagebox.showinfo("Успех", "JSON сохранен")

    def _export_spice(self):
        filename = filedialog.asksaveasfilename(defaultextension=".spice", filetypes=[("SPICE", "*.spice")])
        if filename:
            with open(filename, "w") as f:
                f.write("* Yupana Netlist\n.subckt yupana_core\n")
                f.write(".ends\n")
            messagebox.showinfo("Успех", "SPICE файл создан")

if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaEmulatorGUI(root)
    root.mainloop()
