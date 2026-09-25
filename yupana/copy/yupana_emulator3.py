"""
Эмулятор Юпаны — графический интерфейс для работы с матрицами Стирлинга.

Две матрицы: 6×6, 9×9, 9×18
Режимы заполнения: stirling, rassnos, diagonal, diff, normalized, fibonacci
Действия выбираются из выпадающего списка (без кнопки подтверждения)
Токапу — кнопки-глифы, накапливаются с переносом строк
"""

import tkinter as tk
from tkinter import ttk
import math

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

# ──────────────────────────────────────────────────────────────────────────────
# Приложение
# ──────────────────────────────────────────────────────────────────────────────

class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Эмулятор Юпаны")
        self.root.geometry("1100x750")
        
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
                                          width=40, state="readonly",
                                          values=ACTION_NAMES)
        self.action_combo.pack(side=tk.LEFT, padx=2)
        self.action_combo.bind("<<ComboboxSelected>>", self.on_action)
        
        ttk.Button(action_frame, text="Очистить токапу",
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
                for k in range(min(n, ncols)):
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
            return f"{val}·x^{k}"
        else:
            if abs(val - round(val)) < 1e-9:
                return f"{int(round(val))}·x^{k}"
            s = f"{val:.3g}"
            return f"{s}·x^{k}"
    
    def refresh(self):
        nrows, ncols = self.get_size()
        mode = self.mode_var.get()
        
        values, hl = self.get_matrix_values(mode, nrows, ncols)
        
        self.build_matrix(self.matrix_a_frame, "A", values, hl, nrows, ncols)
        
        # Матрица B — то же содержимое для начала
        self.build_matrix(self.matrix_b_frame, "B", values, hl, nrows, ncols)
    
    def build_matrix(self, parent, name, values, highlight, nrows, ncols):
        # Очистка
        for w in parent.winfo_children():
            w.destroy()
        
        # Заголовки столбцов
        hdr = ttk.Frame(parent)
        hdr.pack(fill=tk.X)
        ttk.Label(hdr, text="", width=3).pack(side=tk.LEFT)
        for c in range(ncols):
            ttk.Label(hdr, text=str(c), width=8, anchor=tk.CENTER).pack(side=tk.LEFT)
        
        # Строки
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
    
    def on_action(self, event=None):
        action_idx = ACTION_NAMES.index(self.action_var.get())
        self.action_count += 1
        
        glyph = GLYPHS[(self.action_count - 1) % len(GLYPHS)]
        btn_text = f"{self.action_count}{glyph}"
        
        # Вычисление позиции кнопки
        col = (self.action_count - 1) % self.max_cols
        row = (self.action_count - 1) // self.max_cols
        
        x = 10 + col * self.btn_spacing_x
        y = 5 + row * self.btn_spacing_y
        
        # Увеличение canvas при необходимости
        needed_height = y + self.btn_height + 10
        if needed_height > int(self.tokapu_canvas.cget("height")):
            self.tokapu_canvas.config(height=needed_height)
        
        btn = tk.Button(self.tokapu_canvas, text=btn_text, width=4, height=2,
                        font=("Arial", 9),
                        bg="#D4C5A0", activebackground="#E8D8B8",
                        relief=tk.RAISED, bd=2)
        self.tokapu_canvas.create_window(x, y, anchor=tk.NW, window=btn)
        self.tokapu_buttons.append(btn)
        
        # Протокол
        self.log(f"[{self.action_count}] {ACTION_NAMES[action_idx]}")
        
        # Подсветка в зависимости от действия
        nrows, ncols = self.get_size()
        if action_idx == 0:  # Разносная
            self.mode_var.set("rassnos")
        elif action_idx == 1:  # Стирлинг
            self.mode_var.set("stirling")
        elif action_idx == 2:  # Дифф
            self.mode_var.set("diff")
        elif action_idx == 3:  # Диагональ A391838
            self.mode_var.set("diagonal")
        elif action_idx == 4:  # Фибоначчи
            self.mode_var.set("fibonacci")
        elif action_idx == 5:  # Нормировка
            self.mode_var.set("normalized")
        elif action_idx == 6:  # Обращение
            self.mode_var.set("stirling")
            self.log("  (Обращение ряда — заглушка, нужна реализация)")
        elif action_idx == 7:  # Сброс
            self.mode_var.set("stirling")
        
        self.refresh()
    
    def clear_tokapu(self):
        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons = []
        self.action_count = 0
        self.tokapu_canvas.config(height=60)
        self.log("--- Очистка токапу ---")
    
    def log(self, msg):
        self.protocol_text.config(state=tk.NORMAL)
        self.protocol_text.insert(tk.END, msg + "\n")
        self.protocol_text.see(tk.END)
        self.protocol_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaApp(root)
    root.mainloop()
