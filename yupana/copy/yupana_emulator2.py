"""
Эмулятор Юпаны — визуализация матриц Стирлинга, разносной схемы и диагоналей.

Две матрицы (A и B), выбор размера: 6×6, 9×9, 9×18.
В ячейках — части полинома a_n·x^n.
Действия добавляют кнопки-токапу, которые переносятся на новые строки.
"""

import tkinter as tk
from tkinter import ttk
import math


# ──────────────────────────────────────────────────────────────────────
# Вычислительные функции
# ──────────────────────────────────────────────────────────────────────

def stirling_first_kind(N):
    s = [[0] * (N + 1) for _ in range(N + 1)]
    s[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            s[n][k] = s[n - 1][k - 1] + (n - 1) * s[n - 1][k]
    return s


def binomial(N):
    c = [[0] * (N + 1) for _ in range(N + 1)]
    c[0][0] = 1
    for n in range(1, N + 1):
        c[n][0] = 1
        for k in range(1, n + 1):
            c[n][k] = c[n - 1][k - 1] + c[n - 1][k]
    return c


def fibonacci(N):
    f = [[0] * (N + 1) for _ in range(N + 1)]
    for n in range(N + 1):
        f[n][n] = 1
        if n >= 2:
            f[n][n - 1] = n - 1
    for n in range(2, N + 1):
        for k in range(n - 1):
            f[n][k] = f[n - 1][k] + f[n - 2][k]
    return f


def compute_matrix(rows, cols, mode):
    if mode == "stirling":
        raw = stirling_first_kind(max(rows, cols))
    elif mode in ("rassnos", "normalized"):
        raw = binomial(max(rows, cols))
    elif mode == "fibonacci":
        raw = fibonacci(max(rows, cols))
    elif mode == "diff":
        raw = stirling_first_kind(max(rows, cols))
    elif mode == "diagonal":
        raw = stirling_first_kind(max(rows, cols))
    else:
        raw = binomial(max(rows, cols))

    mat = []
    for i in range(rows):
        row = []
        for j in range(cols):
            if mode == "diagonal":
                # Косая диагональ: s(n-k, n-2k) — берём элементы
                # по «лесенке»: строка i-j, столбец i-2j
                r = i - j
                c = i - 2 * j
                if r < 0 or c < 0 or r >= len(raw) or c >= len(raw[0]):
                    val = 0
                else:
                    val = raw[r][c]
            elif mode == "diff":
                # Дифференцирование: делим на номер строки
                if i == 0:
                    val = raw[i][j] if j < len(raw[i]) else 0
                else:
                    val = (raw[i][j] / i) if j < len(raw[i]) else 0
            elif mode == "normalized":
                # Нормировка a_n/n!
                if j < len(raw[i]):
                    val = raw[i][j] / math.factorial(i) if math.factorial(i) != 0 else 0
                else:
                    val = 0
            else:
                val = raw[i][j] if j < len(raw[i]) else 0
            row.append(val)
        mat.append(row)
    return mat


def get_diagonal_cells(rows, cols):
    """Возвращает множество (i,j) для косой диагонали A391838."""
    cells = set()
    for n in range(rows):
        for k in range(n // 2 + 1):
            r = n - k
            c = n - 2 * k
            if 0 <= r < rows and 0 <= c < cols:
                cells.add((r, c))
    return cells


def get_fibonacci_cells(rows, cols):
    """Возвращает множество (i,j) для прямой диагонали s(n,n-k)."""
    cells = set()
    for n in range(rows):
        for k in range(min(n + 1, cols)):
            cells.add((n, n - k))
    return cells


# ──────────────────────────────────────────────────────────────────────
# Главное окно
# ──────────────────────────────────────────────────────────────────────

class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Эмулятор Юпаны")
        self.root.geometry("1200x800")

        self.size_var = tk.StringVar(value="9x9")
        self.mode_a_var = tk.StringVar(value="stirling")
        self.mode_b_var = tk.StringVar(value="rassnos")
        self.action_var = tk.StringVar(value="Действие 1")
        self.current_action_num = 1
        self.tokapu_buttons = []  # список кнопок-токапу

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        # Верхняя панель управления
        top = ttk.Frame(self.root, padding=6)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Размер:").pack(side=tk.LEFT)
        ttk.Combobox(top, textvariable=self.size_var, values=["6x6", "9x9", "9x18"],
                     width=6, state="readonly").pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(top, text="Матрица A:").pack(side=tk.LEFT)
        ttk.Combobox(top, textvariable=self.mode_a_var,
                     values=["stirling", "rassnos", "diagonal", "diff", "normalized", "fibonacci"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=(4, 16))

        ttk.Label(top, text="Матрица B:").pack(side=tk.LEFT)
        ttk.Combobox(top, textvariable=self.mode_b_var,
                     values=["stirling", "rassnos", "diagonal", "diff", "normalized", "fibonacci"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=(4, 16))

        ttk.Button(top, text="Обновить", command=self._refresh).pack(side=tk.LEFT, padx=(4, 16))

        # Связывание изменений
        self.size_var.trace_add("write", lambda *_: self._refresh())
        self.mode_a_var.trace_add("write", lambda *_: self._refresh())
        self.mode_b_var.trace_add("write", lambda *_: self._refresh())

        # Центральная область: две матрицы
        mid = ttk.Frame(self.root, padding=6)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.mat_frame_a = ttk.LabelFrame(mid, text="Матрица A", padding=4)
        self.mat_frame_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.mat_frame_b = ttk.LabelFrame(mid, text="Матрица B", padding=4)
        self.mat_frame_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.cell_labels_a = []
        self.cell_labels_b = []

        # Нижняя панель: действия
        bottom = ttk.Frame(self.root, padding=6)
        bottom.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(bottom, text="Действие:").pack(side=tk.LEFT)
        self.action_combo = ttk.Combobox(bottom, textvariable=self.action_var,
                                         values=[f"Действие {i}" for i in range(1, 9)],
                                         width=12, state="readonly")
        self.action_combo.pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(bottom, text="Выполнить", command=self._execute_action).pack(side=tk.LEFT, padx=(4, 16))

        ttk.Button(bottom, text="Очистить токапу", command=self._clear_tokapu).pack(side=tk.LEFT, padx=(16, 0))

        # Строка с выполненными действиями
        self.action_log_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.action_log_var, foreground="gray").pack(side=tk.LEFT, padx=(16, 0))

        # Область токапу — скроллируемая
        self.tokapu_outer = ttk.Frame(self.root, padding=6)
        self.tokapu_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

        ttk.Label(self.tokapu_outer, text="Токапу (последовательность действий):").pack(anchor=tk.W)

        # Canvas + scrollbar для токапу
        self.tokapu_canvas = tk.Canvas(self.tokapu_outer, height=50, bg="#f0f0f0")
        self.tokapu_scroll = ttk.Scrollbar(self.tokapu_outer, orient=tk.HORIZONTAL,
                                           command=self.tokapu_canvas.xview)
        self.tokapu_canvas.configure(xscrollcommand=self.tokapu_scroll.set)
        self.tokapu_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tokapu_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tokapu_inner = ttk.Frame(self.tokapu_canvas)
        self.tokapu_window = self.tokapu_canvas.create_window((0, 0), window=self.tokapu_inner, anchor=tk.NW)

        self.tokapu_inner.bind("<Configure>", self._on_tokapu_configure)
        self.tokapu_canvas.bind("<Configure>", self._on_tokapu_configure)

        # Текущая строка токапу
        self.current_row_frame = None
        self.buttons_in_current_row = 0
        self.max_buttons_per_row = 20  # динамически пересчитывается
        self.tokapu_rows = []  # список фреймов-строк

    def _on_tokapu_configure(self, event=None):
        self.tokapu_canvas.configure(scrollregion=self.tokapu_canvas.bbox("all"))
        if event and event.widget == self.tokapu_canvas:
            canvas_width = event.width
            btn_width = 42  # примерная ширина кнопки
            self.max_buttons_per_row = max(1, canvas_width // btn_width)

    def _refresh(self):
        size_map = {"6x6": (6, 6), "9x9": (9, 9), "9x18": (9, 18)}
        rows, cols = size_map.get(self.size_var.get(), (9, 9))

        self._draw_matrix(self.mat_frame_a, self.cell_labels_a, rows, cols, self.mode_a_var.get(), "A")
        self._draw_matrix(self.mat_frame_b, self.cell_labels_b, rows, cols, self.mode_b_var.get(), "B")

    def _draw_matrix(self, frame, labels_list, rows, cols, mode, matrix_name):
        for w in frame.winfo_children():
            w.destroy()
        labels_list.clear()

        diag_cells = get_diagonal_cells(rows, cols) if mode == "diagonal" else set()
        fib_cells = get_fibonacci_cells(rows, cols) if mode == "fibonacci" else set()
        highlight = diag_cells | fib_cells
        is_diag = mode == "diagonal"
        is_fib = mode == "fibonacci"

        mat = compute_matrix(rows, cols, mode)

        for i in range(rows):
            row_labels = []
            for j in range(cols):
                val = mat[i][j]
                # Формат: a_n·x^n  (или 0)
                if val == 0:
                    text = "0"
                elif isinstance(val, float) and val != int(val):
                    text = f"{val:.2f}·x^{j}"
                else:
                    text = f"{int(val)}·x^{j}"

                bg = "white"
                fg = "black"
                if (i, j) in highlight:
                    if is_diag:
                        bg = "#ffe0b2"  # оранжевый — косая диагональ
                    elif is_fib:
                        bg = "#c8e6c9"  # зелёный — прямая диагональ

                lbl = tk.Label(frame, text=text, width=10, height=2,
                               relief=tk.RIDGE, bg=bg, fg=fg, font=("Consolas", 9))
                lbl.grid(row=i, column=j, padx=1, pady=1)
                row_labels.append(lbl)
            labels_list.append(row_labels)

    def _execute_action(self):
        action_text = self.action_var.get()
        glyph = self._action_glyph(self.current_action_num)
        btn_num = self.current_action_num

        # Создаём кнопку-токапу
        btn = tk.Button(self.tokapu_inner, text=f"{btn_num}\n{glyph}",
                        width=4, height=2, font=("Consolas", 8),
                        relief=tk.RAISED, bg="#fff8e1",
                        command=lambda n=btn_num: self._on_tokapu_click(n))
        self.tokapu_buttons.append(btn)

        # Размещаем на текущей строке
        self._place_tokapu_button(btn)

        # Обновляем лог
        log = self.action_log_var.get()
        if log:
            self.action_log_var.set(log + f" → {action_text}({btn_num})")
        else:
            self.action_log_var.set(f"{action_text}({btn_num})")

        self.current_action_num += 1
        # Переход к следующему действию в списке
        idx = min(self.current_action_num - 1, 7)
        self.action_var.set(f"Действие {idx + 1}")

    def _place_tokapu_button(self, btn):
        # Пересчитываем max_buttons_per_row по текущей ширине canvas
        canvas_width = self.tokapu_canvas.winfo_width()
        if canvas_width > 1:
            btn_width = 42
            self.max_buttons_per_row = max(1, canvas_width // btn_width)
        else:
            self.max_buttons_per_row = 20

        # Если строк нет или текущая заполнена — создаём новую строку
        if self.current_row_frame is None or self.buttons_in_current_row >= self.max_buttons_per_row:
            self.current_row_frame = ttk.Frame(self.tokapu_inner)
            self.current_row_frame.pack(side=tk.TOP, fill=tk.X, pady=1)
            self.tokapu_rows.append(self.current_row_frame)
            self.buttons_in_current_row = 0

            # Увеличиваем высоту canvas
            current_height = self.tokapu_canvas.winfo_height()
            self.tokapu_canvas.configure(height=current_height + 50)

        btn.pack(in_=self.current_row_frame, side=tk.LEFT, padx=2, pady=1)
        self.buttons_in_current_row += 1

        self._on_tokapu_configure()

    def _on_tokapu_click(self, num):
        print(f"Токапу {num} нажат")

    def _clear_tokapu(self):
        for btn in self.tokapu_buttons:
            btn.destroy()
        self.tokapu_buttons.clear()
        for row_frame in self.tokapu_rows:
            row_frame.destroy()
        self.tokapu_rows.clear()
        self.current_row_frame = None
        self.buttons_in_current_row = 0
        self.tokapu_canvas.configure(height=50)
        self.current_action_num = 1
        self.action_log_var.set("")
        self._on_tokapu_configure()

    def _action_glyph(self, num):
        # Простые геометрические глифы-токапу
        glyphs = ["●", "◆", "▲", "■", "★", "◐", "◑", "◒"]
        return glyphs[(num - 1) % len(glyphs)]


if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaApp(root)
    root.mainloop()
