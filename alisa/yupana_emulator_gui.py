"""
yupana_emulator_gui.py
GUI часть эмулятора юпаны (часть 2 из 3).
Импортируется из yupana_emulator.py.
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

    from yupana_arrays import (
        ACTIONS, PHASANT_COLORS, COLOR_MAP, THEMES
    )
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_arrays: {e}")
    ACTIONS = None

try:
    from execute_action import execute_action
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать execute_action: {e}")
    execute_action = None

try:
    from yupana_model import YupanaModel
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать YupanaModel из yupana_model.py: {e}")
    YupanaModel = None


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
        self.stirling_n = tk.StringVar(value="5")


        self.animation_speed = tk.IntVar(value=1500)
        self.current_history = []
        self.current_step_idx = 0
        self.is_playing = False
        self.play_after_id = None

        self.current_theme = "light"
        self.theme_var = tk.BooleanVar(value=False)


        self._build_ui()

    def _build_ui(self):
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)

        self.action_combo_label = ttk.Label(top_frame, text="Действие:")
        self.action_combo_label.pack(side=tk.LEFT, padx=(0, 5))

        self.action_combo = ttk.Combobox(
            top_frame, textvariable=self.current_action,
            values=list(ACTIONS.keys()), width=5, state="readonly"
        )
        self.action_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.action_combo.bind("<<ComboboxSelected>>", self._on_action_change)

        self.action_label = ttk.Label(top_frame, text=ACTIONS[0]["name"])
        self.action_label.pack(side=tk.LEFT, padx=(0, 10))

        # Радиокнопки для тёмной темы — только анимированные действия
        self.radio_frame = tk.Frame(top_frame, bg=THEMES["violet"]["panel_bg"])
        self.radio_buttons = []
        radio_actions = [
            (1,  "1:Stirling"),
            (10, "10:Инки"),
            (11, "11:Диаг"),
            (12, "12:A391838"),
            (13, "13:Подъём"),
            (14, "14:Опуск"),
            (15, "15:Вправо"),
            (16, "16:Влево"),
            (17, "16:Факториал"),
        ]
        for val, text in radio_actions:
            rb = tk.Radiobutton(
                self.radio_frame, text=text,
                variable=self.current_action, value=val,
                bg=THEMES["violet"]["panel_bg"],
                fg=THEMES["violet"]["cell_fg"],
                selectcolor=THEMES["violet"]["cell_bg"],
                font=("Consolas", 9),
                command=self._on_action_change,
                relief=tk.FLAT, bd=0, padx=3
            )
            rb.pack(side=tk.LEFT, padx=2)
            self.radio_buttons.append(rb)


        self.run_button = tk.Button(
            top_frame, text="Выполнить", command=self._execute,
            font=("Consolas", 11, "bold"), padx=14,
            relief=tk.FLAT, bd=0, cursor="hand2"
        )
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = tk.Button(
            top_frame, text="Сброс", command=self._reset,
            font=("Consolas", 11, "bold"), padx=10,
            relief=tk.FLAT, bd=0, cursor="hand2"
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.spice_button = tk.Button(
            top_frame, text="SPICE", command=self._export_spice,
            font=("Consolas", 10, "bold"), padx=8,
            relief=tk.FLAT, bd=0, cursor="hand2"
        )
        self.spice_button.pack(side=tk.RIGHT, padx=2)

        self.json_button = tk.Button(
            top_frame, text="JSON", command=self._export_json,
            font=("Consolas", 10, "bold"), padx=8,
            relief=tk.FLAT, bd=0, cursor="hand2"
        )
        self.json_button.pack(side=tk.RIGHT, padx=2)

        self.csv_button = tk.Button(
            top_frame, text="CSV", command=self._export_csv,
            font=("Consolas", 10, "bold"), padx=8,
            relief=tk.FLAT, bd=0, cursor="hand2"
        )
        self.csv_button.pack(side=tk.RIGHT, padx=2)

        ttk.Checkbutton(
            top_frame, text="Тёмная тема",
            variable=self.theme_var,
            command=self._toggle_theme
        ).pack(side=tk.LEFT, padx=10)


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

        # Навигация для тёмной темы
        self.nav_frame = tk.Frame(self.root, bg=THEMES["violet"]["panel_bg"])

        self.nav_prev = tk.Button(
            self.nav_frame, text="<<", command=self._nav_prev,
            bg=THEMES["violet"]["cell_bg"], fg=THEMES["violet"]["cell_fg"],
            font=("Consolas", 12, "bold"), relief=tk.FLAT, bd=0,
            padx=12, cursor="hand2"
        )
        self.nav_prev.pack(side=tk.LEFT, padx=4)

        self.nav_next = tk.Button(
            self.nav_frame, text=">>", command=self._nav_next,
            bg=THEMES["violet"]["cell_bg"], fg=THEMES["violet"]["cell_fg"],
            font=("Consolas", 12, "bold"), relief=tk.FLAT, bd=0,
            padx=12, cursor="hand2"
        )
        self.nav_next.pack(side=tk.LEFT, padx=4)

        self.nav_play = tk.Button(
            self.nav_frame, text="Play", command=self._nav_play,
            bg=THEMES["violet"]["highlight_bg"], fg="white",
            font=("Consolas", 12, "bold"), relief=tk.FLAT, bd=0,
            padx=16, cursor="hand2"
        )
        self.nav_play.pack(side=tk.LEFT, padx=8)

        self.nav_step_label = tk.Label(
            self.nav_frame, text="",
            bg=THEMES["violet"]["panel_bg"],
            fg=THEMES["violet"]["cell_fg"],
            font=("Consolas", 12)
        )
        self.nav_step_label.pack(side=tk.LEFT, padx=12)



        self.info_text = tk.Text(self.root, height=10, state=tk.DISABLED, font=("Consolas", 10))
        self.info_text.pack(fill=tk.X, padx=10, pady=5)

    def _build_table(self, parent, model):
        cells = []
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        for i in range(model.rows):
            row_cells = []
            for j in range(model.cols):
                cell_frame = tk.Frame(
                    frame, relief=tk.RAISED, borderwidth=2,
                    width=65, height=55, bg="#F0E68C"
                )
                cell_frame.grid(row=i, column=j, padx=1, pady=1)
                cell_frame.pack_propagate(False)

                label = tk.Label(
                    cell_frame, text="0",
                    font=("Arial", 10, "bold"), bg="#F0E68C"
                )
                label.pack(expand=True)
                row_cells.append((cell_frame, label))
            cells.append(row_cells)

        bottom_frame = ttk.Frame(frame)
        bottom_frame.grid(row=model.rows, column=0, columnspan=model.cols, pady=5)
        bottom_cells = []
        for j in range(model.cols):
            blabel = ttk.Label(
                bottom_frame, text="0",
                font=("Arial", 10, "bold"), foreground="blue"
            )
            blabel.grid(row=0, column=j, padx=10)
            bottom_cells.append(blabel)
        cells.append(bottom_cells)

        return cells

    def _build_params(self, action_id):
        for widget in self.param_frame.winfo_children():
            widget.destroy()

        t = THEMES[self.current_theme]

        if action_id in (8, 10, 11, 12, 13, 14, 15, 16, 17):
            label_text = "Параметр n:" if action_id in (11, 12, 13, 14, 15, 16, 17) else "Число A:"
            ttk.Label(self.param_frame, text=label_text).grid(row=0, column=0, padx=5)
            tk.Entry(
                self.param_frame, textvariable=self.lattice_a, width=10,
                bg=t["entry_bg"], fg=t["entry_fg"],
                insertbackground=t["entry_fg"],
                font=("Consolas", 11), relief=tk.FLAT, bd=2
            ).grid(row=0, column=1, padx=5)

            if action_id in (8, 10):
                ttk.Label(self.param_frame, text="Число B:").grid(row=0, column=2, padx=5)
                tk.Entry(
                    self.param_frame, textvariable=self.lattice_b, width=10,
                    bg=t["entry_bg"], fg=t["entry_fg"],
                    insertbackground=t["entry_fg"],
                    font=("Consolas", 11), relief=tk.FLAT, bd=2
                ).grid(row=0, column=3, padx=5)

            if action_id in (10, 11, 12, 13, 14, 15, 16, 17) and self.current_theme == "light":
                col_offset = 2 if action_id in (11, 12, 13, 14, 15, 16, 17) else 4
                ttk.Label(self.param_frame, text="Задержка (мс):").grid(row=0, column=col_offset, padx=(20, 5))
                speed_scale = ttk.Scale(
                    self.param_frame, from_=100, to=3000,
                    variable=self.animation_speed,
                    orient=tk.HORIZONTAL, length=150
                )
                speed_scale.grid(row=0, column=col_offset + 1, padx=5)
                speed_label = ttk.Label(self.param_frame, text=str(self.animation_speed.get()) + " мс")
                speed_label.grid(row=0, column=col_offset + 2, padx=5)
                speed_scale.config(command=lambda val: speed_label.config(text=str(int(float(val))) + " мс"))

        elif action_id == 1:
            ttk.Label(self.param_frame, text="N (строки таблицы):").grid(row=0, column=0, padx=5)
            tk.Entry(
                self.param_frame, textvariable=self.stirling_n, width=5,
                bg=t["entry_bg"], fg=t["entry_fg"],
                insertbackground=t["entry_fg"],
                font=("Consolas", 11), relief=tk.FLAT, bd=2
            ).grid(row=0, column=1, padx=5)

            if self.current_theme == "light":
                ttk.Label(self.param_frame, text="Задержка (мс):").grid(row=0, column=2, padx=(20, 5))
                speed_scale = ttk.Scale(
                    self.param_frame, from_=100, to=3000,
                    variable=self.animation_speed,
                    orient=tk.HORIZONTAL, length=150
                )
                speed_scale.grid(row=0, column=3, padx=5)
                speed_label = ttk.Label(self.param_frame, text=str(self.animation_speed.get()) + " мс")
                speed_label.grid(row=0, column=4, padx=5)
                speed_scale.config(command=lambda val: speed_label.config(text=str(int(float(val))) + " мс"))

        elif action_id == 9:
            ttk.Label(self.param_frame, text="Шагов:").grid(row=0, column=0, padx=5)
            tk.Entry(
                self.param_frame, textvariable=self.sine_steps, width=5,
                bg=t["entry_bg"], fg=t["entry_fg"],
                insertbackground=t["entry_fg"],
                font=("Consolas", 11), relief=tk.FLAT, bd=2
            ).grid(row=0, column=1, padx=5)
            ttk.Label(self.param_frame, text="Амплитуда:").grid(row=0, column=2, padx=5)
            tk.Entry(
                self.param_frame, textvariable=self.sine_amp, width=10,
                bg=t["entry_bg"], fg=t["entry_fg"],
                insertbackground=t["entry_fg"],
                font=("Consolas", 11), relief=tk.FLAT, bd=2
            ).grid(row=0, column=3, padx=5)
        else:
            ttk.Label(self.param_frame, text="Дополнительных параметров не требуется").grid(row=0, column=0, padx=5)

    def _on_action_change(self, event=None):
        action_id = self.current_action.get()
        if action_id in ACTIONS:
            self.action_label.config(text=ACTIONS[action_id]["name"])
            self._build_params(action_id)

    def _toggle_theme(self):
        if self.theme_var.get():
            self.current_theme = "violet"
        else:
            self.current_theme = "light"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.current_theme]
        self.root.configure(bg=t["root_bg"])

        # ttk-виджеты красятся через Style, а не через bg=
        style = ttk.Style()
        style.configure("TFrame", background=t["panel_bg"])
        style.configure("TLabelframe", background=t["panel_bg"])
        style.configure("TLabelframe.Label", background=t["panel_bg"], foreground=t["cell_fg"])
        style.configure("TLabel", background=t["panel_bg"], foreground=t["cell_fg"])
        style.configure("TButton", background=t["panel_bg"], foreground=t["cell_fg"])
        style.configure("TCheckbutton", background=t["panel_bg"], foreground=t["cell_fg"])
        style.configure("TCombobox", fieldbackground=t["entry_bg"], background=t["panel_bg"],
                        foreground=t["entry_fg"])
        style.configure("TEntry", fieldbackground=t["entry_bg"], foreground=t["entry_fg"])
        style.configure("TScale", background=t["panel_bg"])

        # Текстовое поле журнала — обычный tk.Text, красится напрямую
        self.info_text.configure(bg=t["info_bg"], fg=t["info_fg"])

        # Клетки таблиц
        for model, cells in [(self.model_a, self.left_cells), (self.model_b, self.right_cells)]:
            for i in range(model.rows):
                for j in range(model.cols):
                    if i < len(cells) - 1:
                        cell_frame, label = cells[i][j]
                        cell_frame.configure(bg=t["cell_bg"])
                        label.configure(bg=t["cell_bg"], fg=t["cell_fg"])

            bottom_cells = cells[-1]
            for blabel in bottom_cells:
                blabel.configure(foreground=t["bottom_fg"])

 
        # Переключение combobox <-> radiobuttons
        if self.current_theme == "violet":
            self.action_combo_label.pack_forget()
            self.action_combo.pack_forget()
            self.action_label.pack_forget()
            self.radio_frame.pack(side=tk.LEFT, padx=(0, 10), before=self.run_button)
        else:
            self.radio_frame.pack_forget()
            self.action_combo_label.pack(side=tk.LEFT, padx=(0, 5), before=self.run_button)
            self.action_combo.pack(side=tk.LEFT, padx=(0, 10), before=self.run_button)
            self.action_label.pack(side=tk.LEFT, padx=(0, 10), before=self.run_button)




       # Кнопки
        if self.current_theme == "violet":
            self.run_button.config(
                text="Run",
                bg=t["highlight_bg"],
                fg="white",
                activebackground="#c73852",
                activeforeground="white"
            )
            self.reset_button.config(
                text="Reset",
                bg="#4a6fa5", activebackground="#3a5a8a",
                fg="white", activeforeground="white"
            )
            self.csv_button.config(
                bg="#53d769", activebackground="#3ba850",
                fg="#0a1a0a", activeforeground="#0a1a0a"
            )
            self.json_button.config(
                bg="#4a6fa5", activebackground="#3a5a8a",
                fg="white", activeforeground="white"
            )
            self.spice_button.config(
                bg="#6c5ce7", activebackground="#5b4bd1",
                fg="white", activeforeground="white"
            )
        else:
            self.run_button.config(
                text="Выполнить",
                bg="#e0e0e0", activebackground="#d0d0d0",
                fg="#333333", activeforeground="#333333"
            )
            self.reset_button.config(
                text="Сброс",
                bg="#e0e0e0", activebackground="#d0d0d0",
                fg="#333333", activeforeground="#333333"
            )
            self.csv_button.config(
                bg="#e0e0e0", activebackground="#d0d0d0",
                fg="#333333", activeforeground="#333333"
            )
            self.json_button.config(
                bg="#e0e0e0", activebackground="#d0d0d0",
                fg="#333333", activeforeground="#333333"
            )
            self.spice_button.config(
                bg="#e0e0e0", activebackground="#d0d0d0",
                fg="#333333", activeforeground="#333333"
            )

        # Навигация: только в тёмной теме
        if self.current_theme == "violet":
            self.nav_frame.pack(fill=tk.X, padx=10, pady=2, before=self.info_text)
        else:
            self.nav_frame.pack_forget()


        self._refresh_display()



    def _execute(self):
        action_id = self.current_action.get()
        params = {}
        if action_id in (8, 10, 11, 12, 13, 14, 15, 16, 17):
            try:
                params["a"] = int(self.lattice_a.get())
                if action_id in (8, 10):
                    params["b"] = int(self.lattice_b.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Введите целые числа")
                return

        elif action_id == 1:
            try:
                params["n"] = int(self.stirling_n.get())
            except ValueError:
                params["n"] = 5

        elif action_id == 9:
            try:
                params["steps"] = int(self.sine_steps.get())
                params["amplitude"] = int(self.sine_amp.get())
                params["shift_bit"] = int(self.sine_shift.get())
            except ValueError:
                messagebox.showerror("Ошибка", "Проверьте параметры генератора синуса")
                return

        print("[ОТЛАДКА GUI] Нажата кнопка Выполнить. Действие: " + str(action_id) + ", параметры: " + str(params))
        self.model_a, self.model_b = execute_action(action_id, self.model_a, self.model_b, params)

        meta = self.model_b.metadata
        if meta:
            print("[ОТЛАДКА GUI] Метаданные после вычислений: " + str(list(meta.keys())))
        else:
            print("[ОТЛАДКА GUI] Метаданные после вычислений: Пусто")

        has_history = "steps_history" in meta
        print("[ОТЛАДКА GUI] steps_history в метаданных: " + str(has_history))
        if has_history:
            print("[ОТЛАДКА GUI] Количество шагов: " + str(len(meta["steps_history"])))

        if action_id in (1, 10, 11, 12, 13, 14, 15, 16, 17) and has_history:
            print("[ОТЛАДКА GUI] Запуск анимации для действия " + str(action_id))
            self._stop_play()
            self.is_playing = True
            if self.current_theme == "violet":
                self.nav_play.config(text="Pause")
            self._run_steps_animation(0)
        else:
            print("[ОТЛАДКА GUI] Анимация не запущена. Переходим к стандартному отображению.")
            self._refresh_display()
            self._show_info()

    def _run_steps_animation(self, current_step_idx, history=None, manual=False):
        if history is None:
            history = list(self.model_b.metadata.get("steps_history", []))

        self.current_history = history
        self.current_step_idx = current_step_idx

        if manual:
            self._stop_play()

        print("[ОТЛАДКА АНИМАЦИИ] Шаг " + str(current_step_idx) + " из " + str(len(history)))

        if current_step_idx >= len(history):
            print("[ОТЛАДКА АНИМАЦИИ] Достигнут конец истории. Завершение.")
            self.info_text.config(state=tk.NORMAL)
            self.info_text.insert(tk.END, "\n\n" + str(self.model_b.metadata.get("lattice_viz", "")))
            self.info_text.config(state=tk.DISABLED)
            return

        step_data = history[current_step_idx]
        action_id = self.current_action.get()

        saved_result = self.model_b.metadata.get("result", 0)
        saved_viz = self.model_b.metadata.get("lattice_viz", "")

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

        left_data = step_data.get("left", {})
        print("[ОТЛАДКА АНИМАЦИИ] left_data: " + str(len(left_data)) + " ячеек")

        for (r, c), val in left_data.items():
            self.model_a.set_cell(r, c, val)

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
        elif action_id in (1, 13, 14, 15, 16, 17):
            right_data = step_data.get("right", {})
            print("[ОТЛАДКА АНИМАЦИИ] right_data: " + str(len(right_data)) + " ячеек")
            for (r, c), val in right_data.items():
                self.model_b.set_cell(r, c, val)
        else:
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

        # Обновление навигационной метки
        if self.current_theme == "violet":
            self.nav_step_label.config(
                text="Кадр " + str(current_step_idx + 1) + "/" + str(len(history))
            )

        # Авто-переход только если не ручная навигация
        if not manual and current_step_idx < len(history) - 1:
            next_idx = current_step_idx + 1
            current_delay = self.animation_speed.get()
            self.play_after_id = self.root.after(
                current_delay,
                lambda idx=next_idx, hist=history: self._run_steps_animation(idx, hist)
            )
        elif not manual and current_step_idx >= len(history) - 1:
            # Достигнут конец — останавливаем
            self.is_playing = False
            if self.current_theme == "violet":
                self.nav_play.config(text="Play")

    def _reset(self):
        self.model_a.reset()
        self.model_b.reset()
        self._refresh_display()
        self._show_info()

    def _refresh_display(self):
        action_id = self.current_action.get()
        t = THEMES[self.current_theme]

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
                                    cell_frame.config(bg=t["cell_bg"])
                                    label.config(bg=t["cell_bg"], foreground=t["cell_fg"])
                            else:
                                cell_frame.config(bg=t["cell_bg"])
                                label.config(bg=t["cell_bg"], foreground=t["cell_fg"])

                        # Подсветка для действий 11-16 (левая таблица — выделение)
                        elif action_id in (11, 12, 13, 14, 15, 16, 17) and is_left_table:
                            highlight_cells = self.model_b.metadata.get("highlight_cells_current", [])
                            if (i, j) in highlight_cells:
                                cell_frame.config(bg=t["highlight_bg"])
                                label.config(bg=t["highlight_bg"], foreground=t["highlight_fg"])
                            else:
                                cell_frame.config(bg=t["cell_bg"])
                                label.config(bg=t["cell_bg"], foreground=t["cell_fg"])

                        # Начало блока Действие 1 (раскраска)
                        elif action_id == 1 and is_right_table:
                            if 0 <= val < len(PHASANT_COLORS):
                                color_name = PHASANT_COLORS[val]
                                hex_color = COLOR_MAP.get(color_name, t["cell_bg"])
                                fg_color = "white" if color_name == "чёрный" else "black"
                                cell_frame.config(bg=hex_color)
                                label.config(bg=hex_color, foreground=fg_color)
                            else:
                                cell_frame.config(bg=t["cell_bg"])
                                label.config(bg=t["cell_bg"], foreground=t["cell_fg"])
                        # Конец блока Действие 1 (раскраска)

                        # Подсветка для правой таблицы (фазановые цвета)
                        elif is_right_table and 0 < val < len(PHASANT_COLORS):
                            color_name = PHASANT_COLORS[val]
                            hex_color = COLOR_MAP.get(color_name, t["cell_bg"])
                            fg_color = "white" if color_name == "чёрный" else "black"
                            cell_frame.config(bg=hex_color)
                            label.config(bg=hex_color, foreground=fg_color)
                        else:
                            cell_frame.config(bg=t["cell_bg"])
                            label.config(bg=t["cell_bg"], foreground=t["cell_fg"])

            bottom_cells = cells[-1]
            for j in range(model.cols):
                if j < len(bottom_cells):
                    bottom_cells[j].config(text=str(model.get_bottom(j)))

    def _show_info(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        action_id = self.current_action.get()
        info_lines = ["Действие " + str(action_id) + ": " + ACTIONS[action_id]["desc"]]

        if self.model_b.metadata:
            meta = self.model_b.metadata
            if "lattice_viz" in meta:
                if "a" in meta and "b" in meta:
                    info_lines.append("\nРезультат: " + str(meta["a"]) + " x " + str(meta["b"]) + " = " + str(meta["result"]) + "\n")
                elif "a" in meta:
                    info_lines.append("\nРезультат для n=" + str(meta["a"]) + ": " + str(meta["result"]) + "\n")
                info_lines.append(meta["lattice_viz"])
            else:
                info_lines.append("\nМетаданные:\n" + json.dumps(meta, ensure_ascii=False, indent=2))

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
                json.dump(
                    {"table_a": self.model_a.to_dict(), "table_b": self.model_b.to_dict()},
                    f, indent=2
                )
            messagebox.showinfo("Успех", "JSON сохранен")

    def _export_spice(self):
        filename = filedialog.asksaveasfilename(defaultextension=".spice", filetypes=[("SPICE", "*.spice")])
        if filename:
            with open(filename, "w") as f:
                f.write("* Yupana Netlist\n.subckt yupana_core\n")
                f.write(".ends\n")
            messagebox.showinfo("Успех", "SPICE файл создан")

    def _stop_play(self):
        """Остановить авто-воспроизведение."""
        self.is_playing = False
        if self.play_after_id:
            self.root.after_cancel(self.play_after_id)
            self.play_after_id = None
        if self.current_theme == "violet":
            self.nav_play.config(text="Play")

    def _nav_prev(self):
        """Шаг назад."""
        if self.current_step_idx > 0:
            self._run_steps_animation(
                self.current_step_idx - 1,
                self.current_history,
                manual=True
            )

    def _nav_next(self):
        """Шаг вперёд."""
        if self.current_step_idx < len(self.current_history) - 1:
            self._run_steps_animation(
                self.current_step_idx + 1,
                self.current_history,
                manual=True
            )

    def _nav_play(self):
        """Play/Pause — переключение авто-воспроизведения."""
        if self.is_playing:
            self._stop_play()
        else:
            if self.current_step_idx >= len(self.current_history) - 1:
                # Достигнут конец — начинаем сначала
                self.current_step_idx = 0
            self.is_playing = True
            self.nav_play.config(text="Pause")
            self._run_steps_animation(
                self.current_step_idx,
                self.current_history
            )

