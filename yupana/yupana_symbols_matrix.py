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
    # Пастельные цвета
    COLOR_DISTRIBUTED = "#F7E4D4"    # персиковый — распределённые
    COLOR_CONCENTRATED = "#D4E5F7"   # голубой — сосредоточенные
    COLOR_DEFAULT = "#FFFFFF"
    # Порядок формы по базовым столбцам (без offset):
    # col 0: -1 | col 1: 0 (T) | col 2: 1 | col 3: 0 (Alpha/N1) | col 4: 1
    # col 5: 2 | col 6: 3      | col 7: 2 | col 8: 1
    X_POWERS_BY_COL = [-1, 0, 1, 0, 1, 2, 3, 2, 3, 4, 4]
#    X_POWERS_BY_COL = [1, 0, 1, 2, 3, 2, 3, 4, 4]

    # Фаза пространства: добавка к степени x во всех формулах.
    # 0 — свёрнутое (Бартини, L = x^-1), c^2 в парах присутствует
    # 2 — плоское (L = x^1), c^2 в парах сокращается
    # 3 — объёмное (L = x^2)
    X_PHASE_SHIFT = 0

    # Степени x для чётных display-колонок (Бартини/Крон — СИ)
    # display col 2→base 1: 0, col 4→base 3: 0, col 6→base 5: 2, col 8→base 7: 2
    X_POWERS_EVEN_COL = {1: 0, 3: 0, 5: 2, 7: 2}


    # Якорные клетки: (display_row, display_col) -> (c_power, t_power)
    ANCHORS = {
        (2, 4): (0, 0),   # Alpha — распределённая
        (2, 3): (0, -1),   # F — сосредоточенная
    }

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
        start_col = self.offset[1]
        col_from_start = display_col - start_col

        if col_from_start not in self.DIAGONAL_COL_OFFSETS:
            return None

        step = self.DIAGONAL_COL_OFFSETS.index(col_from_start)
        start_row = display_row - step

        if start_row < 0:
            return None

        base_c = display_col - self.offset[1]
        if base_c < 0 or base_c >= len(self.X_POWERS_BY_COL):
            return None

        t_power = -step
        x_power = self.X_POWERS_BY_COL[base_c]

        # c^-2 для любого нечётного start_row (не только step > 0)
        has_c2 = (start_row % 2 == 1)
        if has_c2:
            x_power += 2

        parts = [str(matrix_value), f"x^{x_power}"]
        if has_c2:
            parts.append("c^-2")
        parts.append(f"t^{t_power}")

        return "*".join(parts)


    def get_cell_color(self, display_row, display_col):
        """Возвращает цвет клетки по паттерну сосредоточенные/распределённые."""
        base_r = display_row - self.offset[0]
        base_c = display_col - self.offset[1]

        # Только для клеток физической матрицы (6 строк × 9 столбцов)
        if base_r < 0 or base_r > 5 or base_c < 0 or base_c > 8:
            return self.COLOR_DEFAULT

        # Паттерн: блок по 4 колонки, позиции 0 и 3 — тип A, 1 и 2 — тип B
        pos_in_block = base_c % 4
        is_type_a = (pos_in_block == 0 or pos_in_block == 3)
        is_even_row = (base_r % 2 == 0)

        # Чётные строки: A = сосредоточенные, B = распределённые
        # Нечётные строки: A = распределённые, B = сосредоточенные
        if is_even_row:
            return self.COLOR_CONCENTRATED if is_type_a else self.COLOR_DISTRIBUTED
        else:
            return self.COLOR_DISTRIBUTED if is_type_a else self.COLOR_CONCENTRATED

    def get_even_col_formula(self, display_row, display_col, matrix_value):
        base_c = display_col - self.offset[1]
        if base_c not in self.X_POWERS_EVEN_COL:
            return None

        x_power = self.X_POWERS_EVEN_COL[base_c]

        # Сосед справа: нечётный столбец base_c + 1
        neighbor_col_from_start = base_c + 1
        if neighbor_col_from_start not in self.DIAGONAL_COL_OFFSETS:
            return None

        neighbor_step = self.DIAGONAL_COL_OFFSETS.index(neighbor_col_from_start)
        neighbor_start_row = display_row - neighbor_step

        if neighbor_start_row < 0:
            return None

        neighbor_t = -neighbor_step
        neighbor_has_c2 = (neighbor_start_row % 2 == 1)

        # Поправка: +2 если у соседа нет c^-2, +0 если есть
        t_power = neighbor_t + (0 if neighbor_has_c2 else 2)
        has_c2 = neighbor_has_c2

        parts = [str(matrix_value), f"x^{x_power}"]
        if has_c2:
            parts.append("c^-2")
        parts.append(f"t^{t_power}")

        return "*".join(parts)


    def _get_cell_type(self, r, c):
        color = self.get_cell_color(r, c)
        if color == self.COLOR_DISTRIBUTED:
            return "distributed"
        elif color == self.COLOR_CONCENTRATED:
            return "concentrated"
        return None

    def _get_diagonal_transitions(self, r, c):
        """4 косых перехода: (nr, nc, delta_c, delta_t)."""
        t = self._get_cell_type(r, c)
        if t == "distributed":
            return [
                (r - 1, c - 2,  0,  1),   # ↖  t^1
                (r - 1, c + 2, -2, -1),   # ↗  c^-2 * t^-1
                (r + 1, c + 2,  0, -1),   # ↘  t^-1
                (r + 1, c - 2,  2,  1),   # ↙  c^2 * t^1
            ]
        elif t == "concentrated":
            return [
                (r - 1, c - 2,  2,  1),   # ↖  c^2 * t^1
                (r - 1, c + 2,  0, -1),   # ↗  t^-1
                (r + 1, c + 2, -2, -1),   # ↘  c^-2 * t^-1
                (r + 1, c - 2,  0,  1),   # ↙  t^1
            ]
        return []

    def _get_vertical_transitions(self, r, c):
        """Вертикальные переходы c^4 / c^-4."""
        t = self._get_cell_type(r, c)
        if t == "distributed":
            return [
                (r + 4, c,  4, 0),   # c^4  → строка +4
                (r - 4, c, -4, 0),   # c^-4 → строка −4
            ]
        elif t == "concentrated":
            return [
                (r - 4, c,  4, 0),   # c^4  → строка −4
                (r + 4, c, -4, 0),   # c^-4 → строка +4
            ]
        return []

    def _get_horizontal_transitions(self, r, c):
        """Горизонтальные переходы между однотипными соседями
        (производная по x): вправо c^2*t^1, влево c^-2*t^-1."""
        transitions = []
        t1 = self._get_cell_type(r, c)
        if not t1:
            return transitions

        # Вправо (c+1)
        t2 = self._get_cell_type(r, c + 1)
        if t2 and t2 == t1:
            transitions.append((r, c + 1, 2, 1))

        # Влево (c-1)
        t2 = self._get_cell_type(r, c - 1)
        if t2 and t2 == t1:
            transitions.append((r, c - 1, -2, -1))

        return transitions

    def _get_all_transitions(self, r, c):
        return (self._get_diagonal_transitions(r, c) +
                self._get_vertical_transitions(r, c) +
                self._get_horizontal_transitions(r, c))

    def compute_all_formulas(self, nrows=7, ncols=9):
        """BFS от якорей: (c_power, t_power) для всех клеток."""
        from collections import deque

        formula_powers = {}

        for (ar, ac), (c0, t0) in self.ANCHORS.items():
            queue = deque()
            queue.append((ar, ac, c0, t0))
            visited = {(ar, ac): (c0, t0)}

            while queue:
                r, c, cp, tp = queue.popleft()
                for nr, nc, dc, dt in self._get_all_transitions(r, c):
                    base_r = nr - self.offset[0]
                    base_c = nc - self.offset[1]
                    if base_r < 0 or base_r >= nrows or base_c < 0 or base_c >= ncols:
                        continue
                    if (nr, nc) in visited:
                        continue
                    visited[(nr, nc)] = (cp + dc, tp + dt)
                    queue.append((nr, nc, cp + dc, tp + dt))

            formula_powers.update(visited)

        self._formula_powers = formula_powers
        return formula_powers

    def get_cell_formula_old(self, display_row, display_col, matrix_value):
        """Полная формула: val*x^p*c^q*t^r."""
        if not hasattr(self, '_formula_powers'):
            self.compute_all_formulas()

        key = (display_row, display_col)
        if key not in self._formula_powers:
            return None

        c_power, t_power = self._formula_powers[key]
        base_c = display_col - self.offset[1]
        if base_c < 0 or base_c >= len(self.X_POWERS_BY_COL):
            return None

        x_power = self.X_POWERS_BY_COL[base_c]

        parts = [str(matrix_value), f"x^{x_power}"]
        if c_power != 0:
            parts.append(f"c^{c_power}")
        if t_power != 0:
            parts.append(f"t^{t_power}")

        return "*".join(parts)

    def get_cell_formula(self, display_row, display_col, matrix_value):
        """Полная формула: val*x^p*c^q*t^r."""
        if not hasattr(self, '_formula_powers'):
            self.compute_all_formulas()

        key = (display_row, display_col)
        if key not in self._formula_powers:
            return None

        c_power, t_power = self._formula_powers[key]
        base_c = display_col - self.offset[1]
        if base_c < 0 or base_c >= len(self.X_POWERS_BY_COL):
            return None

        x_power = self.X_POWERS_BY_COL[base_c] + self.X_PHASE_SHIFT

        parts = [str(matrix_value), f"x^{x_power}"]
        if c_power != 0:
            parts.append(f"c^{c_power}")
        if t_power != 0:
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
