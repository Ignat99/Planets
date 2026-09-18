"""
yupana_emulator.py - GUI эмулятора Юпаны.

Импортирует математику из yupana_math (чистый модуль, без GUI).
Макросы yupanki сохраняются/загружаются из каталога yupanki/.
yupanki0.json - встроенные действия, грузится при старте.

Архитектура:
  yupana_math.py  - чистая математика (Stirling, A391838, обращение ряда, экспорт)
  yupana_emulator.py - Tkinter GUI (этот файл)
  test_yupana_math.py - unit-тесты

Запуск: python yupana_emulator.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import json
import os
import re
import io
import contextlib
import sys

# Добавляем каталог, где лежит yupana_emulator6.py, в путь поиска
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Для осциллятора:
from yupana_oscillator import oscillator_to_yupana_bottom_row
bottom_row = oscillator_to_yupana_bottom_row(steps=9, amplitude=100000, shift_bit=6)

# Для решётки:
from yupana_lattice_hook import lattice_to_yupana, lattice_to_bottom_row
left_row, right_row, result, info = lattice_to_yupana(23, 41)
bottom = lattice_to_bottom_row(23, 41)

from yupana_involute import involute_to_yupana_bottom_row, involute_to_yupana_full

# Упрощённый — результат в нижнюю строку:
bottom = involute_to_yupana_bottom_row(x_val=1, n_terms=5, scale=100000)

# Полный — раскладка по столбцам + результат:
columns, sin_result, cos_result, info = involute_to_yupana_full(
    x_val=math.pi/6, n_terms=5, scale=100000
)


from yupana_math import (
    S_MAX, stirling_first_kind,
    rassnos_matrix, stirling_matrix, diff_matrix, normalized_matrix,
    fibonacci_diagonal, a391838_diagonal,
    compute_a391838, a391838_to_float, a391838_polynomial,
    multiplicative_inverse, compositional_inverse,
    difference_triangle,
    plotnikov_9cell, plotnikov_maxwell_6cell,
    export_matrix_csv, export_sequence_json, export_spice_subcircuit,
    verify_a391838,
)
from fractions import Fraction

GLYPHS = [
    "\u25CF", "\u25C6", "\u25B2", "\u25A0", "\u2605",
    "\u2724", "\u2725", "\u2726", "\u2727", "\u2728",
    "\u2729", "\u272A", "\u272B", "\u272C", "\u272D",
    "\u272E", "\u272F", "\u2730", "\u2731", "\u2732",
    "\u2733", "\u2734", "\u2735", "\u2736", "\u2737",
    "\u2738", "\u2739", "\u273A", "\u273B", "\u273C",
    "\u273D", "\u273E", "\u273F", "\u2740", "\u2741",
    "\u2742", "\u2743", "\u2744", "\u2745", "\u2746",
]

YUPANKI_DIR = "yupanki"

# yupanki0.json - встроенные действия
YUPANKI0_DATA = {
    "name": "yupanki0",
    "action_desc": "Встроенные действия эмулятора Юпаны",
    "actions": [
        {
            "name": "Действие 0: Инициализация",
            "action_desc": "1, 3, 10, 42, 216, 1320, 9360, 75600, 685440, 6894720",
            "action": (
                "seq = [1, 3, 10, 42, 216, 1320, 9360, 75600, 685440, 6894720]\n"
                "ctx.seq = seq\n"
                "ctx.bottom_row = seq[:ctx.ncols]"
            )
        },
        {
            "name": "Действие 1: Разносная схема",
            "action_desc": "Разностная схема",
            "action": "ctx.mode = 'rassnos'"
        },
        {
            "name": "Действие 2: Переход к Стирлингу",
            "action_desc": "Умножение верхнего элемента на номер строки",
            "action": "ctx.mode = 'stirling'"
        },
        {
            "name": "Действие 3: Дифференцирование",
            "action_desc": "Деление на номер строки, переход вверх",
            "action": "ctx.mode = 'diff'"
        },
        {
            "name": "Действие 4: Диагональ n-k, n-2k (A391838)",
            "action_desc": "Косые диагонали s(n-k, n-2k)",
            "action": "ctx.mode = 'diagonal'"
        },
        {
            "name": "Действие 5: Прямая диагональ n, n-k (Фибоначчи)",
            "action_desc": "Прямые диагонали s(n, n-k)",
            "action": "ctx.mode = 'fibonacci'"
        },
        {
            "name": "Действие 6: Нормировка a_n/n!",
            "action_desc": "Деление на факториал номера строки",
            "action": "ctx.mode = 'normalized'"
        },
        {
            "name": "Действие 7: Обращение ряда",
            "action_desc": "Композиционное обращение степенного ряда",
            "action": (
                "# Вычисляем A391838 и обращаем ряд\n"
                "from yupana_math import compute_a391838, compositional_inverse\n"
                "a_seq = compute_a391838(ctx.ncols - 1)\n"
                "# A391838 как ряд: a_0 + a_1*x + ... - нужен сдвиг для обращения\n"
                "# Для обращения нужен a_0=0, поэтому используем производную\n"
                "ctx.mode = 'stirling'\n"
                "ctx.bottom_row = [float(x) for x in a_seq[:ctx.ncols]]"
            )
        },
        {
            "name": "Действие 8: Сброс матрицы",
            "action_desc": "Сброс к исходному состоянию",
            "action": (
                "ctx.mode = 'stirling'\n"
                "ctx.seq = []\n"
                "ctx.bottom_row = []"
            )
        },
    ]
}


class ActionContext:
    """Контекст, передаваемый в exec() для кода действия."""
    def __init__(self, app):
        self.mode = app.mode_var.get()
        self.nrows, self.ncols = app.get_size()
        self.seq = list(getattr(app, 'seq', []))
        self.bottom_row = list(getattr(app, 'bottom_row', []))
        self.triangle = None

    def apply_to(self, app):
        app.mode_var.set(self.mode)
        app.seq = list(self.seq)
        app.bottom_row = list(self.bottom_row)
        app.refresh()


class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Эмулятор Юпаны")
        self.root.geometry("1100x800")

        self.size_var = tk.StringVar(value="9x9")
        self.mode_var = tk.StringVar(value="stirling")
        self.action_var = tk.StringVar()

        self.action_count = 0
        self.tokapu_buttons = []
        self.btn_width = 50
        self.btn_height = 45
        self.btn_spacing_x = 58
        self.btn_spacing_y = 55
        self.max_cols = 16

        self.seq = []
        self.bottom_row = []

        self.action_history = []
        self.loaded_macros = {}
        self.yupanki0_actions = []
        self.current_action_values = []

        self.ensure_yupanki0()
        self.load_yupanki0()

        self.build_ui()
        self.refresh()

    def ensure_yupanki0(self):
        os.makedirs(YUPANKI_DIR, exist_ok=True)
        path = os.path.join(YUPANKI_DIR, "yupanki0.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(YUPANKI0_DATA, f, ensure_ascii=False, indent=2)

    def load_yupanki0(self):
        path = os.path.join(YUPANKI_DIR, "yupanki0.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = YUPANKI0_DATA
        self.yupanki0_actions = data.get("actions", [])
        self.current_action_values = [a["name"] for a in self.yupanki0_actions]
        if self.current_action_values:
            self.action_var.set(self.current_action_values[0])

    def execute_action_code(self, code, ctx):
        if not code or not code.strip():
            return ""
        output = io.StringIO()
        namespace = {
            "ctx": ctx, "math": math, "S_MAX": S_MAX,
            "compute_a391838": compute_a391838,
            "compositional_inverse": compositional_inverse,
            "multiplicative_inverse": multiplicative_inverse,
            "difference_triangle": difference_triangle,
            "export_matrix_csv": export_matrix_csv,
            "export_sequence_json": export_sequence_json,
            "export_spice_subcircuit": export_spice_subcircuit,
        }
        try:
            with contextlib.redirect_stdout(output):
                exec(code, namespace)
        except Exception as e:
            return f"Ошибка: {e}"
        return output.getvalue().strip()

    def build_ui(self):
        # Верхняя панель
        top = ttk.Frame(self.root, padding=5)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Размер:").pack(side=tk.LEFT, padx=(0, 5))
        for sz in ["6x6", "9x9", "18x9"]:
            rb = ttk.Radiobutton(top, text=sz, value=sz,
                                variable=self.size_var,
                                command=self.refresh)
            rb.pack(side=tk.LEFT, padx=2)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(top, text="Режим:").pack(side=tk.LEFT, padx=(0, 5))
        mode_combo = ttk.Combobox(top, textvariable=self.mode_var, width=18,
                                  state="readonly", values=[
                                      "stirling", "rassnos", "diagonal",
                                      "diff", "normalized", "fibonacci"])
        mode_combo.pack(side=tk.LEFT, padx=2)
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Экспорт
        ttk.Button(top, text="Экспорт CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top, text="Экспорт JSON", command=self.export_json).pack(side=tk.RIGHT, padx=2)
        ttk.Button(top, text="Экспорт SPICE", command=self.export_spice).pack(side=tk.RIGHT, padx=2)

        # Матрицы
        matrix_frame = ttk.Frame(self.root)
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.matrix_a_frame = ttk.LabelFrame(matrix_frame, text="Матрица A", padding=5)
        self.matrix_a_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.matrix_b_frame = ttk.LabelFrame(matrix_frame, text="Матрица B (после действия)", padding=5)
        self.matrix_b_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель действий
        action_frame = ttk.Frame(self.root, padding=5)
        action_frame.pack(fill=tk.X)

        ttk.Label(action_frame, text="Действие:").pack(side=tk.LEFT, padx=(0, 5))
        self.action_combo = ttk.Combobox(action_frame, textvariable=self.action_var,
                                          width=50, state="readonly",
                                          values=self.current_action_values)
        self.action_combo.pack(side=tk.LEFT, padx=2)
        self.action_combo.bind("<<ComboboxSelected>>", self.on_action)

        ttk.Button(action_frame, text="Загрузить",
                   command=self.load_yupanki).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Очистить Юпану",
                   command=self.clear_tokapu).pack(side=tk.RIGHT, padx=5)

        # Токапу
        tokapu_outer = ttk.Frame(self.root, padding=5)
        tokapu_outer.pack(fill=tk.BOTH, expand=False)

        ttk.Label(tokapu_outer, text="Токапу:").pack(anchor=tk.W)

        self.tokapu_canvas = tk.Canvas(tokapu_outer, height=60, bg="#F5F0E0",
                                        highlightthickness=1,
                                        highlightbackground="#999")
        self.tokapu_canvas.pack(fill=tk.BOTH, expand=True)

        # Протокол
        proto_frame = ttk.Frame(self.root, padding=5)
        proto_frame.pack(fill=tk.X)

        ttk.Label(proto_frame, text="Протокол:").pack(anchor=tk.W)
        self.protocol_text = tk.Text(proto_frame, height=5, state=tk.DISABLED,
                                     bg="#FAFAF0", wrap=tk.WORD)
        self.protocol_text.pack(fill=tk.X)

    def get_size(self):
        s = self.size_var.get()
        if s == "6x6": return 6, 6
        if s == "9x9": return 9, 9
        if s == "18x9": return 18, 9
        return 9, 9

    def get_matrix_values(self, mode, nrows, ncols):
        """Делегирует в yupana_math."""
        highlight = set()

        if mode == "stirling":
            values = stirling_matrix(nrows, ncols, S_MAX)
        elif mode == "rassnos":
            values = rassnos_matrix(nrows, ncols)
        elif mode == "diagonal":
            values, highlight = a391838_diagonal(nrows, ncols, S_MAX)
        elif mode == "diff":
            values = diff_matrix(nrows, ncols, S_MAX)
        elif mode == "normalized":
            values = normalized_matrix(nrows, ncols, S_MAX)
            for n in range(nrows):
                highlight.add((n, 0))
        elif mode == "fibonacci":
            values, highlight = fibonacci_diagonal(nrows, ncols, S_MAX)
        else:
            values = [[0]*ncols for _ in range(nrows)]

        return values, highlight

    def format_cell(self, val, n, k):
        if val == 0:
            return ""
        if isinstance(val, Fraction):
            if val.denominator == 1:
                v = val.numerator
                if k == 0:
                    return str(v)
                return f"{v}\u00B7x^{k}"
            else:
                s = str(val)
                return f"{s}\u00B7x^{k}"
        if isinstance(val, float) and val == int(val):
            val = int(val)
        if isinstance(val, int):
            if k == 0:
                return str(val)
            return f"{val}\u00B7x^{k}"
        else:
            if abs(val - round(val)) < 1e-9:
                v = int(round(val))
                if k == 0:
                    return str(v)
                return f"{v}\u00B7x^{k}"
            s = f"{val:.3g}"
            return f"{s}\u00B7x^{k}"

    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, hl = self.get_matrix_values(mode, nrows, ncols)

        bottom = self.bottom_row[:ncols] if self.bottom_row else []

        # Матрица A — исходная (всегда stirling)
        a_values = stirling_matrix(nrows, ncols, S_MAX)
        self.build_matrix(self.matrix_a_frame, "A", a_values, set(), nrows, ncols, bottom)

        # Матрица B — после действия (текущий режим)
        self.build_matrix(self.matrix_b_frame, "B", values, hl, nrows, ncols, bottom)

    def build_matrix(self, parent, name, values, highlight, nrows, ncols, bottom_row):
        for w in parent.winfo_children():
            w.destroy()

        hdr = ttk.Frame(parent)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="", width=3).pack(side=tk.LEFT)
        for c in range(ncols):
            ttk.Label(hdr, text=str(c), width=8, anchor=tk.CENTER).pack(side=tk.LEFT)

        for r in range(nrows):
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill=tk.X)
            ttk.Label(row_frame, text=str(r), width=3).pack(side=tk.LEFT)
            for c in range(ncols):
                val = values[r][c]
                text = self.format_cell(val, r, c)
                bg = "#E8E8FF" if (r, c) in highlight else "#FFFFFF"
                lbl = tk.Label(row_frame, text=text, width=8, anchor=tk.CENTER,
                               relief=tk.GROOVE, bg=bg, font=("Consolas", 9))
                lbl.pack(side=tk.LEFT)

        # Нижняя строка — коэффициенты последовательности
        if bottom_row:
            ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
            bottom_frame = ttk.Frame(parent)
            bottom_frame.pack(fill=tk.X)
            ttk.Label(bottom_frame, text="\u2193", width=3,
                      anchor=tk.CENTER, font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
            for c in range(ncols):
                if c < len(bottom_row):
                    val = bottom_row[c]
                    text = self.format_cell(val, 0, c)
                else:
                    text = ""
                lbl = tk.Label(bottom_frame, text=text, width=8, anchor=tk.CENTER,
                               relief=tk.GROOVE, bg="#F0E8D0",
                               font=("Consolas", 9, "bold"))
                lbl.pack(side=tk.LEFT)

    def add_tokapu_button(self, btn_text, bg_color="#D4C5A0"):
        col = (self.action_count - 1) % self.max_cols
        row = (self.action_count - 1) // self.max_cols

        x = 10 + col * self.btn_spacing_x
        y = 5 + row * self.btn_spacing_y

        needed_height = y + self.btn_height + 10
        if needed_height > int(self.tokapu_canvas.cget("height")):
            self.tokapu_canvas.config(height=needed_height)

        btn = tk.Button(self.tokapu_canvas, text=btn_text, width=4, height=2,
                        font=("Arial", 9),
                        bg=bg_color, activebackground="#E8D8B8",
                        relief=tk.RAISED, bd=2)
        self.tokapu_canvas.create_window(x, y, anchor=tk.NW, window=btn)
        self.tokapu_buttons.append(btn)

    def on_action(self, event=None):
        selected = self.action_var.get()

        if selected in self.loaded_macros:
            self.play_macro(selected)
            return

        action = None
        for a in self.yupanki0_actions:
            if a["name"] == selected:
                action = a
                break
        if not action:
            return

        self.action_count += 1
        glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
        btn_text = f"{self.action_count}{glyph}"
        self.add_tokapu_button(btn_text)

        ctx = ActionContext(self)
        output = self.execute_action_code(action.get("action", ""), ctx)
        ctx.apply_to(self)

        self.action_history.append({
            "name": action["name"],
            "action_desc": action.get("action_desc", ""),
            "action": action.get("action", "")
        })

        self.log(f"[{self.action_count}] {action['name']}")
        if action.get("action_desc"):
            self.log(f"  {action['action_desc']}")
        if output:
            self.log(f"  > {output}")

    def play_macro(self, macro_name):
        macro = self.loaded_macros[macro_name]
        actions = macro.get("actions", [])
        desc = macro.get("desc", "")

        m = re.match(r'yupanki(\d+)', macro_name)
        macro_num = int(m.group(1)) if m else 0

        self.action_count += 1
        glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
        btn_text = f"{glyph}{macro_num}"
        self.add_tokapu_button(btn_text, bg_color="#C4A882")

        self.log(f"[{self.action_count}] {macro_name}")
        if desc:
            self.log(f"  {desc}")
        else:
            self.log("  (action_desc пуст - заполните в JSON)")

        ctx = ActionContext(self)
        self.log(f"  \u25B6 Подпоследовательность: {len(actions)} действий")
        for i, act in enumerate(actions):
            name = act.get("name", f"Действие {i}")
            action_desc = act.get("action_desc", "")
            code = act.get("action", "")
            self.log(f"    [{i+1}] {name}")
            if action_desc:
                self.log(f"        {action_desc}")
            output = self.execute_action_code(code, ctx)
            if output:
                self.log(f"        > {output}")
        ctx.apply_to(self)
        self.log(f"  \u25A0 Конец подпоследовательности")

        self.action_history.append({
            "macro": macro_name,
            "name": macro_name,
            "action_desc": desc,
            "actions": actions
        })

    def get_next_yupanki_number(self):
        if not os.path.isdir(YUPANKI_DIR):
            return 1
        max_num = 0
        pattern = re.compile(r'^yupanki(\d+)\.json$')
        for fname in os.listdir(YUPANKI_DIR):
            m = pattern.match(fname)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        return max_num + 1

    def save_yupanki(self):
        if not self.action_history:
            self.log("Нет действий для сохранения")
            return None

        os.makedirs(YUPANKI_DIR, exist_ok=True)
        num = self.get_next_yupanki_number()
        filename = f"yupanki{num}.json"
        filepath = os.path.join(YUPANKI_DIR, filename)

        data = {
            "name": f"yupanki{num}",
            "action_desc": "",
            "actions": []
        }

        for entry in self.action_history:
            if "macro" in entry:
                data["actions"].append({
                    "name": entry["name"],
                    "action_desc": entry.get("action_desc", ""),
                    "action": "",
                    "macro": entry["macro"],
                    "sub_actions": entry.get("actions", [])
                })
            else:
                data["actions"].append({
                    "name": entry["name"],
                    "action_desc": entry.get("action_desc", ""),
                    "action": entry.get("action", "")
                })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.log(f"Сохранено: {filepath} ({len(self.action_history)} действий)")
        return filename

    def load_yupanki(self):
        if not os.path.isdir(YUPANKI_DIR):
            os.makedirs(YUPANKI_DIR, exist_ok=True)
            messagebox.showinfo("Загрузка", f"Каталог {YUPANKI_DIR} создан, но пуст.")
            return

        filepath = filedialog.askopenfilename(
            title="Выберите yupanki-файл",
            initialdir=os.path.abspath(YUPANKI_DIR),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось прочитать файл:\n{e}")
            return

        macro_name = data.get("name", os.path.splitext(os.path.basename(filepath))[0])
        desc = data.get("action_desc", "")
        actions = data.get("actions", [])

        flat_actions = []
        for act in actions:
            if act.get("macro"):
                sub = act.get("sub_actions", [])
                flat_actions.extend(sub)
            else:
                flat_actions.append(act)

        self.loaded_macros[macro_name] = {
            "path": filepath,
            "actions": flat_actions,
            "desc": desc
        }

        if macro_name not in self.current_action_values:
            self.current_action_values.append(macro_name)
            self.action_combo["values"] = self.current_action_values

        self.log(f"Загружен макрос: {macro_name}")
        if desc:
            self.log(f"  action_desc: {desc}")
        else:
            self.log("  action_desc: (пусто - заполните вручную в JSON)")

    def clear_tokapu(self):
        saved = self.save_yupanki()
        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons = []
        self.action_count = 0
        self.action_history = []
        self.tokapu_canvas.config(height=60)
        self.log("--- Очистка Юпаны ---")

    def log(self, msg):
        self.protocol_text.config(state=tk.NORMAL)
        self.protocol_text.insert(tk.END, msg + "\n")
        self.protocol_text.see(tk.END)
        self.protocol_text.config(state=tk.DISABLED)

    # Экспорт

    def export_csv(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = self.get_matrix_values(mode, nrows, ncols)
        filepath = filedialog.asksaveasfilename(
            title="Экспорт CSV", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if filepath:
            export_matrix_csv(values, filepath)
            self.log(f"Экспорт CSV: {filepath}")

    def export_json(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = self.get_matrix_values(mode, nrows, ncols)
        seq = self.bottom_row[:ncols] if self.bottom_row else []
        filepath = filedialog.asksaveasfilename(
            title="Экспорт JSON", defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if filepath:
            export_sequence_json(seq, filepath, metadata={
                "mode": mode, "size": f"{nrows}x{ncols}",
                "matrix": [[float(v) if isinstance(v, Fraction) else v
                            for v in row] for row in values]
            })
            self.log(f"Экспорт JSON: {filepath}")

    def export_spice(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = self.get_matrix_values(mode, nrows, ncols)
        filepath = filedialog.asksaveasfilename(
            title="Экспорт SPICE netlist", defaultextension=".sp",
            filetypes=[("SPICE", "*.sp"), ("All", "*.*")])
        if filepath:
            spice = export_spice_subcircuit(values, name=f"yupana_{mode}",
                                             nrows=nrows, ncols=ncols)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(spice)
            self.log(f"Экспорт SPICE: {filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaApp(root)
    root.mainloop()
