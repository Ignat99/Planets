"""
yupana_symbols_matrix.py — Массивы констант для эмулятора Юпаны с Tkinter GUI.

Импорт:

from yupana_symbols_matrix import YupanaSymbolMatrix
"""

import json
import os


class YupanaSymbolMatrix:
    # Смещения колонок вдоль диагонали от стартовой колонки:
    # шаг 0 → +0, шаг 1 → +3, шаг 2 → +5, шаг 3 → +6, шаг 4 → +7
#    DIAGONAL_COL_OFFSETS = [0, 3, 5, 6, 7]
    DIAGONAL_COL_OFFSETS = [0, 2, 4, 6, 8]

    def __init__(self, json_path="receptacle.json"):
        self.json_path = json_path
        self.default_mapping = {}  # { (row, col): (cokey, cell_id) }
        self.offset = (0, 0)
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"Файл {self.json_path} не найден.")

        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cocycles = data.get("cocycles", {})

        for pass_num in range(2):
            for cokey, cocycle in cocycles.items():
                parts = cokey.split("_")
                try:
                    level_num = int(parts[0])
                except ValueError:
                    continue

                if level_num < 2:
                    continue

                row = level_num - 2

                cells = cocycle.get("cells", {})
                for cell_id, cell_data in cells.items():
                    symbol = cell_data.get("symbol", "")
                    if not symbol:
                        continue
                    if cell_id == "0":
                        continue

                    is_9xx = cell_id.startswith("9") and len(cell_id) > 1

                    if pass_num == 0 and not is_9xx:
                        continue
                    if pass_num == 1 and is_9xx:
                        continue

                    if is_9xx:
                        try:
                            n = int(cell_id[-2:])
                            col = (n - 11) // 2
                        except ValueError:
                            continue
                    else:
                        try:
                            n = int(cell_id)
                            col = (n - 1) // 2
                        except ValueError:
                            continue

                    if 0 <= col <= 8:
                        key = (row, col)
                        if pass_num == 0 or key not in self.default_mapping:
                            self.default_mapping[key] = (cokey, cell_id)

        print(f"Базовая матрица символов инициализирована. Размещено: {len(self.default_mapping)}")

    def set_offset(self, row_shift, col_shift):
        self.offset = (row_shift, col_shift)

    def get_symbol_info(self, yupana_row, yupana_col):
        base_r = yupana_row - self.offset[0]
        base_c = yupana_col - self.offset[1]
        return self.default_mapping.get((base_r, base_c))

    def get_filename_for_symbol(self, yupana_row, yupana_col):
        info = self.get_symbol_info(yupana_row, yupana_col)
        if info:
            cokey, cell_id = info
            return f"{cokey}__{cell_id}.jpg"
        return None

    def generate_full_matrix(self, rows, cols):
        matrix = [[None for _ in range(cols)] for _ in range(rows)]
        for (r, c), (cokey, cell_id) in self.default_mapping.items():
            target_r = r + self.offset[0]
            target_c = c + self.offset[1]
            if 0 <= target_r < rows and 0 <= target_c < cols:
                matrix[target_r][target_c] = (cokey, cell_id)
        return matrix

    def get_diagonal_formula(self, display_row, display_col, matrix_value):
        """
        Если клетка лежит на косой диагонали, возвращает строку формулы
        вида "1*x^1*t^0" или "6*x^3*c^-2*t^-1".
        Иначе возвращает None.
        """
        start_col = self.offset[1]
        col_from_start = display_col - start_col

        if col_from_start not in self.DIAGONAL_COL_OFFSETS:
            return None

        step = self.DIAGONAL_COL_OFFSETS.index(col_from_start)
        start_row = display_row - step

        if start_row < 0:
            return None

        t_power = -step
        x_power = 2 * step + 1

        # Коэффициент — значение матрицы в этой клетке
        parts = [str(matrix_value), f"x^{x_power}"]

        # c^-2 добавляется для нечётных start_row, начиная с шага 1
        if start_row % 2 == 1 and step > 0:
            parts.append("c^-2")

        parts.append(f"t^{t_power}")

        return "*".join(parts)



# --- Пример использования (можно вставить в yupana_emulator.py) ---

if __name__ == "__main__":
    # 1. Инициализация
    symbol_engine = YupanaSymbolMatrix("receptacle.json")
    
    # 2. Установка сдвига (опционально)
    # Например, сдвинуть все символы на 2 строки вниз и 1 столбец вправо
    symbol_engine.set_offset(2, 1) 
    
    # 3. Получение матрицы для текущего размера Юпаны (например, 9x9)
    yupana_size = (9, 9)
    matrix = symbol_engine.generate_full_matrix(*yupana_size)
    
    print("\nСгенерированная матрица номеров символов (None = пусто):")
    for r in matrix:
        print(r)

    # Пример получения конкретного символа
    # Допустим, нам нужен символ для клетки (2, 2) в интерфейсе
    sym_id = symbol_engine.get_symbol_at(2, 2)
    if sym_id:
        print(f"\nДля клетки (2,2) нужен символ с номером: {sym_id}")
        # Далее в коде эмулятора: найти файл symbols/{sym_id}.jpg или {cokey}__{sym_id}.jpg
    else:
        print("\nДля клетки (2,2) символ не назначен.")
