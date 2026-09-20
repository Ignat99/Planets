"""
yupana_emulator.py
Tkinter GUI эмулятор юпаны с полной поддержкой вычислений и умножения.
Версия с действиями 0-16 и отладочными сообщениями для действий 15 и 16.
Часть 1: модель, действия, вычисления.
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
    from yupana_emulator_gui import YupanaEmulatorGUI
except ImportError as e:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_emulator_gui: {e}")
    YupanaEmulatorGUI = None


if __name__ == "__main__":
    if YupanaEmulatorGUI is not None:
        root = tk.Tk()
        app = YupanaEmulatorGUI(root)
        root.mainloop()
    else:
        print("Ошибка: GUI модуль недоступен")
