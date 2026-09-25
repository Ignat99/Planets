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
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cocycles = data.get("cocycles", {})
        
        # Пример привязки. В реальном проекте эти координаты должны быть в JSON.
        # Сейчас хардкодим для демонстрации: (row, col) -> (cokey, cell_id)
        # cokey = "2_Lightostatics", cell_id = "913"
        self.default_mapping[(0, 1)] = ("2_Lightostatics", "913")
        self.default_mapping[(1, 0)] = ("2_Lightostatics", "911")
        
        print("Базовая матрица символов инициализирована.")

    def set_offset(self, row_shift, col_shift):
        self.offset = (row_shift, col_shift)

    def get_symbol_info(self, yupana_row, yupana_col):
        """
        Возвращает кортеж (cokey, cell_id) для данной клетки с учетом сдвига.
        Если символа нет, возвращает None.
        """
        base_r = yupana_row - self.offset[0]
        base_c = yupana_col - self.offset[1]
        return self.default_mapping.get((base_r, base_c))

    def get_filename_for_symbol(self, yupana_row, yupana_col):
        """
        Генерирует имя файла строго по твоему шаблону:
        {cokey}__{cell_id}.jpg
        Пример: 2_Lightostatics__913.jpg
        """
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
                matrix[target_r][target_c] = (cokey, cell_id) # Храним пару, а не просто ID
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
