"""
yupana_emulator.py — Эмулятор Юпаны с Tkinter GUI.

Импортирует yupana_math (чистая математика, без GUI).
Две матрицы: A (исходная — Стирлинг) и B (после действия).
Три кнопки экспорта: CSV, JSON, SPICE.
Макросы yupanki: сохранение/загрузка последовательностей действий.
"""

import sys
import os

# ── Подключение локального модуля yupana_math ─────────────────────────────────
# Добавляем каталог этого скрипта в sys.path — работает на Windows и Linux
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from yupana_math import (
    S_MAX,
    get_matrix_values,
    compute_a391838,
    compute_a391838_sequence,
    verify_a391838,
    multiplicative_inverse,
    compositional_inverse,
    difference_triangle,
    format_cell_display,
    export_matrix_csv,
    export_sequence_json,
    export_spice_subcircuit,
    a391838_to_float,
)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import math
import json
import re
import io
import contextlib
from fractions import Fraction

from yupana_arrays import (
    GLYPHS,
    YUPANKI_DIR,
    YUPANKI0_DATA,
)

from yupana_symbols_matrix import YupanaSymbolMatrix

# ──────────────────────────────────────────────────────────────────────────────
# Контекст для exec() кода действий
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────────────────────────────────────────

class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Эмулятор Юпаны")
        self.root.geometry("1725x900")

        self.size_var = tk.StringVar(value="9x9")
        self.mode_var = tk.StringVar(value="stirling")
        self.action_var = tk.StringVar()

        self.action_count = 0
        self.tokapu_buttons = []
        self.btn_spacing_x = 58
        self.btn_spacing_y = 55
        self.max_cols = 16

        # Последовательность и нижняя строка
        self.seq = []
        self.bottom_row = []

        # История действий текущей сессии
        self.action_history = []

        # Загруженные макросы
        self.loaded_macros = {}

        # Действия из yupanki0
        self.yupanki0_actions = []

        # Значения выпадающего списка
        self.current_action_values = []

        # Создание и загрузка yupanki0
        self.ensure_yupanki0()
        self.load_yupanki0()

        self.symbol_engine = YupanaSymbolMatrix("receptacle.json")
        # Можно задать начальный сдвиг, если нужно
        # self.symbol_engine.set_offset(0, 0) 
        self.symbol_engine.set_offset(1, 1)


        self.build_ui()
        self.refresh()

    # ── yupanki0 ────────────────────────────────────────────────────────────────

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

    # ── Выполнение кода действия ────────────────────────────────────────────────

    def execute_action_code(self, code, ctx):
        if not code or not code.strip():
            return ""
        output = io.StringIO()
        namespace = {
            "ctx": ctx,
            "math": math,
            "S_MAX": S_MAX,
            "Fraction": Fraction,
            "compute_a391838": compute_a391838,
            "compute_a391838_sequence": compute_a391838_sequence,
            "difference_triangle": difference_triangle,
            "__builtins__": __builtins__,
        }
        try:
            with contextlib.redirect_stdout(output):
                exec(code, namespace)
        except Exception as e:
            return f"Ошибка: {e}"
        return output.getvalue().strip()

    # ── UI ────────────────────────────────────────────────────────────────────

    def build_ui(self):
        # ── Верхняя панель ──────────────────────────────────────────────────
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

        # Кнопки экспорта
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(top, text="Экспорт CSV", command=self.export_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Экспорт JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Экспорт SPICE", command=self.export_spice).pack(side=tk.LEFT, padx=2)


        # Переключатель DDF
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.ddf_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="DDF", variable=self.ddf_var,
                        command=self.refresh).pack(side=tk.LEFT, padx=2)


        # ── Область матриц ─────────────────────────────────────────────────
        matrix_frame = ttk.Frame(self.root)
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.matrix_a_frame = ttk.LabelFrame(matrix_frame, text="Матрица A (исходная — Стирлинг)", padding=5)
        self.matrix_a_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.matrix_b_frame = ttk.LabelFrame(matrix_frame, text="Матрица B (после действия)", padding=5)
        self.matrix_b_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Панель действий ─────────────────────────────────────────────────
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

        # ── Область токапу ──────────────────────────────────────────────────
        tokapu_outer = ttk.Frame(self.root, padding=5)
        tokapu_outer.pack(fill=tk.BOTH, expand=False)

        ttk.Label(tokapu_outer, text="Токапу:").pack(anchor=tk.W)

        self.tokapu_canvas = tk.Canvas(tokapu_outer, height=60, bg="#F5F0E0",
                                        highlightthickness=1,
                                        highlightbackground="#999")
        self.tokapu_canvas.pack(fill=tk.BOTH, expand=True)

        # ── Протокол ─────────────────────────────────────────────────────────
        proto_frame = ttk.Frame(self.root, padding=5)
        proto_frame.pack(fill=tk.X)

        ttk.Label(proto_frame, text="Протокол:").pack(anchor=tk.W)
        self.protocol_text = tk.Text(proto_frame, height=5, state=tk.DISABLED,
                                     bg="#FAFAF0", wrap=tk.WORD)
        self.protocol_text.pack(fill=tk.X)

        # Стартовая запись
        ok = verify_a391838()
        self.log(f"Эмулятор Юпаны запущен. A391838 проверен: {'OK' if ok else 'FAIL'}")

    # ── Размеры ──────────────────────────────────────────────────────────────

    def get_size(self):
        s = self.size_var.get()
        if s == "6x6": return 6, 6
        if s == "9x9": return 9, 9
        if s == "18x9": return 18, 9
        return 9, 9

    # ── Перерисовка ────────────────────────────────────────────────────────────

    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()

        # Матрица A — всегда Стирлинг (исходная)
        a_values, a_hl = get_matrix_values("stirling", nrows, ncols)

        # Матрица B — текущий режим
        b_values, b_hl = get_matrix_values(mode, nrows, ncols)

        # Усечение нижней строки
        bottom = self.bottom_row[:ncols] if self.bottom_row else []

        self.build_matrix(self.matrix_a_frame, a_values, a_hl, nrows, ncols, bottom)
        self.build_matrix(self.matrix_b_frame, b_values, b_hl, nrows, ncols, bottom)

    def build_matrix(self, parent, values, highlight, nrows, ncols, bottom_row):
        for w in parent.winfo_children():
            w.destroy()

        if not hasattr(self, 'cached_images'):
            self.cached_images = {}

        symbols_dir = os.path.join(_SCRIPT_DIR, "symbols")

        CELL_W_PX = 74
        CELL_H_PX = 56
        IMG_SIZE = (24, 24)
        CELL_W_CHARS = 10
        HDR_H_PX = 20

        ddf_on = getattr(self, 'ddf_var', None) and self.ddf_var.get()

        # Заголовок столбцов
        hdr = ttk.Frame(parent)
        hdr.pack(fill=tk.X)
        corner = tk.Frame(hdr, width=24, height=HDR_H_PX)
        corner.pack_propagate(False)
        corner.pack(side=tk.LEFT)
        for c in range(ncols):
            hdr_cell = tk.Frame(hdr, width=CELL_W_PX, height=HDR_H_PX)
            hdr_cell.pack_propagate(False)
            hdr_cell.pack(side=tk.LEFT)
            ttk.Label(hdr_cell, text=str(c), anchor=tk.CENTER,
                      font=("Consolas", 9, "bold")).pack(expand=True, fill=tk.BOTH)

        # Основная матрица
        for r in range(nrows):
            row_frame = ttk.Frame(parent)
            row_frame.pack(fill=tk.X)
            row_lbl_cell = tk.Frame(row_frame, width=24, height=CELL_H_PX)
            row_lbl_cell.pack_propagate(False)
            row_lbl_cell.pack(side=tk.LEFT)
            tk.Label(row_lbl_cell, text=str(r), anchor=tk.CENTER,
                     font=("Consolas", 9, "bold")).pack(expand=True, fill=tk.BOTH)

            for c in range(ncols):
                val = values[r][c] if r < len(values) and c < len(values[r]) else 0
                text = format_cell_display(val, r, c)

                # ── Цвет клетки ──────────────────────────────────────────────
                if (r, c) in highlight:
                    bg = "#E8E8FF"
                elif hasattr(self, 'symbol_engine'):
                    bg = self.symbol_engine.get_cell_color(r, c)
                else:
                    bg = "#FFFFFF"

                # ── Определяем отображаемый текст ────────────────────────────
                formula = None
                formula_color = "#006600"   # зелёный — по умолчанию для диагоналей с t
                formula_font = ("Consolas", 7)

                if hasattr(self, 'symbol_engine'):
                    # Проверяем: это чётный столбец и включён DDF?
                    if ddf_on and (c - self.symbol_engine.offset[1]) % 2 == 1:
                        # Чётный display-столбец → форма без t, красным
                        even_formula = self.symbol_engine.get_even_col_formula(r, c, val)
                        if even_formula:
                            formula = even_formula
                            formula_color = "#CC0000"   # красный
                    else:
                        # Нечётный display-столбец → диагональ с t, зелёным
                        formula = self.symbol_engine.get_diagonal_formula(r, c, val)

                display_text = formula if formula else text
                if formula:
                    txt_font = formula_font
                    txt_fg = formula_color
                else:
                    txt_font = ("Consolas", 9)
                    txt_fg = "#000000"

                # Контейнер ячейки
                cell = tk.Frame(row_frame, width=CELL_W_PX, height=CELL_H_PX,
                                relief=tk.GROOVE, bg=bg, bd=1)
                cell.pack_propagate(False)
                cell.pack(side=tk.LEFT)

                # ── Картинка символа ─────────────────────────────────────────
                has_image = False
                if hasattr(self, 'symbol_engine'):
                    filename = self.symbol_engine.get_filename_for_symbol(r, c)
                    if filename:
                        img_path = os.path.join(symbols_dir, filename)
                        if os.path.exists(img_path):
                            if filename not in self.cached_images:
                                try:
                                    from PIL import Image, ImageTk
                                    pil_img = Image.open(img_path)
                                    pil_img = pil_img.resize(IMG_SIZE, Image.LANCZOS)
                                    tk_img = ImageTk.PhotoImage(pil_img)
                                    self.cached_images[filename] = tk_img
                                except Exception:
                                    self.cached_images[filename] = None

                            tk_img = self.cached_images.get(filename)
                            if tk_img is not None:
                                img_lbl = tk.Label(cell, image=tk_img, bg=bg)
                                img_lbl.pack(side=tk.TOP, pady=(2, 1))
                                has_image = True

                # ── Текст ────────────────────────────────────────────────────
                txt_lbl = tk.Label(cell, text=display_text, width=CELL_W_CHARS,
                                   anchor=tk.CENTER, bg=bg, font=txt_font, fg=txt_fg)
                txt_lbl.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Нижняя строка
        if bottom_row:
            ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=3)
            bottom_frame = ttk.Frame(parent)
            bottom_frame.pack(fill=tk.X)
            corner2 = tk.Frame(bottom_frame, width=24)
            corner2.pack_propagate(False)
            corner2.pack(side=tk.LEFT)
            for c in range(ncols):
                b_cell = tk.Frame(bottom_frame, width=CELL_W_PX)
                b_cell.pack_propagate(False)
                b_cell.pack(side=tk.LEFT)
                if c < len(bottom_row):
                    val = bottom_row[c]
                    text = format_cell_display(val, 0, c)
                else:
                    text = ""
                tk.Label(b_cell, text=text, width=CELL_W_CHARS, anchor=tk.CENTER,
                         relief=tk.GROOVE, bg="#F0E8D0",
                         font=("Consolas", 9, "bold")).pack(expand=True, fill=tk.BOTH)







    # ── Кнопка-глиф ────────────────────────────────────────────────────────────

    def add_tokapu_button(self, btn_text, bg_color="#D4C5A0"):
        col = (self.action_count - 1) % self.max_cols
        row = (self.action_count - 1) // self.max_cols

        x = 10 + col * self.btn_spacing_x
        y = 5 + row * self.btn_spacing_y

        needed_height = y + 50 + 10
        if needed_height > int(self.tokapu_canvas.cget("height")):
            self.tokapu_canvas.config(height=needed_height)

        btn = tk.Button(self.tokapu_canvas, text=btn_text, width=4, height=2,
                        font=("Arial", 9),
                        bg=bg_color, activebackground="#E8D8B8",
                        relief=tk.RAISED, bd=2)
        self.tokapu_canvas.create_window(x, y, anchor=tk.NW, window=btn)
        self.tokapu_buttons.append(btn)

    # ── Обработка действия ────────────────────────────────────────────────────

    def on_action(self, event=None):
        selected = self.action_var.get()

        # Макрос yupankiN?
        if selected in self.loaded_macros:
            self.play_macro(selected)
            return

        # Встроенное действие
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

    # ── Проигрывание макроса ───────────────────────────────────────────────────

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
            self.log("  (описание пусто)")

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

    # ── Экспорт ────────────────────────────────────────────────────────────────

    def export_csv(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = get_matrix_values(mode, nrows, ncols)
        csv_str = export_matrix_csv(values, mode, ncols)

        filepath = filedialog.asksaveasfilename(
            title="Сохранить CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_str)
        self.log(f"CSV сохранён: {filepath}")

    def export_json(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = get_matrix_values(mode, nrows, ncols)
        seq = self.seq if self.seq else compute_a391838_sequence(8)
        json_str = export_sequence_json(seq, mode, values)

        filepath = filedialog.asksaveasfilename(
            title="Сохранить JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
        self.log(f"JSON сохранён: {filepath}")

    def export_spice(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, _ = get_matrix_values(mode, nrows, ncols)
        name = f"yupana_{mode}_{nrows}x{ncols}"
        spice_str = export_spice_subcircuit(values, name, ncols)

        filepath = filedialog.asksaveasfilename(
            title="Сохранить SPICE нетлист",
            defaultextension=".sp",
            filetypes=[("SPICE files", "*.sp *.cir *.sub"), ("All files", "*.*")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(spice_str)
        self.log(f"SPICE нетлист сохранён: {filepath}")

    # ── yupanki: сохранение ────────────────────────────────────────────────────

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

    # ── yupanki: загрузка ──────────────────────────────────────────────────────

    def load_yupanki(self):
        if not os.path.isdir(YUPANKI_DIR):
            os.makedirs(YUPANKI_DIR, exist_ok=True)
            messagebox.showinfo("Загрузка", f"Каталог {YUPANKI_DIR} создан, но пуст.")
            return

        filepath = filedialog.askopenfilename(
            title="Выберите yupanki-файл",
            initialdir=os.path.abspath(YUPANKI_DIR),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
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
            self.log("  action_desc: (пусто)")

    # ── Очистка ────────────────────────────────────────────────────────────────

    def clear_tokapu(self):
        saved = self.save_yupanki()
        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons = []
        self.action_count = 0
        self.action_history = []
        self.tokapu_canvas.config(height=60)
        self.log("--- Очистка Юпаны ---")

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

