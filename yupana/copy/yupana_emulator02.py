"""
yupana_emulator.py — Эмулятор Юпаны с Tkinter GUI.

Импортирует всю математику из yupana_math.py.
Матрицы A и B разделены: A — исходная (stirling), B — после действия.
Экспорт: CSV, JSON, SPICE .subckt.
Макросы yupanki: сохранение/загрузка последовательностей действий.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import json
import re
import io
import contextlib

from yupana_math import (
    S_MAX,
    rassnos_matrix, stirling_matrix, diff_matrix, normalized_matrix,
    fibonacci_diagonal, a391838_diagonal,
    compute_a391838, a391838_sequence, a391838_normalized,
    verify_a391838,
    multiplicative_inverse,
    difference_triangle,
    triangular_number, find_triangular_representation,
    a391838_triangular_indices,
    export_matrix_csv, export_sequence_json, export_spice_subcircuit,
    format_cell_display, matrix_to_display,
    format_fraction,
)
from fractions import Fraction

GLYPHS = [
    '\u25CF', '\u25C6', '\u25B2', '\u25A0', '\u2605',
    '\u2724', '\u2725', '\u2726', '\u2727', '\u2728',
    '\u2729', '\u272A', '\u272B', '\u272C', '\u272D',
    '\u272E', '\u272F', '\u2730', '\u2731', '\u2732',
    '\u2733', '\u2734', '\u2735', '\u2736', '\u2737',
    '\u2738', '\u2739', '\u273A', '\u273B', '\u273C',
    '\u273D', '\u273E', '\u273F', '\u2740', '\u2741',
    '\u2742', '\u2743', '\u2744', '\u2745', '\u2746',
]

YUPANKI_DIR = "yupanki"

# yupanki0: встроенные действия
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
            "action_desc": "Разностная схема (биномиальные коэффициенты)",
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
            "name": "Действие 7: Обращение ряда (A391838)",
            "action_desc": "Вычисление коэффициентов A391838 через диагонали Стирлинга",
            "action": (
                "from yupana_math import a391838_sequence\n"
                "ctx.seq = a391838_sequence(10)\n"
                "ctx.bottom_row = ctx.seq[:ctx.ncols]\n"
                "ctx.mode = 'stirling'"
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
    """Контекст для exec() кода действия."""
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
        self.root.geometry("1200x850")

        self.size_var = tk.StringVar(value="9x9")
        self.mode_var = tk.StringVar(value="stirling")
        self.action_var = tk.StringVar()

        self.action_count = 0
        self.tokapu_buttons = []
        self.btn_spacing_x = 58
        self.btn_spacing_y = 55
        self.btn_height = 45
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

        # Автозапуск действия 0 (инициализация)
        self.execute_builtin(0)
        self.refresh()

    # ── yupanki0 ──────────────────────────────────────────────────────────────

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

    # ── exec code ──────────────────────────────────────────────────────────────

    def execute_action_code(self, code, ctx):
        if not code or not code.strip():
            return ""
        output = io.StringIO()
        namespace = {
            "ctx": ctx, "math": math, "S_MAX": S_MAX,
            "Fraction": Fraction, "difference_triangle": difference_triangle,
            "compute_a391838": compute_a391838, "a391838_sequence": a391838_sequence,
        }
        try:
            with contextlib.redirect_stdout(output):
                exec(code, namespace)
        except Exception as e:
            return f"Error: {e}"
        return output.getvalue().strip()

    def execute_builtin(self, idx):
        """Выполняет встроенное действие по индексу (без кнопки токапу)."""
        if idx < 0 or idx >= len(self.yupanki0_actions):
            return
        action = self.yupanki0_actions[idx]
        ctx = ActionContext(self)
        self.execute_action_code(action.get("action", ""), ctx)
        ctx.apply_to(self)

    # ── UI ────────────────────────────────────────────────────────────────────

    def build_ui(self):
        # Верхняя панель
        top = ttk.Frame(self.root, padding=5)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Размер:").pack(side=tk.LEFT, padx=(0, 5))
        for sz in ["6x6", "9x9", "18x9"]:
            ttk.Radiobutton(top, text=sz, value=sz,
                           variable=self.size_var,
                           command=self.refresh).pack(side=tk.LEFT, padx=2)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Label(top, text="Режим:").pack(side=tk.LEFT, padx=(0, 5))
        mode_combo = ttk.Combobox(top, textvariable=self.mode_var, width=18,
                                 state="readonly", values=[
                                     "stirling", "rassnos", "diagonal",
                                     "diff", "normalized", "fibonacci"])
        mode_combo.pack(side=tk.LEFT, padx=2)
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Экспорт
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(top, text="CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="SPICE", command=self.export_spice).pack(side=tk.LEFT, padx=2)

        # Матрицы
        matrix_frame = ttk.Frame(self.root)
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.matrix_a_frame = ttk.LabelFrame(matrix_frame, text="Матрица A (исходная)", padding=5)
        self.matrix_a_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.matrix_b_frame = ttk.LabelFrame(matrix_frame, text="Матрица B (после действия)", padding=5)
        self.matrix_b_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель действий
        action_frame = ttk.Frame(self.root, padding=5)
        action_frame.pack(fill=tk.X)

        ttk.Label(action_frame, text="Действие:").pack(side=tk.LEFT, padx=(0, 5))
        self.action_combo = ttk.Combobox(action_frame, textvariable=self.action_var,
                                         width=55, state="readonly",
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

    # ── Размеры ────────────────────────────────────────────────────────────────

    def get_size(self):
        s = self.size_var.get()
        if s == "6x6": return 6, 6
        if s == "9x9": return 9, 9
        if s == "18x9": return 18, 9
        return 9, 9

    # ── Значения матрицы ───────────────────────────────────────────────────────

    def get_matrix_values(self, mode, nrows, ncols):
        if mode == "stirling":
            return stirling_matrix(nrows, ncols), set()
        elif mode == "rassnos":
            return rassnos_matrix(nrows, ncols), set()
        elif mode == "diagonal":
            return a391838_diagonal(nrows, ncols)
        elif mode == "diff":
            return diff_matrix(nrows, ncols), set()
        elif mode == "normalized":
            vals = normalized_matrix(nrows, ncols)
            hl = set()
            for n in range(nrows):
                hl.add((n, 0))
            return vals, hl
        elif mode == "fibonacci":
            return fibonacci_diagonal(nrows, ncols)
        return [[0]*ncols for _ in range(nrows)], set()

    # ── Перерисовка ────────────────────────────────────────────────────────────

    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()

        # Матрица A — всегда stirling (исходная)
        a_vals, a_hl = stirling_matrix(nrows, ncols), set()
        bottom = self.bottom_row[:ncols] if self.bottom_row else []

        self.build_matrix(self.matrix_a_frame, "A", a_vals, a_hl, nrows, ncols, bottom)

        # Матрица B — текущий режим (после действия)
        b_vals, b_hl = self.get_matrix_values(mode, nrows, ncols)
        self.build_matrix(self.matrix_b_frame, "B", b_vals, b_hl, nrows, ncols, bottom)

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
                text = format_cell_display(val, r, c)
                bg = "#E8E8FF" if (r, c) in highlight else "#FFFFFF"
                tk.Label(row_frame, text=text, width=8, anchor=tk.CENTER,
                        relief=tk.GROOVE, bg=bg, font=("Consolas", 9)).pack(side=tk.LEFT)

        if bottom_row:
            ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
            bottom_frame = ttk.Frame(parent)
            bottom_frame.pack(fill=tk.X)
            ttk.Label(bottom_frame, text="\u2193", width=3,
                     anchor=tk.CENTER, font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
            for c in range(ncols):
                if c < len(bottom_row):
                    val = bottom_row[c]
                    text = format_cell_display(val, 0, c)
                else:
                    text = ""
                tk.Label(bottom_frame, text=text, width=8, anchor=tk.CENTER,
                        relief=tk.GROOVE, bg="#F0E8D0",
                        font=("Consolas", 9, "bold")).pack(side=tk.LEFT)

    # ── Токапу ────────────────────────────────────────────────────────────────

    def add_tokapu_button(self, btn_text, bg_color="#D4C5A0"):
        col = (self.action_count - 1) % self.max_cols
        row = (self.action_count - 1) // self.max_cols
        x = 10 + col * self.btn_spacing_x
        y = 5 + row * self.btn_spacing_y

        needed = y + self.btn_height + 10
        if needed > int(self.tokapu_canvas.cget("height")):
            self.tokapu_canvas.config(height=needed)

        btn = tk.Button(self.tokapu_canvas, text=btn_text, width=4, height=2,
                       font=("Arial", 9), bg=bg_color,
                       activebackground="#E8D8B8", relief=tk.RAISED, bd=2)
        self.tokapu_canvas.create_window(x, y, anchor=tk.NW, window=btn)
        self.tokapu_buttons.append(btn)

    # ── Действия ───────────────────────────────────────────────────────────────

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
        self.add_tokapu_button(f"{self.action_count}{glyph}")

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
        self.add_tokapu_button(f"{glyph}{macro_num}", bg_color="#C4A882")

        self.log(f"[{self.action_count}] {macro_name}")
        if desc:
            self.log(f"  {desc}")
        else:
            self.log("  (action_desc пуст -- заполните в JSON)")

        ctx = ActionContext(self)
        self.log(f"  \u25B6 Подпоследовательность: {len(actions)} действий")
        for i, act in enumerate(actions):
            name = act.get("name", f"Действие {i}")
            ad = act.get("action_desc", "")
            code = act.get("action", "")
            self.log(f"    [{i+1}] {name}")
            if ad:
                self.log(f"        {ad}")
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

    # ── yupanki: сохранение ────────────────────────────────────────────────────

    def get_next_yupanki_number(self):
        if not os.path.isdir(YUPANKI_DIR):
            return 1
        max_num = 0
        pat = re.compile(r'^yupanki(\d+)\.json$')
        for fn in os.listdir(YUPANKI_DIR):
            mm = pat.match(fn)
            if mm:
                n = int(mm.group(1))
                if n > max_num:
                    max_num = n
        return max_num + 1

    def save_yupanki(self):
        if not self.action_history:
            self.log("Нет действий для сохранения")
            return None

        os.makedirs(YUPANKI_DIR, exist_ok=True)
        num = self.get_next_yupanki_number()
        fname = f"yupanki{num}.json"
        fpath = os.path.join(YUPANKI_DIR, fname)

        data = {"name": f"yupanki{num}", "action_desc": "", "actions": []}
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

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.log(f"Сохранено: {fpath} ({len(self.action_history)} действий)")
        return fname

    # ── yupanki: загрузка ──────────────────────────────────────────────────────

    def load_yupanki(self):
        if not os.path.isdir(YUPANKI_DIR):
            os.makedirs(YUPANKI_DIR, exist_ok=True)
            messagebox.showinfo("Загрузка", f"Каталог {YUPANKI_DIR} создан, но пуст.")
            return

        fpath = filedialog.askopenfilename(
            title="Выберите yupanki-файл",
            initialdir=os.path.abspath(YUPANKI_DIR),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not fpath:
            return

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать:\n{e}")
            return

        mname = data.get("name", os.path.splitext(os.path.basename(fpath))[0])
        desc = data.get("action_desc", "")
        actions = data.get("actions", [])

        flat = []
        for act in actions:
            if act.get("macro"):
                flat.extend(act.get("sub_actions", []))
            else:
                flat.append(act)

        self.loaded_macros[mname] = {"path": fpath, "actions": flat, "desc": desc}

        if mname not in self.current_action_values:
            self.current_action_values.append(mname)
            self.action_combo["values"] = self.current_action_values

        self.log(f"Загружен макрос: {mname}")
        if desc:
            self.log(f"  action_desc: {desc}")
        else:
            self.log("  action_desc: (пусто)")

    # ── Экспорт ────────────────────────────────────────────────────────────────

    def export_csv(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        vals, _ = self.get_matrix_values(mode, nrows, ncols)
        fpath = filedialog.asksaveasfilename(
            title="Сохранить CSV", defaultextension=".csv",
            initialdir=os.getcwd(),
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if fpath:
            export_matrix_csv(vals, filename=fpath, mode=mode)
            self.log(f"CSV: {fpath}")

    def export_json(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        seq = self.bottom_row if self.bottom_row else a391838_sequence(min(ncols, 10))
        meta = {"mode": mode, "size": f"{nrows}x{ncols}"}
        if self.seq:
            meta["seq"] = self.seq
        fpath = filedialog.asksaveasfilename(
            title="Сохранить JSON", defaultextension=".json",
            initialdir=os.getcwd(),
            filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if fpath:
            export_sequence_json(seq, filename=fpath, metadata=meta)
            self.log(f"JSON: {fpath}")

    def export_spice(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        vals, _ = self.get_matrix_values(mode, nrows, ncols)
        name = f"yupana_{mode}_{nrows}x{ncols}"
        fpath = filedialog.asksaveasfilename(
            title="Сохранить SPICE .subckt", defaultextension=".sp",
            initialdir=os.getcwd(),
            filetypes=[("SPICE", "*.sp"), ("All", "*.*")])
        if fpath:
            export_spice_subcircuit(vals, name=name, filename=fpath)
            self.log(f"SPICE: {fpath}")

    # ── Очистка ────────────────────────────────────────────────────────────────

    def clear_tokapu(self):
        self.save_yupanki()
        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons = []
        self.action_count = 0
        self.action_history = []
        self.tokapu_canvas.config(height=60)
        self.log("--- Очистка Юпаны ---")
        # Реинициализация
        self.execute_builtin(0)
        self.refresh()

    # ── Протокол ──────────────────────────────────────────────────────────────

    def log(self, msg):
        self.protocol_text.config(state=tk.NORMAL)
        self.protocol_text.insert(tk.END, msg + "\n")
        self.protocol_text.see(tk.END)
        self.protocol_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaApp(root)
    root.mainloop()
