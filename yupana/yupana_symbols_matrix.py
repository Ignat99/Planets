import json
import os

class YupanaSymbolMatrix:
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

        # Двухпроходная стратегия: сначала размещаем ключи 9XX (основные символы),
        # затем — однозначные ключи (3, 5, 7, 9) только в свободные позиции.
        for pass_num in range(2):
            for cokey, cocycle in cocycles.items():
                # Извлекаем номер из ключа коцикла: "2_Lightostatics" -> 2
                parts = cokey.split("_")
                try:
                    level_num = int(parts[0])
                except ValueError:
                    continue

                # Пропускаем коциклы с level < 2 (Инфостатика "0_4")
                if level_num < 2:
                    continue

                row = level_num - 2  # 2->0, 3->1, 4->2, 5->3, 6->4, 7->5

                cells = cocycle.get("cells", {})
                for cell_id, cell_data in cells.items():
                    symbol = cell_data.get("symbol", "")
                    if not symbol:
                        continue
                    if cell_id == "0":
                        continue  # масштаб — пропускаем

                    is_9xx = cell_id.startswith("9") and len(cell_id) > 1

                    # Проход 0: только 9XX; проход 1: только остальные
                    if pass_num == 0 and not is_9xx:
                        continue
                    if pass_num == 1 and is_9xx:
                        continue

                    # Вычисляем столбец
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
                        # В проходе 0 (9XX) — перезаписываем.
                        # В проходе 1 (остальные) — только если свободно.
                        if pass_num == 0 or key not in self.default_mapping:
                            self.default_mapping[key] = (cokey, cell_id)

        print(f"Базовая матрица символов инициализирована. Размещено: {len(self.default_mapping)}")

    def set_offset(self, row_shift, col_shift):
        self.offset = (row_shift, col_shift)

    def get_symbol_info(self, yupana_row, yupana_col):
        """Возвращает (cokey, cell_id) для клетки с учётом сдвига, или None."""
        base_r = yupana_row - self.offset[0]
        base_c = yupana_col - self.offset[1]
        return self.default_mapping.get((base_r, base_c))

    def get_filename_for_symbol(self, yupana_row, yupana_col):
        """Возвращает имя файла вида '2_Lightostatics__913.jpg' или None."""
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
