"""
Эмулятор Юпаны — графический интерфейс
======================================
Две матрицы (6×6, 9×9, 9×18) с ячейками вида a_n·x^n.
Действия: заполнение Стирлингом, разносная схема, диагонали, дифференцирование.
Токапу: кнопки действий накапливаются в нижней строке.

Запуск: py yupana_emulator.py
"""

import tkinter as tk
from tkinter import ttk
import math


# ── Беззнаковые числа Стирлинга I рода ──
def stirling_first_kind(N):
    s = [[0] * (N + 1) for _ in range(N + 1)]
    s[0][0] = 1
    for n in range(1, N + 1):
        for k in range(1, n + 1):
            s[n][k] = s[n - 1][k - 1] + (n - 1) * s[n - 1][k]
    return s


# ── Нормированные коэффициенты a_n/n! (A391838) ──
def a391838_norm(n_max):
    s = stirling_first_kind(n_max + 1)
    result = []
    for n in range(n_max + 1):
        total = 0.0
        for k in range(n // 2 + 1):
            row, col = n - k, n - 2 * k
            if col < 0 or row < 0:
                break
            sv = s[row][col]
            if sv == 0:
                continue
            total += sv / (math.factorial(2 * k + 1) * math.factorial(n - k))
        a_n = math.factorial(n) ** 2 * total
        result.append(a_n / math.factorial(n))
    return result


A39 = a391838_norm(17)  # с запасом до 18 столбцов

# ── Токапу: глифы ──
TOCAPU_GLYPHS = [
    "\u25A1", "\u25A0", "\u25A3", "\u25A4", "\u25A5", "\u25A6", "\u25A7",
    "\u25A8", "\u25A9", "\u25C6", "\u25C8", "\u25C9", "\u25CA", "\u25CB",
    "\u25CF", "\u25D0", "\u25D1", "\u25D2", "\u25D3", "\u25D4", "\u25D5",
    "\u25D6", "\u25D7", "\u25EF", "\u2588", "\u2593", "\u2592", "\u2591",
]

# ── Действия ──
ACTIONS = [
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 1 \u2014 \u0417\u0430\u043F\u043E\u043B\u043D\u0438\u0442\u044C \u0421\u0442\u0438\u0440\u043B\u0438\u043D\u0433",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 2 \u2014 \u0420\u0430\u0437\u043D\u043E\u0441\u043D\u0430\u044F \u0441\u0445\u0435\u043C\u0430",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 3 \u2014 \u0414\u0438\u0430\u0433\u043E\u043D\u0430\u043B\u044C n-k, n-2k",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 4 \u2014 \u0414\u0438\u0444\u0444\u0435\u0440\u0435\u043D\u0446\u0438\u0440\u043E\u0432\u0430\u043D\u0438\u0435",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 5 \u2014 \u041D\u043E\u0440\u043C\u0438\u0440\u043E\u0432\u043A\u0430 a_n/n!",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 6 \u2014 \u041E\u0431\u0440\u0430\u0449\u0435\u043D\u0438\u0435 \u0440\u044F\u0434\u0430",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 7 \u2014 \u041A\u043E\u0441\u0430\u044F \u0434\u0438\u0430\u0433\u043E\u043D\u0430\u043B\u044C (\u0414\u0435\u043B\u043E\u043D\u0435)",
    "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435 8 \u2014 \u0410\u043D\u0430\u043B\u043E\u0433 \u0424\u0438\u0431\u043E\u043D\u0430\u0447\u0447\u0438",
]

ACTION_DESC = {
    0: "s(n,k) = s(n-1,k-1) + (n-1)\u00B7s(n-1,k)",
    1: "\u0411\u0435\u0437 \u0443\u043C\u043D\u043E\u0436\u0435\u043D\u0438\u044F \u043D\u0430 \u043D\u043E\u043C\u0435\u0440 \u0441\u0442\u0440\u043E\u043A\u0438 (\u0430\u043D\u0430\u043B\u043E\u0433 \u041F\u0430\u0441\u043A\u0430\u043B\u044F)",
    2: "\u0412\u044B\u0431\u043E\u0440\u043A\u0430 \u044F\u0447\u0435\u0435\u043A \u0434\u043B\u044F A391838",
    3: "\u041F\u0435\u0440\u0435\u0445\u043E\u0434 \u0432\u0432\u0435\u0440\u0445, \u0434\u0435\u043B\u0435\u043D\u0438\u0435 \u043D\u0430 \u043D\u043E\u043C\u0435\u0440 \u0441\u0442\u0440\u043E\u043A\u0438",
    4: "\u041A\u043E\u044D\u0444\u0444\u0438\u0446\u0438\u0435\u043D\u0442\u044B \u043F\u043E\u043B\u0438\u043D\u043E\u043C\u0430 A(e)",
    5: "\u041F\u043E\u0441\u0442\u0440\u043E\u0435\u043D\u0438\u0435 \u043E\u0431\u0440\u0430\u0442\u043D\u043E\u0439 \u0444\u0443\u043D\u043A\u0446\u0438\u0438",
    6: "\u0414\u0438\u0430\u0433\u043E\u043D\u0430\u043B\u044C \u0432 \u0441\u0442\u0438\u043B\u0435 \u0414\u0435\u043B\u043E\u043D\u0435",
    7: "\u041F\u0440\u044F\u043C\u0430\u044F \u0434\u0438\u0430\u0433\u043E\u043D\u0430\u043B\u044C s(n, n-k)",
}


class YupanaMatrix(ttk.LabelFrame):
    """Одна матрица юпаны."""

    def __init__(self, parent, name, max_rows=9, max_cols=18):
        super().__init__(parent, text=name)
        self.max_rows = max_rows
        self.max_cols = max_cols
        self.cur_rows = 6
        self.cur_cols = 6
        self.labels = {}
        self._build_grid()

    def _build_grid(self):
        inner = ttk.Frame(self)
        inner.pack(padx=4, pady=4)

        for r in range(self.max_rows):
            for c in range(self.max_cols):
                lbl = tk.Label(
                    inner, text="", width=11, anchor="center",
                    relief="solid", borderwidth=1,
                    font=("Consolas", 8), padx=1, pady=1,
                )
                lbl.grid(row=r, column=c, sticky="nsew")
                self.labels[(r, c)] = lbl

    def set_size(self, rows, cols):
        self.cur_rows = rows
        self.cur_cols = cols
        for (r, c), lbl in self.labels.items():
            if r < rows and c < cols:
                lbl.grid()
            else:
                lbl.grid_remove()

    def clear_highlights(self):
        for lbl in self.labels.values():
            lbl.config(bg="white", fg="black")

    def update_cells(self, mode="stirling"):
        s = stirling_first_kind(max(self.max_rows, self.max_cols) + 1)

        for (r, c), lbl in self.labels.items():
            if r >= self.cur_rows or c >= self.cur_cols:
                continue

            if mode == "stirling":
                val = s[r][c]
                text = f"{val}\u00B7x^{c}" if val != 0 else ""

            elif mode == "rassnos":
                # Разносная схема — биномиальные коэффициенты (без умножения на n)
                val = math.comb(r, c) if c <= r else 0
                text = f"{val}\u00B7x^{c}" if val != 0 else ""

            elif mode == "diagonal":
                # Диагональ n-k, n-2k
                k = c
                n = r
                row_d = n - k
                col_d = n - 2 * k
                if 0 <= col_d < self.max_cols and 0 <= row_d < self.max_rows:
                    val = s[row_d][col_d]
                    text = f"{val}\u00B7x^{k}" if val != 0 else ""
                else:
                    text = ""

            elif mode == "diff":
                # Дифференцирование: деление на номер строки, переход вверх
                if r > 0 and c > 0:
                    val = s[r][c]
                    if val % r == 0:
                        text = f"{val // r}\u00B7x^{c-1}"
                    elif val != 0:
                        text = f"{val}/{r}\u00B7x^{c-1}"
                    else:
                        text = ""
                else:
                    text = ""

            elif mode == "normalized":
                if r == 0 and c < len(A39):
                    text = f"{A39[c]:.4g}\u00B7x^{c}"
                else:
                    text = ""

            elif mode == "fibonacci":
                # Аналог Фибоначчи: прямая диагональ s(n, n-k)
                k = r - c
                if k >= 0:
                    val = s[r][c]
                    text = f"{val}\u00B7x^{k}" if val != 0 else ""
                else:
                    text = ""

            else:
                text = ""

            lbl.config(text=text, bg="white", fg="black")

    def highlight_diagonal(self, kind="straight"):
        self.clear_highlights()
        s = stirling_first_kind(max(self.max_rows, self.max_cols) + 1)

        if kind == "straight":
            for r in range(self.cur_rows):
                for k in range(r + 1):
                    c = r - k
                    if c < self.cur_cols and (r, c) in self.labels:
                        self.labels[(r, c)].config(bg="#c8e6c9")
        elif kind == "oblique":
            for n in range(self.cur_rows):
                for k in range(n // 2 + 1):
                    r = n - k
                    c = n - 2 * k
                    if (r < self.cur_rows and c < self.cur_cols
                            and (r, c) in self.labels):
                        self.labels[(r, c)].config(bg="#ffe0b2")


class YupanaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("\u042E\u043F\u0430\u043D\u0430 \u2014 \u042D\u043C\u0443\u043B\u044F\u0442\u043E\u0440")
        self.root.geometry("1400x850")

        self.current_mode = "stirling"
        self.tocapu_buttons = []

        self._build_ui()
        self._apply()

    def _build_ui(self):
        # ── Верх: выбор размера ──
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=4)

        ttk.Label(top, text="\u0420\u0430\u0437\u043C\u0435\u0440:").pack(side="left", padx=4)
        self.size_var = tk.StringVar(value="6\u00D76")
        ttk.Combobox(top, textvariable=self.size_var, width=8,
                     values=["6\u00D76", "9\u00D79", "9\u00D718"],
                     state="readonly").pack(side="left", padx=4)
        self.size_var.trace_add("write", lambda *_: self._apply())

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=8)

        ttk.Label(top, text="\u0420\u0435\u0436\u0438\u043C:").pack(side="left", padx=4)
        self.mode_var = tk.StringVar(value="stirling")
        ttk.Combobox(top, textvariable=self.mode_var, width=24,
                     values=["stirling", "rassnos", "diagonal",
                             "diff", "normalized", "fibonacci"],
                     state="readonly").pack(side="left", padx=4)
        self.mode_var.trace_add("write", lambda *_: self._apply())

        # ── Матрицы ──
        mid = ttk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=8, pady=4)

        self.mat_a = YupanaMatrix(mid, "\u041C\u0430\u0442\u0440\u0438\u0446\u0430 A")
        self.mat_a.pack(side="left", fill="both", expand=True, padx=(0, 4))

        self.mat_b = YupanaMatrix(mid, "\u041C\u0430\u0442\u0440\u0438\u0446\u0430 B")
        self.mat_b.pack(side="right", fill="both", expand=True, padx=(4, 0))

        # ── Действия ──
        act_frame = ttk.Frame(self.root)
        act_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(act_frame, text="\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0435:").pack(side="left", padx=4)
        self.action_var = tk.StringVar(value=ACTIONS[0])
        ttk.Combobox(act_frame, textvariable=self.action_var, width=48,
                     values=ACTIONS, state="readonly").pack(side="left", padx=4)
        self.action_var.trace_add("write", lambda *_: self._on_action())

        self.desc_label = ttk.Label(act_frame, text="", font=("Arial", 9, "italic"))
        self.desc_label.pack(side="left", padx=12)

        ttk.Button(act_frame, text="\u0412\u044B\u043F\u043E\u043B\u043D\u0438\u0442\u044C",
                   command=self._on_action).pack(side="right", padx=4)

        # ── Токапу ──
        toc_frame = ttk.LabelFrame(self.root, text="\u0422\u043E\u043A\u0430\u043F\u0443")
        toc_frame.pack(fill="x", padx=8, pady=4)

        self.tocapu_bar = ttk.Frame(toc_frame)
        self.tocapu_bar.pack(fill="x", pady=2)

        self.tocapu_string = tk.Label(toc_frame, text="", font=("Arial", 14),
                                      anchor="w")
        self.tocapu_string.pack(fill="x", pady=4)

        # ── Статус ──
        self.status = ttk.Label(self.root, text="\u0413\u043E\u0442\u043E\u0432\u043E")
        self.status.pack(fill="x", padx=8, pady=2)

    def _apply(self):
        size = self.size_var.get()
        if "6" in size:
            rows, cols = 6, 6
        elif "18" in size:
            rows, cols = 9, 18
        else:
            rows, cols = 9, 9

        mode = self.mode_var.get()
        self.mat_a.set_size(rows, cols)
        self.mat_b.set_size(rows, cols)
        self.mat_a.update_cells(mode)
        self.mat_b.update_cells(mode)
        self.status.config(text=f"\u0420\u0430\u0437\u043C\u0435\u0440: {rows}\u00D7{cols}  |  \u0420\u0435\u0436\u0438\u043C: {mode}")

    def _on_action(self):
        action = self.action_var.get()
        idx = ACTIONS.index(action)
        self.desc_label.config(text=ACTION_DESC.get(idx, ""))

        # Добавляем кнопку-токапу
        glyph = TOCAPU_GLYPHS[idx % len(TOCAPU_GLYPHS)]
        btn = ttk.Button(self.tocapu_bar, text=f"{idx + 1} {glyph}",
                         command=lambda i=idx: self._tocapu_click(i))
        btn.pack(side="left", padx=2)
        self.tocapu_buttons.append(btn)

        # Обновляем строку токапу
        current = self.tocapu_string.cget("text")
        self.tocapu_string.config(text=current + f" {idx + 1}{glyph}")

        # Выполняем действие
        mode_map = {
            0: "stirling",
            1: "rassnos",
            2: "diagonal",
            3: "diff",
            4: "normalized",
            5: "stirling",
            6: "diagonal",
            7: "fibonacci",
        }

        mode = mode_map.get(idx, "stirling")

        if idx in (2, 6):
            self.mat_a.highlight_diagonal("oblique")
            self.mat_b.highlight_diagonal("oblique")
        elif idx == 7:
            self.mat_a.highlight_diagonal("straight")
            self.mat_b.highlight_diagonal("straight")
        else:
            self.mat_a.update_cells(mode)
            self.mat_b.update_cells(mode)

        self.status.config(text=f"\u0412\u044B\u043F\u043E\u043B\u043D\u0435\u043D\u043E: {action}")

    def _tocapu_click(self, idx):
        self.action_var.set(ACTIONS[idx])
        self._on_action()


if __name__ == "__main__":
    root = tk.Tk()
    app = YupanaApp(root)
    root.mainloop()
