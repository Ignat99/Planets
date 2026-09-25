import json
import os

class YupanaSymbolMatrix:
    def __init__(self, json_path="receptacle.json"):
        self.json_path = json_path
        self.symbol_map = {}  # { "913": "T", "911": "l1", ... } - для справки
        self.default_mapping = {} # { (row, col): symbol_number }
        self.offset = (0, 0) # (row_shift, col_shift)
        self._load_data()

    def _load_data(self):
        """Загружает receptacle.json и строит базовую карту соответствий."""
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"Файл {self.json_path} не найден.")
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cocycles = data.get("cocycles", {})
        
        # Заполняем default_mapping на основе описания задачи
        # Примечание: В реальном JSON ключи ячеек - это строки ("0", "913" и т.д.).
        # Нам нужно сопоставить их с координатами матрицы Юпаны.
        # Поскольку в JSON нет явных координат (row, col), мы используем эвристику 
        # или предполагаем, что ключи ячеек соответствуют номерам символов.
        
        # Для примера реализации "по умолчанию" из вашего ТЗ:
        # Мы вручную зададим базовые точки, так как в JSON нет полей row/col.
        # В реальном проекте эти координаты должны быть в JSON или вычисляться алгоритмом.
        
        self.default_mapping[(0, 1)] = "913"  # T (время)
        self.default_mapping[(1, 0)] = "911"  # l1
        
        # Если в JSON есть другие явные связи, их можно добавить сюда.
        # Сейчас мы просто возвращаем эту структуру, которую можно расширить.
        print("Базовая матрица символов инициализирована.")
        print("Точки привязки по умолчанию: (0,1)->913, (1,0)->911")

    def set_offset(self, row_shift, col_shift):
        """Устанавливает глобальный сдвиг для всей матрицы символов."""
        self.offset = (row_shift, col_shift)
        print(f"Сдвиг установлен: row+={row_shift}, col+={col_shift}")

    def get_symbol_at(self, yupana_row, yupana_col):
        """
        Возвращает номер символа для данной клетки Юпаны с учетом сдвига.
        Если символа нет, возвращает None.
        """
        # Вычисляем "реальную" позицию в базовой карте
        base_r = yupana_row - self.offset[0]
        base_c = yupana_col - self.offset[1]
        
        key = (base_r, base_c)
        return self.default_mapping.get(key)

    def generate_full_matrix(self, rows, cols):
        """
        Генерирует полную матрицу (список списков) номеров символов для размера Юпаны.
        Пустые клетки заполняются None.
        """
        matrix = [[None for _ in range(cols)] for _ in range(rows)]
        
        for (r, c), symbol_id in self.default_mapping.items():
            # Применяем сдвиг
            target_r = r + self.offset[0]
            target_c = c + self.offset[1]
            
            # Проверка границ
            if 0 <= target_r < rows and 0 <= target_c < cols:
                matrix[target_r][target_c] = symbol_id
                
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
