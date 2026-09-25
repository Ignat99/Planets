"""
Эмулятор Юпаны — графический интерфейс для работы с матрицами Стирлинга.

Две матрицы: 6×6, 9×9, 9×18
Режимы заполнения: stirling, rassnos, diagonal, diff, normalized, fibonacci
Действия выбираются из выпадающего списка (без кнопки подтверждения)
Токапу — кнопки-глифы, накапливаются с переносом строк

Макросы yupanki (Forth-стиль):
  yupanki0.json — встроенные действия (создаётся автоматически, грузится при старте)
  yupankiN.json — пользовательские макросы (N >= 1), сохраняются при очистке
  Каждое действие: name, action_desc, action (Python-код, exec с контекстом ctx)
  При выборе макроса: одна кнопка-глиф yN, протокол логирует подпоследовательность
  Нижняя строчка юпаны — коэффициенты последовательности (полином)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import json
import os
import re
import io
import contextlib

# ──────────────────────────────────────────────────────────────────────────────
# Математика: числа Стирлинга и родственные структуры
# ──────────────────────────────────────────────────────────────────────────────

def stirling_first_kind(N):
    """Беззнаковые числа Стирлинга I рода s(n,k)."""
    s = [[0]*(N+1) for _ in range(N+1)]
    s[0][0] = 1
    for n in range(1, N+1):
        for k in range(1, n+1):
            s[n][k] = s[n-1][k-1] + (n-1)*s[n-1][k]
    return s

S_MAX = stirling_first_kind(18)

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

# ──────────────────────────────────────────────────────────────────────────────
# yupanki0.json — встроенные действия
# ──────────────────────────────────────────────────────────────────────────────

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
            "action": (
                "# Построение треугольника разностей из последовательности\n"
                "triangle = [list(ctx.seq)]\n"
                "for i in range(len(ctx.seq) - 1):\n"
                "    current = triangle[-1]\n"
                "    diff = [current[j+1] - current[j] for j in range(len(current) - 1)]\n"
                "    triangle.append(diff)\n"
                "ctx.triangle = triangle\n"
                "ctx.mode = 'rassnos'"
            )
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
            "action_desc": "Заглушка — нужна реализация",
            "action": "ctx.mode = 'stirling'"
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

        # Последовательность и нижняя строка
        self.seq = []
        self.bottom_row = []

        # История действий текущей сессии
        self.action_history = []

        # Загруженные макросы: {"yupanki1": {"actions": [...], "desc": ...}, ...}
        self.loaded_macros = {}

        # Действия из yupanki0
        self.yupanki0_actions = []

        # Значения выпадающего списка
        self.current_action_values = []

        # Создание и загрузка yupanki0
        self.ensure_yupanki0()
        self.load_yupanki0()

        self.build_ui()
        self.refresh()

    # ── yupanki0: встроенные действия ──────────────────────────────────────────

    def ensure_yupanki0(self):
        """Создаёт yupanki/yupanki0.json, если его нет."""
        os.makedirs(YUPANKI_DIR, exist_ok=True)
        path = os.path.join(YUPANKI_DIR, "yupanki0.json")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(YUPANKI0_DATA, f, ensure_ascii=False, indent=2)

    def load_yupanki0(self):
        """Загружает yupanki0.json и заполняет список действий."""
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
        """Выполняет Python-код из поля action с контекстом ctx.
        Возвращает перехваченный stdout."""
        if not code or not code.strip():
            return ""
        output = io.StringIO()
        namespace = {
            "ctx": ctx,
            "math": math,
            "S_MAX": S_MAX,
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

        # ── Область матриц ─────────────────────────────────────────────────
        matrix_frame = ttk.Frame(self.root)
        matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.matrix_a_frame = ttk.LabelFrame(matrix_frame, text="Матрица A", padding=5)
        self.matrix_a_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.matrix_b_frame = ttk.LabelFrame(matrix_frame, text="Матрица B", padding=5)
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

    # ── Размеры ──────────────────────────────────────────────────────────────

    def get_size(self):
        s = self.size_var.get()
        if s == "6x6": return 6, 6
        if s == "9x9": return 9, 9
        if s == "18x9": return 18, 9
        return 9, 9

    # ── Значения матрицы ───────────────────────────────────────────────────────

    def get_matrix_values(self, mode, nrows, ncols):
        values = [[0]*ncols for _ in range(nrows)]
        highlight = set()

        if mode == "stirling":
            for n in range(nrows):
                for k in range(min(n+1, ncols)):
                    values[n][k] = S_MAX[n][k]

        elif mode == 'rassnos':
            for n in range(nrows):
                for k in range(min(n+1, ncols)):
                    values[n][k] = math.comb(n, k)

        elif mode == 'diagonal':
            for n in range(nrows):
                kmax = min(n // 2, ncols - 1)
                for k in range(kmax + 1):
                    row = n - k
                    col = n - 2 * k
                    if 0 <= row < nrows and 0 <= col < ncols:
                        values[n][k] = S_MAX[row][col]
                        highlight.add((n, k))

        elif mode == 'diff':
            for n in range(nrows):
                for k in range(min(n+1, ncols)):
                    if n > 0:
                        values[n][k] = S_MAX[n][k] / n

        elif mode == 'normalized':
            for n in range(nrows):
                for k in range(min(n+1, ncols)):
                    values[n][k] = S_MAX[n][k] / math.factorial(n)
            for n in range(nrows):
                highlight.add((n, 0))

        elif mode == 'fibonacci':
            for n in range(nrows):
                for k in range(min(n+1, ncols)):
                    dk = n - k
                    if 0 <= dk <= n:
                        values[n][k] = S_MAX[n][dk]
                        if dk <= 3:
                            highlight.add((n, k))

        return values, highlight

    # ── Форматирование ячейки ──────────────────────────────────────────────────

    def format_cell(self, val, n, k):
        if val == 0:
            return ""
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

    # ── Перерисовка ────────────────────────────────────────────────────────────

    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        values, hl = self.get_matrix_values(mode, nrows, ncols)

        # Усечение нижней строки под размер юпаны
        bottom = self.bottom_row[:ncols] if self.bottom_row else []

        self.build_matrix(self.matrix_a_frame, "A", values, hl, nrows, ncols, bottom)
        self.build_matrix(self.matrix_b_frame, "B", values, hl, nrows, ncols, bottom)

    def build_matrix(self, parent, name, values, highlight, nrows, ncols, bottom_row):
        for w in parent.winfo_children():
            w.destroy()

        # Заголовки столбцов
        hdr = ttk.Frame(parent)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="", width=3).pack(side=tk.LEFT)
        for c in range(ncols):
            ttk.Label(hdr, text=str(c), width=8, anchor=tk.CENTER).pack(side=tk.LEFT)

        # Строки матрицы
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

        # Нижняя строка — коэффициенты последовательности (полином)
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

    # ── Кнопка-глиф в токапу ───────────────────────────────────────────────────

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

    # ── Обработка выбора действия ──────────────────────────────────────────────

    def on_action(self, event=None):
        selected = self.action_var.get()

        # Макрос yupankiN (N >= 1)?
        if selected in self.loaded_macros:
            self.play_macro(selected)
            return

        # Встроенное действие из yupanki0
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

        # Извлекаем номер макроса для кнопки
        m = re.match(r'yupanki(\d+)', macro_name)
        macro_num = int(m.group(1)) if m else 0

        self.action_count += 1
        glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
        btn_text = f"{glyph}{macro_num}"
        # Макрос-кнопка — другой оттенок
        self.add_tokapu_button(btn_text, bg_color="#C4A882")

        self.log(f"[{self.action_count}] {macro_name}")
        if desc:
            self.log(f"  {desc}")
        else:
            self.log("  (описание пусто — заполните action_desc в JSON)")

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
                # Макрос разворачивается в подпоследовательность
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

        # Разворачиваем макросы в подпоследовательностях в плоский список
        flat_actions = []
        for act in actions:
            if act.get("macro"):
                # Это ссылка на другой макрос — разворачиваем
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
            self.log("  action_desc: (пусто — заполните вручную в JSON)")

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
