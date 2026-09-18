"""
Эмулятор Юпаны — графический интерфейс для работы с матрицами Стирлинга.

Две матрицы: 6×6, 9×9, 9×18
Режимы заполнения: stirling, rassnos, diagonal, diff, normalized, fibonacci
Действия выбираются из выпадающего списка (без кнопки подтверждения)
Токапу — кнопки-глифы, накапливаются с переносом строк
Макросы yupanki: сохранение/загрузка последовательностей действий (Forth-стиль)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import math
import json
import os
import re

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

# Предварительно вычисляем для максимального размера 18
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

ACTION_NAMES = [
    "Действие 1: Разносная схема",
    "Действие 2: Переход к Стирлингу (×строка)",
    "Действие 3: Дифференцирование (÷строка)",
    "Действие 4: Диагональ n-k, n-2k (A391838)",
    "Действие 5: Прямая диагональ n, n-k (Фибоначчи)",
    "Действие 6: Нормировка a_n/n!",
    "Действие 7: Обращение ряда",
    "Действие 8: Сброс матрицы",
]

YUPANKI_DIR = "yupanki"

# ──────────────────────────────────────────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────────────────────────────────────────

class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Эмулятор Юпаны")
        self.root.geometry("1100x780")

        self.size_var = tk.StringVar(value="9x9")
        self.mode_var = tk.StringVar(value="stirling")
        self.action_var = tk.StringVar(value=ACTION_NAMES[0])

        self.action_count = 0
        self.tokapu_buttons = []
        self.tokapu_row = 0
        self.tokapu_col = 0
        self.btn_width = 50
        self.btn_height = 45
        self.btn_spacing_x = 58
        self.btn_spacing_y = 55
        self.max_cols = 16

        # История действий текущей сессии (для записи в yupanki JSON)
        self.action_history = []

        # Загруженные макросы: { "yupanki1": {"path": ..., "actions": [...], "desc": ...}, ... }
        self.loaded_macros = {}

        # Текущие значения выпадающего списка действий (ACTION_NAMES + макросы)
        self.current_action_values = list(ACTION_NAMES)

        self.build_ui()
        self.refresh()

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

        self.matrix_a = None
        self.matrix_b = None
        self.highlight_a = set()
        self.highlight_b = set()

        # ── Панель действий ─────────────────────────────────────────────────
        action_frame = ttk.Frame(self.root, padding=5)
        action_frame.pack(fill=tk.X)

        ttk.Label(action_frame, text="Действие:").pack(side=tk.LEFT, padx=(0, 5))
        self.action_combo = ttk.Combobox(action_frame, textvariable=self.action_var,
                                          width=45, state="readonly",
                                          values=self.current_action_values)
        self.action_combo.pack(side=tk.LEFT, padx=2)
        self.action_combo.bind("<<ComboboxSelected>>", self.on_action)

        # Кнопка Загрузить
        ttk.Button(action_frame, text="Загрузить",
                   command=self.load_yupanki).pack(side=tk.RIGHT, padx=5)

        # Кнопка Очистить токапу (теперь сохраняет yupanki перед очисткой)
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
        self.protocol_text = tk.Text(proto_frame, height=4, state=tk.DISABLED,
                                     bg="#FAFAF0", wrap=tk.WORD)
        self.protocol_text.pack(fill=tk.X)

    # ── Yupanki: сохранение ──────────────────────────────────────────────────

    def get_next_yupanki_number(self):
        """Находит максимальный номер среди существующих yupankiN.json + 1."""
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
        """Сохраняет историю действий в yupanki/yupankiN.json."""
        if not self.action_history:
            self.log("Нет действий для сохранения в yupanki")
            return None

        os.makedirs(YUPANKI_DIR, exist_ok=True)
        num = self.get_next_yupanki_number()
        filename = f"yupanki{num}.json"
        filepath = os.path.join(YUPANKI_DIR, filename)

        data = {
            "name": f"yupanki{num}",
            "actions": [
                {"index": a["index"], "name": a["name"]}
                for a in self.action_history
            ],
            "ACTION_DESC": ""
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.log(f"Сохранено: {filepath} ({len(self.action_history)} действий)")
        return filename

    # ── Yupanki: загрузка ─────────────────────────────────────────────────────

    def load_yupanki(self):
        """Открывает диалог выбора JSON из каталога yupanki."""
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
        actions = data.get("actions", [])
        desc = data.get("ACTION_DESC", "")

        self.loaded_macros[macro_name] = {
            "path": filepath,
            "actions": actions,
            "desc": desc
        }

        # Добавляем макрос в выпадающий список
        if macro_name not in self.current_action_values:
            self.current_action_values.append(macro_name)
            self.action_combo["values"] = self.current_action_values

        # Подсветка ACTION_DESC в протоколе
        self.log(f"Загружен макрос: {macro_name}")
        if desc:
            self.log(f"  Описание: {desc}")
        else:
            self.log("  Описание: (пусто — заполните ACTION_DESC в JSON вручную)")

    # ── Yupanki: проигрывание макроса ─────────────────────────────────────────

    def play_macro(self, macro_name):
        """Проигрывает последовательность действий из загруженного макроса."""
        macro = self.loaded_macros.get(macro_name)
        if not macro:
            self.log(f"Макрос {macro_name} не найден")
            return

        self.log(f"▶ Макрос {macro_name}: начало ({len(macro['actions'])} действий)")
        for act in macro["actions"]:
            idx = act["index"]
            name = act["name"]
            self.execute_action_by_index(idx, name, record_history=True)
        self.log(f"■ Макрос {macro_name}: конец")

    # ── Матрицы ──────────────────────────────────────────────────────────────

    def get_size(self):
        s = self.size_var.get()
        if s == "6x6": return 6, 6
        if s == "9x9": return 9, 9
        if s == "18x9": return 18, 9
        return 9, 9

    def get_matrix_values(self, mode, nrows, ncols):
        """Возвращает матрицу значений и множество ячеек для подсветки."""
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

    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()

        values, hl = self.get_matrix_values(mode, nrows, ncols)

        self.build_matrix(self.matrix_a_frame, "A", values, hl, nrows, ncols)
        self.build_matrix(self.matrix_b_frame, "B", values, hl, nrows, ncols)

    def build_matrix(self, parent, name, values, highlight, nrows, ncols):
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

    # ── Действия ──────────────────────────────────────────────────────────────

    def on_action(self, event=None):
        selected = self.action_var.get()

        # Проверка: выбран ли макрос yupanki
        if selected in self.loaded_macros:
            self.action_count += 1
            glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
            btn_text = f"y{self.action_count}{glyph}"
            self.add_tokapu_button(btn_text)
            self.log(f"[{self.action_count}] {selected}")
            self.play_macro(selected)
            return

        # Обычное действие
        action_idx = ACTION_NAMES.index(selected)
        self.execute_action_by_index(action_idx, selected, record_history=True)

    def execute_action_by_index(self, idx, name, record_history=True):
        """Выполняет действие по индексу и добавляет кнопку-глиф."""
        self.action_count += 1

        glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
        btn_text = f"{self.action_count}{glyph}"

        self.add_tokapu_button(btn_text)

        if record_history:
            self.action_history.append({"index": idx, "name": name})

        self.log(f"[{self.action_count}] {name}")

        # Смена режима в зависимости от действия
        if idx == 0:    # Разносная
            self.mode_var.set("rassnos")
        elif idx == 1:  # Стирлинг
            self.mode_var.set("stirling")
        elif idx == 2:  # Дифф
            self.mode_var.set("diff")
        elif idx == 3:  # Диагональ A391838
            self.mode_var.set("diagonal")
        elif idx == 4:  # Фибоначчи
            self.mode_var.set("fibonacci")
        elif idx == 5:  # Нормировка
            self.mode_var.set("normalized")
        elif idx == 6:  # Обращение
            self.mode_var.set("stirling")
            self.log("  (Обращение ряда — заглушка, нужна реализация)")
        elif idx == 7:  # Сброс
            self.mode_var.set("stirling")

        self.refresh()

    def add_tokapu_button(self, btn_text):
        """Добавляет кнопку-глиф в токапу с переносом строк."""
        col = (self.action_count - 1) % self.max_cols
        row = (self.action_count - 1) // self.max_cols

        x = 10 + col * self.btn_spacing_x
        y = 5 + row * self.btn_spacing_y

        needed_height = y + self.btn_height + 10
        if needed_height > int(self.tokapu_canvas.cget("height")):
            self.tokapu_canvas.config(height=needed_height)

        btn = tk.Button(self.tokapu_canvas, text=btn_text, width=4, height=2,
                        font=("Arial", 9),
                        bg="#D4C5A0", activebackground="#E8D8B8",
                        relief=tk.RAISED, bd=2)
        self.tokapu_canvas.create_window(x, y, anchor=tk.NW, window=btn)
        self.tokapu_buttons.append(btn)

    # ── Очистка ───────────────────────────────────────────────────────────────

    def clear_tokapu(self):
        """Сохраняет yupanki, затем очищает токапу."""
        # Сохраняем текущую сессию в JSON
        saved = self.save_yupanki()

        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons = []
        self.action_count = 0
        self.action_history = []
        self.tokapu_canvas.config(height=60)
        self.log("--- Очистка токапу ---")

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
