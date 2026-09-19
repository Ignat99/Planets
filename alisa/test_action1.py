"""
test_action1.py
Тесты для Действия 1: беззнаковые числа Стирлинга I рода.
Запуск: py test_action1.py
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def make_mock_model(rows=8, cols=8):
    """Создаёт mock-модель YupanaModel для тестов без GUI."""
    model = MagicMock()
    model.rows = rows
    model.cols = cols
    cells = [[0] * cols for _ in range(rows)]
    bottom = [0] * cols
    metadata = {}

    model.get_cell = MagicMock(side_effect=lambda r, c: cells[r][c])
    model.set_cell = MagicMock(side_effect=lambda r, c, v: cells.__setitem__(r, cells[r][:c] + [v] + cells[r][c+1:]))
    model.get_bottom = MagicMock(side_effect=lambda j: bottom[j])
    model.set_bottom = MagicMock(side_effect=lambda j, v: bottom.__setitem__(j, v))
    model.reset = MagicMock(side_effect=lambda: (cells.__setitem__(slice(None), [[0]*cols for _ in range(rows)]), bottom.__setitem__(slice(None), [0]*cols), metadata.clear()))
    model.metadata = metadata
    return model, cells, bottom


class TestStirlingUnsignedFirst(unittest.TestCase):
    """Тесты эталонных значений c(n,k)."""

    EXPECTED = {
        (0, 0): 1,
        (1, 0): 0, (1, 1): 1,
        (2, 0): 0, (2, 1): 1, (2, 2): 1,
        (3, 0): 0, (3, 1): 2, (3, 2): 3, (3, 3): 1,
        (4, 0): 0, (4, 1): 6, (4, 2): 11, (4, 3): 6, (4, 4): 1,
        (5, 0): 0, (5, 1): 24, (5, 2): 50, (5, 3): 35, (5, 4): 10, (5, 5): 1,
    }

    def test_known_values(self):
        """Проверка известных значений c(n,k)."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(5)
        self.assertEqual(len(table), 6, "Таблица должна иметь размер (N+1) x (N+1)")

        for (n, k), expected in self.EXPECTED.items():
            actual = table[n][k]
            self.assertEqual(actual, expected,
                f"c({n},{k}) = {actual}, ожидалось {expected}")

    def test_n0(self):
        """c(0,0) = 1 — вырожденный случай."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(0)
        self.assertEqual(table, [[1]])

    def test_n1(self):
        """c(1,0)=0, c(1,1)=1."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(1)
        self.assertEqual(table, [[1, 0], [0, 1]])

    def test_table_dimensions(self):
        """Размер таблицы (N+1) x (N+1)."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        for N in [3, 5, 10]:
            table = stirling_unsigned_first(N)
            self.assertEqual(len(table), N + 1, f"Строк должно быть {N+1}")
            for row in table:
                self.assertEqual(len(row), N + 1, f"Столбцов должно быть {N+1}")

    def test_diagonal_ones(self):
        """Диагональ c(n,n) = 1 для всех n."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(5)
        for n in range(6):
            self.assertEqual(table[n][n], 1, f"c({n},{n}) должно быть 1")

    def test_first_column(self):
        """c(n,0) = 0 для n > 0, c(0,0) = 1."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(5)
        self.assertEqual(table[0][0], 1)
        for n in range(1, 6):
            self.assertEqual(table[n][0], 0, f"c({n},0) должно быть 0")

    def test_recurrence(self):
        """Проверка рекуррентного соотношения c(n,k) = c(n-1,k-1) + (n-1)*c(n-1,k)."""
        try:
            from yupana_core import stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        table = stirling_unsigned_first(6)
        for n in range(2, 7):
            for k in range(1, n):
                expected = table[n-1][k-1] + (n-1) * table[n-1][k]
                self.assertEqual(table[n][k], expected,
                    f"Рекуррентность нарушена для c({n},{k}): {table[n][k]} != {expected}")


class TestExecuteActionRefactoringAct1(unittest.TestCase):
    """Тесты execute_action_refactoring_act1."""

    def test_returns_table_and_n(self):
        """Возвращает словарь с ключами 'table' и 'n'."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 5}

        result = execute_action_refactoring_act1(1, model_a, model_b, params)

        self.assertIsInstance(result, dict)
        self.assertIn("table", result)
        self.assertIn("n", result)
        self.assertEqual(result["n"], 5)

    def test_default_n5(self):
        """Если n не указано, используется 5."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()

        result = execute_action_refactoring_act1(1, model_a, model_b, {})
        self.assertEqual(result["n"], 5)

    def test_table_values_match_stirling(self):
        """Значения в таблице совпадают с эталонными."""
        try:
            from yupana_core import execute_action_refactoring_act1, stirling_unsigned_first
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 5}

        result = execute_action_refactoring_act1(1, model_a, model_b, params)
        table = result["table"]

        expected = {
            (0, 0): 1,
            (3, 1): 2, (3, 2): 3, (3, 3): 1,
            (5, 1): 24, (5, 2): 50, (5, 3): 35, (5, 4): 10, (5, 5): 1,
        }
        for (n, k), val in expected.items():
            self.assertEqual(table[n][k], val,
                f"c({n},{k}) = {table[n][k]}, ожидалось {val}")

    def test_n3(self):
        """Таблица для n=3."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 3}

        result = execute_action_refactoring_act1(1, model_a, model_b, params)
        table = result["table"]

        self.assertEqual(table[0][0], 1)
        self.assertEqual(table[1][1], 1)
        self.assertEqual(table[2][1], 1)
        self.assertEqual(table[2][2], 1)
        self.assertEqual(table[3][1], 2)
        self.assertEqual(table[3][2], 3)
        self.assertEqual(table[3][3], 1)

    def test_n10(self):
        """Таблица для n=10 — проверка больших значений."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 10}

        result = execute_action_refactoring_act1(1, model_a, model_b, params)
        table = result["table"]

        self.assertEqual(len(table), 11)
        # c(10,10) = 1
        self.assertEqual(table[10][10], 1)
        # c(10,1) = 9! = 362880
        self.assertEqual(table[10][1], 362880)


class TestExecuteActionAct1(unittest.TestCase):
    """Тесты execute_action для action_id == 1 (интеграционные)."""

    def test_metadata_set(self):
        """metadata содержит action и n."""
        try:
            from execute_action import execute_action
        except ImportError:
            self.skipTest("execute_action недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 5}

        execute_action(1, model_a, model_b, params)

        self.assertIn("action", model_b.metadata)
        self.assertEqual(model_b.metadata["action"], "Stirling")
        self.assertEqual(model_b.metadata["n"], 5)

    def test_cells_filled(self):
        """Клетки 0..n заполнены значениями Стирлинга, остальные — нули."""
        try:
            from execute_action import execute_action
        except ImportError:
            self.skipTest("execute_action недоступен")

        model_a, cells_b, _ = make_mock_model(rows=8, cols=8)
        model_b, _, _ = make_mock_model(rows=8, cols=8)
        # Перенаправляем set_cell на реальное хранение
        real_cells = [[0]*8 for _ in range(8)]
        model_b.set_cell = MagicMock(side_effect=lambda r, c, v: real_cells.__getitem__(r).__setitem__(c, v))
        model_b.get_cell = MagicMock(side_effect=lambda r, c: real_cells[r][c])
        model_b.metadata = {}
        params = {"n": 5}

        execute_action(1, model_a, model_b, params)

        # c(0,0) = 1
        self.assertEqual(real_cells[0][0], 1)
        # c(5,5) = 1
        self.assertEqual(real_cells[5][5], 1)
        # c(5,1) = 24
        self.assertEqual(real_cells[5][1], 24)
        # Строка 6 (за пределами n=5) — нули
        self.assertEqual(real_cells[6][0], 0)
        self.assertEqual(real_cells[6][5], 0)

    def test_bottom_zeroed(self):
        """Нижняя строка (вне сетки) обнулена."""
        try:
            from execute_action import execute_action
        except ImportError:
            self.skipTest("execute_action недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 3}

        execute_action(1, model_a, model_b, params)

        # set_bottom вызван 8 раз (по cols), все с нулём
        bottom_calls = model_b.set_bottom.call_args_list
        self.assertEqual(len(bottom_calls), 8)
        for call in bottom_calls:
            self.assertEqual(call[0][1], 0)

    def test_n3_values(self):
        """Проверка конкретных значений для n=3."""
        try:
            from execute_action import execute_action
        except ImportError:
            self.skipTest("execute_action недоступен")

        model_a, _, _ = make_mock_model(rows=8, cols=8)
        model_b, _, _ = make_mock_model(rows=8, cols=8)
        real_cells = [[0]*8 for _ in range(8)]
        model_b.set_cell = MagicMock(side_effect=lambda r, c, v: real_cells.__getitem__(r).__setitem__(c, v))
        model_b.get_cell = MagicMock(side_effect=lambda r, c: real_cells[r][c])
        model_b.metadata = {}
        params = {"n": 3}

        execute_action(1, model_a, model_b, params)

        expected = [
            [1, 0, 0, 0, 0, 0, 0, 0],  # c(0,*)
            [0, 1, 0, 0, 0, 0, 0, 0],  # c(1,*)
            [0, 1, 1, 0, 0, 0, 0, 0],  # c(2,*)
            [0, 2, 3, 1, 0, 0, 0, 0],  # c(3,*)
            [0, 0, 0, 0, 0, 0, 0, 0],  # строка 4 — нули
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        for i in range(8):
            for j in range(8):
                self.assertEqual(real_cells[i][j], expected[i][j],
                    f"cell({i},{j}) = {real_cells[i][j]}, ожидалось {expected[i][j]}")


class TestEdgeCases(unittest.TestCase):
    """Граничные случаи."""

    def test_n0(self):
        """n=0 — только c(0,0)=1 в строке 0, остальное нули."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()
        params = {"n": 0}

        result = execute_action_refactoring_act1(1, model_a, model_b, params)
        table = result["table"]

        self.assertEqual(table[0][0], 1)
        self.assertEqual(len(table), 1)

    def test_wrong_action_id(self):
        """Неверный action_id вызывает NotImplementedError."""
        try:
            from yupana_core import execute_action_refactoring_act1
        except ImportError:
            self.skipTest("yupana_core недоступен")

        model_a, _, _ = make_mock_model()
        model_b, _, _ = make_mock_model()

        with self.assertRaises(NotImplementedError):
            execute_action_refactoring_act1(99, model_a, model_b, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
