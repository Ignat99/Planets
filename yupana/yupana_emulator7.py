"""
yupana_emulator.py
Tkinter GUI эмулятор юпаны с поддержкой:
- Действия 0-7 (базовые операции)
- Действие 8: Умножение методом решётки (4 клетки / 3x3 юпана)
- Действие 9: Генерация синуса на треугольной сетке
- Экспорт CSV / JSON / SPICE
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import math
import os
import sys

# Добавляем каталог скрипта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from yupana_math import (
        stirling_second_kind, a391838_sequence,
        matrix_to_list, format_cell_display
    )
except ImportError:
    pass

try:
    from yupana_lattice import (
        emulator_lattice_action, visualize_lattice, visualize_yupana3x3
    )
except ImportError:
    pass

try:
    from yupana_oscillator import (
        generate_sine_on_triangular_grid, oscillator_to_yupana_bottom_row
    )
except ImportError:
    pass


# ============================================================
# Исправленные цвета фазана
# ============================================================

PHASANT_COLORS = [
    "красный",    # 0
    "оранжевый",  # 1
    "жёлтый",     # 2
    "зелёный",    # 3
    "голубой",    # 4
    "синий",      # 5
    "фиолетовый", # 6
    "белый",      # 7 — «большой» (крупные белые перья)
    "чёрный",     # 8 — «чубатый» (чёрный хохолок)
]

# Цвета для отображения в Tkinter
COLOR_MAP = {
    "красный": "#E53935",
    "оранжевый": "#FB8C00",
    "жёлтый": "#FDD835",
    "зелёный": "#43A047",
    "голубой": "#039BE5",
    "синий": "#1E88E5",
    "фиолетовый": "#8E24AA",
    "белый": "#FAFAFA",
    "чёрный": "#212121",
}


# ============================================================
# Модель юпаны
# ============================================================

class YupanaModel:
    """Модель данных юпаны 5x4 (5 столбцов, 4 строки)."""
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
        return {
            "rows": self.rows,
            "cols": self.cols,
            "cells": self.cells,
            "bottom_row": self.bottom_row,
            "metadata": self.metadata,
        }

    def from_dict(self, d):
        self.rows = d.get("rows", self.rows)
        self.cols = d.get("cols", self.cols)
        self.cells = d.get("cells", self.cells)
        self.bottom_row = d.get("bottom_row", self.bottom_row)
        self.metadata = d.get("metadata", {})


# ============================================================
# Действия
# ============================================================

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
}


def execute_action(action_id, model_a, model_b, params=None):
    """Выполнить действие и вернуть обновлённые модели."""
    params = params or {}

    if action_id == 0:
        # A391838
        try:
            seq = a391838_sequence(10)
            model_b.set_bottom_row(seq)
            model_b.metadata = {"action": "A391838", "sequence": seq}
        except Exception:
            seq = [1, 6, 40, 336, 3456, 42240, 599040, 9676800, 175472640, 3530096640]
            model_b.set_bottom_row(seq[:model_b.cols])
            model_b.metadata = {"action": "A391838", "sequence": seq}

    elif action_id == 1:
        # Stirling
        n = params.get("n", 5)
        k = params.get("k", 3)
        try:
            val = stirling_second_kind(n, k)
            for i in range(model_b.rows):
                for j in range(model_b.cols):
                    model_b.set_cell(i, j, stirling_second_kind(n, j + 1))
            model_b.metadata = {"action": "Stirling", "n": n, "k": k}
        except Exception:
            pass

    elif action_id == 2:
        # Сложение
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, j) + model_a.get_cell(i, j))
        model_b.metadata = {"action": "add"}

    elif action_id == 3:
        # Вычитание
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, j))
        model_b.metadata = {"action": "sub"}

    elif action_id == 4:
        # Сдвиг вправо
        for i in range(model_a.rows):
            row = model_a.cells[i]
            shifted = [0] + row[:-1]
            for j in range(model_b.cols):
                model_b.set_cell(i, j, shifted[j])
        model_b.metadata = {"action": "shift"}

    elif action_id == 5:
        # Зеркало
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, model_a.cols - 1 - j))
        model_b.metadata = {"action": "mirror"}

    elif action_id == 6:
        # Транспонирование (только для квадратных)
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j < model_b.rows and i < model_b.cols:
                    model_b.set_cell(j % model_b.rows, i % model_b.cols, model_a.get_cell(i, j))
        model_b.metadata = {"action": "transpose"}

    elif action_id == 7:
        # Обращение
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(model_a.rows - 1 - i, model_a.cols - 1 - j, model_a.get_cell(i, j))
        model_b.metadata = {"action": "inverse"}

    elif action_id == 8:
        # Умножение методом решётки
        a = params.get("a", 23)
        b = params.get("b", 41)
        try:
            state = emulator_lattice_action(a, b)
            left = state.get("left_yupana")
            right = state.get("right_yupana")
            result = state.get("result", 0)

            # Заполняем левую таблицу — раскладка решётки
            if left:
                for i in range(min(3, model_a.rows)):
                    for j in range(min(3, model_a.cols)):
                        cell = left.cells.get((i + 1, j + 1))
                        if cell:
                            # upper = десятки (белые), lower = единицы (чёрные)
                            # Суммируем в одно число: white*10 + black
                            val = cell.white * 10 + cell.black
                            model_a.set_cell(i, j, val)

            # Заполняем правую таблицу — результат
            if right:
                for i in range(min(3, model_b.rows)):
                    for j in range(min(3, model_b.cols)):
                        cell = right.cells.get((i + 1, j + 1))
                        if cell:
                            model_b.set_cell(i, j, cell.white + cell.black)

            model_b.metadata = {
                "action": "lattice_multiply",
                "a": a, "b": b, "result": result,
                "lattice_viz": state.get("lattice_str", ""),
            }
        except Exception as e:
            # Fallback: простое умножение
            result = a * b
            model_b.set_bottom_row([result])
            model_b.metadata = {"action": "lattice_multiply", "a": a, "b": b, "result": result, "error": str(e)}

    elif action_id == 9:
        # Генерация синуса на треугольной сетке
        steps = params.get("steps", 9)
        amplitude = params.get("amplitude", 100000)
        shift_bit = params.get("shift_bit", 6)
        try:
            results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
            sine_values = [r[2] for r in results]
            tri_values = [r[1] for r in results]
            model_b.set_bottom_row(sine_values[:model_b.cols])
            model_b.metadata = {
                "action": "sine_nco",
                "steps": steps,
                "amplitude": amplitude,
                "shift_bit": shift_bit,
                "sine_values": sine_values,
                "triangular_values": tri_values,
            }
        except Exception as e:
            model_b.metadata = {"action": "sine_nco", "error": str(e)}

    return model_a, model_b


# ============================================================
# GUI
# ============================================================

class YupanaEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Юпана — Эмулятор")
        self.root.geometry("900x700")

        self.model_a = YupanaModel()
        self.model_b = YupanaModel()

        self.current_action = tk.IntVar(value=0)

        # Параметры для действия 8 (решётка)
        self.lattice_a = tk.StringVar(value="23")
        self.lattice_b = tk.StringVar(value="41")

        # Параметры для действия 9 (синус)
        self.sine_steps = tk.StringVar(value="9")
        self.sine_amp = tk.StringVar(value="100000")
        self.sine_shift = tk.StringVar(value="6")

        self._build_ui()

    def _build_ui(self):
        # --- Верхняя панель ---
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Действие:").pack(side=tk.LEFT, padx=(0, 5))
        action_combo = ttk.Combobox(
            top_frame,
            textvariable=self.current_action,
            values=list(ACTIONS.keys()),
            width=5,
            state="readonly",
        )
        action_combo.pack(side=tk.LEFT, padx=(0, 10))
        action_combo.bind("<<ComboboxSelected>>", self._on_action_change)

        self.action_label = ttk.Label(top_frame, text=ACTIONS[0]["name"])
        self.action_label.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_frame, text="Выполнить", command=self._execute).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Сброс", command=self._reset).pack(side=tk.LEFT, padx=5)

        # Кнопки экспорта
        ttk.Button(top_frame, text="CSV", command=self._export_csv).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top_frame, text="JSON", command=self._export_json).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top_frame, text="SPICE", command=self._export_spice).pack(side=tk.RIGHT, padx=2)

        # --- Панель параметров ---
        self.param_frame = ttk.LabelFrame(self.root, text="Параметры", padding="5")
        self.param_frame.pack(fill=tk.X, padx=10, pady=5)
        self._build_params(0)

        # --- Таблицы ---
        tables_frame = ttk.Frame(self.root, padding="10")
        tables_frame.pack(fill=tk.BOTH, expand=True)

        # Левая таблица (A)
        left_frame = ttk.LabelFrame(tables_frame, text="Таблица A (вход)", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_cells = self._build_table(left_frame, self.model_a)

        # Правая таблица (B)
        right_frame = ttk.LabelFrame(tables_frame, text="Таблица B (результат)", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_cells = self._build_table(right_frame, self.model_b)

        # --- Информационная панель ---
        self.info_text = tk.Text(self.root, height=8, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X, padx=10, pady=5)

    def _build_table(self, parent, model):
        """Построить визуальную таблицу юпаны."""
        cells = []
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        for i in range(model.rows):
            row_cells = []
            for j in range(model.cols):
                cell_frame = tk.Frame(
                    frame,
                    relief=tk.RAISED,
                    borderwidth=2,
                    width=80,
                    height=60,
                    bg="#F0E68C",
                )
                cell_frame.grid(row=i, column=j, padx=2, pady=2)
                cell_frame.pack_propagate(False)

                label = tk.Label(
                    cell_frame,
                    text="0",
                    font=("Arial", 14),
                    bg="#F0E68C",
                )
                label.pack(expand=True)

                row_cells.append((cell_frame, label))
            cells.append(row_cells)

        # Нижняя строка
        bottom_frame = ttk.Frame(frame)
        bottom_frame.grid(row=model.rows, column=0, columnspan=model.cols, pady=5)
        bottom_cells = []
        for j in range(model.cols):
            blabel = ttk.Label(bottom_frame, text="0", font=("Arial", 12), foreground="blue")
            blabel.grid(row=0, column=j, padx=5)
            bottom_cells.append(blabel)
        cells.append(bottom_cells)

        return cells

    def _build_params(self, action_id):
        """Построить панель параметров для выбранного действия."""
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        if action_id == 8:
            ttk.Label(self.param_frame, text="Число A:").grid(row=0, column=0, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.lattice_a, width=10).grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="Число B:").grid(row=0, column=2, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.lattice_b, width=10).grid(row=0, column=3, padx=5)
            ttk.Label(self.param_frame, text="(Левая таблица = раскладка, правая = результат)").grid(
                row=0, column=4, padx=10)

        elif action_id == 9:
            ttk.Label(self.param_frame, text="Шагов:").grid(row=0, column=0, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.sine_steps, width=5).grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="Амплитуда:").grid(row=0, column=2, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.sine_amp, width=10).grid(row=0, column=3, padx=5)
            ttk.Label(self.param_frame, text="Сдвиг:").grid(row=0, column=4, padx=5)
            ttk.Entry(self.param_frame, textvariable=self.sine_shift, width=5).grid(row=0, column=5, padx=5)

        elif action_id == 1:
            ttk.Label(self.param_frame, text="Stirling: n=5, k=3 (по умолчанию)").grid(row=0, column=0, padx=5)

        else:
            ttk.Label(self.param_frame, text="Дополнительных параметров нет").grid(row=0, column=0, padx=5)

    def _on_action_change(self, event=None):
        action_id = self.current_action.get()
        if action_id in ACTIONS:
            self.action_label.config(text=ACTIONS[action_id]["name"])
        self._build_params(action_id)

    def _execute(self):
        action_id = self.current_action.get()
        params = {}

        if action_id == 8:
            try:
                params["a"] = int(self.lattice_a.get())
                params["b"] = int(self.lattice_b.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целые числа для A и B")
                return
        elif action_id == 9:
            try:
                params["steps"] = int(self.sine_steps.get())
                params["amplitude"] = int(self.sine_amp.get())
                params["shift_bit"] = int(self.sine_shift.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целые числа")
                return

        self.model_a, self.model_b = execute_action(action_id, self.model_a, self.model_b, params)
        self._refresh_display()
        self._show_info()

    def _reset(self):
        self.model_a.reset()
        self.model_b.reset()
        self._refresh_display()
        self._show_info()

    def _refresh_display(self):
        """Обновить визуальное отображение таблиц."""
        for model, cells in [(self.model_a, self.left_cells), (self.model_b, self.right_cells)]:
            for i in range(model.rows):
                for j in range(model.cols):
                    if i < len(cells) - 1 and j < len(cells[i]):
                        _, label = cells[i][j]
                        val = model.get_cell(i, j)
                        label.config(text=str(val))
            # Нижняя строка
            if len(cells) > model.rows:
                bottom_cells = cells[model.rows]
                for j in range(min(len(bottom_cells), model.cols)):
                    bottom_cells[j].config(text=str(model.get_bottom(j)))

    def _show_info(self):
        """Показать метаданные и информацию о действии."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)

        action_id = self.current_action.get()
        info_lines = [f"Действие: {ACTIONS.get(action_id, {}).get('name', '?')}"]

        if self.model_b.metadata:
            meta = self.model_b.metadata
            info_lines.append(f"Метаданные: {json.dumps(meta, indent=2, ensure_ascii=False, default=str)}")

            if meta.get("action") == "lattice_multiply":
                info_lines.append(f"\nУмножение: {meta.get('a')} × {meta.get('b')} = {meta.get('result')}")
                if meta.get("lattice_viz"):
                    info_lines.append(f"\nРешётка:\n{meta['lattice_viz']}")

            elif meta.get("action") == "sine_nco":
                if meta.get("sine_values"):
                    vals = meta["sine_values"]
                    info_lines.append(f"\nСинус (первые {len(vals)} шагов): {vals}")

        self.info_text.insert("1.0", "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)

    def _export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="yupana_export.csv",
        )
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Table", "Row", "Col", "Value"])
            for i in range(self.model_b.rows):
                for j in range(self.model_b.cols):
                    writer.writerow(["B", i, j, self.model_b.get_cell(i, j)])
            for j in range(self.model_b.cols):
                writer.writerow(["B_bottom", 0, j, self.model_b.get_bottom(j)])
        messagebox.showinfo("Экспорт", f"CSV сохранён: {filename}")

    def _export_json(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="yupana_export.json",
        )
        if not filename:
            return
        data = {
            "table_a": self.model_a.to_dict(),
            "table_b": self.model_b.to_dict(),
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        messagebox.showinfo("Экспорт", f"JSON сохранён: {filename}")

    def _export_spice(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".spice",
            filetypes=[("SPICE files", "*.spice")],
            initialfile="yupana_export.spice",
        )
        if not filename:
            return
        with open(filename, "w", encoding="utf-8") as f:
            f.write("* Yupana SPICE export\n")
            f.write(f"* Action: {ACTIONS.get(self.current_action.get(), {}).get('name', '?')}\n\n")
            f.write(".subckt yupana ")
            for j in range(self.model_b.cols):
                f.write(f"n{j} ")
            f.write("n_out\n")
            for i in range(self.model_b.rows):
                for j in range(self.model_b.cols):
                    val = self.model_b.get_cell(i, j)
                    if val != 0:
                        f.write(f"B{i}_{j} n{j} 0 V={val}\n")
            for j in range(self.model_b.cols):
                val = self.model_b.get_bottom(j)
                if val != 0:
                    f.write(f"Bb{j} n{j} 0 V={val}\n")
            f.write(".ends\n")
        messagebox.showinfo("Экспорт", f"SPICE сохранён: {filename}")


# ============================================================
# Запуск
# ============================================================

def main():
    root = tk.Tk()
    app = YupanaEmulatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
