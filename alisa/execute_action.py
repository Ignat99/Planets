"""
yupana_action.py
GUI часть эмулятора юпаны (часть 3 из 3).
Импортируется из yupana_emulator_gui.py.
"""

try:
    from yupana_math import (
        stirling_second_kind, format_cell_display, compute_a391838_sequence
    )
except ImportError:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_math: {e}")
    yupana_math = None
#    def compute_a391838_sequence(n): return [1, 6, 40, 336, 3456][:n]
#    def stirling_second_kind(n, k): return 1

# Импорт функции рефакторинга Действия 1 из yupana_core
try:
    from yupana_core import (
        execute_action_refactoring_act0,
        execute_action_refactoring_act1,
#        execute_action_refactoring_act1,
#        execute_action_refactoring_act1
    )
except ImportError:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_core: {e}")
    yupana_core = None
#    def execute_action_refactoring_act1(action_id, model_a, model_b, params=None):
#        pass

def execute_action(action_id, model_a, model_b, params=None):
    params = params or {}

    if action_id in (8, 10):
        model_a.reset()
        model_b.reset()
    elif action_id == 11:
        model_a.reset()
    elif action_id in (13, 14, 15, 16):
        model_a.reset()
        model_b.reset()

    # Начало блока Действие 0
    if action_id == 0:
        # Вызов функции из yupana_core action_refactoring_act0
        execute_action_refactoring_act0(action_id, model_a, model_b, params)

        # Должно быть (данные в последнюю строку клеток):
        seq = compute_a391838_sequence(model_b.cols)
        # Размещение результата в нижней строке Юпаны (последняя строка сетки)
        last_row = model_b.rows - 1
        for j in range(model_b.cols):
            model_b.set_cell(last_row, j, seq[j])
    # Конец блока Действие 0

    # Начало блока Действие 1
    elif action_id == 1:
        n = params.get("n", 5)
        # Вызов функции из yupana_core
        execute_action_refactoring_act1(action_id, model_a, model_b, params)
        # Размещение результата в нижней строке Юпаны (последняя строка сетки)
        last_row = model_b.rows - 1
        for j in range(model_b.cols):
            val = stirling_second_kind(last_row + 1, j + 1)
            model_b.set_cell(last_row, j, val)
        # Остальные строки — нули
        for i in range(last_row - 2):
            for j in range(model_b.cols):
                model_b.set_cell(i, j, 0)
        # Нижняя строка (вне сетки) — нули
        for j in range(model_b.cols):
            model_b.set_bottom(j, 0)
        model_b.metadata = {"action": "Stirling", "n": n}
    # Конец блока Действие 1

    # Начало блока Действие 2
    elif action_id == 2:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, j) * 2)
        model_b.metadata = {"action": "add"}
    # Конец блока Действие 2

    # Начало блока Действие 3
    elif action_id == 3:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "sub"}
    # Конец блока Действие 3

    # Начало блока Действие 4
    elif action_id == 4:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j > 0:
                    model_b.set_cell(i, j, model_a.get_cell(i, j - 1))
                else:
                    model_b.set_cell(i, j, 0)
        model_b.metadata = {"action": "shift"}
    # Конец блока Действие 4

    # Начало блока Действие 5
    elif action_id == 5:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(i, j, model_a.get_cell(i, model_a.cols - 1 - j))
        model_b.metadata = {"action": "mirror"}
    # Конец блока Действие 5

    # Начало блока Действие 6
    elif action_id == 6:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                if j < model_b.rows and i < model_b.cols:
                    model_b.set_cell(j, i, model_a.get_cell(i, j))
        model_b.metadata = {"action": "transpose"}
    # Конец блока Действие 6

    # Начало блока Действие 7
    elif action_id == 7:
        for i in range(model_a.rows):
            for j in range(model_a.cols):
                model_b.set_cell(model_a.rows - 1 - i, model_a.cols - 1 - j, model_a.get_cell(i, j))
        model_b.metadata = {"action": "inverse"}
    # Конец блока Действие 7

    # Начало блока Действие 8
    elif action_id == 8:
        a = params.get("a", 23)
        b = params.get("b", 41)
        try:
            state = emulator_lattice_action_old(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.set_bottom(0, result)
            model_b.metadata = {
                "action": "lattice_multiply", "a": a, "b": b, "result": result,
                "lattice_viz": state.get("lattice_str", "Сетка решётки построена успешно.")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "lattice_multiply", "a": a, "b": b, "result": result, "error": str(e)}
    # Конец блока Действие 8

    # Начало блока Действие 9
    elif action_id == 9:
        steps = params.get("steps", 9)
        amplitude = params.get("amplitude", 100000)
        shift_bit = params.get("shift_bit", 6)
        try:
            results = generate_sine_on_triangular_grid(steps, amplitude, shift_bit)
            sine_values = [r[2] for r in results]
            model_b.set_bottom_row(sine_values[:model_b.cols])
            model_b.metadata = {"action": "sine_nco", "steps": steps, "amplitude": amplitude, "sine_values": sine_values}
        except Exception as e:
            model_b.metadata = {"action": "sine_nco", "error": str(e)}
    # Конец блока Действие 9

    # Начало блока Действие 10
    elif action_id == 10:
        a = params.get("a", 11)
        b = params.get("b", 22)
        try:
            state = emulator_inca_lattice_action(a, b)
            left_data = state.get("left_yupana", {})
            right_data = state.get("right_yupana", {})
            result = state.get("result", a * b)

            for (r, c), val in left_data.items():
                if 0 <= r < model_a.rows and 0 <= c < model_a.cols:
                    model_a.set_cell(r, c, val)
            for (r, c), val in right_data.items():
                if 0 <= r < model_b.rows and 0 <= c < model_b.cols:
                    model_b.set_cell(r, c, val)

            model_b.metadata = {
                "action": "inca_multiply",
                "a": a, "b": b,
                "result": state.get("result", a * b),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            result = a * b
            model_b.set_bottom(0, result)
            model_b.metadata = {"action": "inca_multiply", "a": a, "b": b, "result": result, "error": str(e)}
    # Конец блока Действие 10

    # Начало блока Действие 11
    elif action_id == 11:
        n_val = params.get("a", 3)
        try:
            state = emulator_stirling_diagonal_action(n_val)
            model_b.metadata = {
                "action": "stirling_diagonal",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "stirling_diagonal", "error": str(e)}
    # Конец блока Действие 11

    # Начало блока Действие 12
    elif action_id == 12:
        n_val = params.get("a", 3)
        try:
            state = emulator_a391838_action(n_val)
            model_b.metadata = {
                "action": "a391838_row",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "a391838_row", "error": str(e)}
    # Конец блока Действие 12

    # Начало блока Действие 13
    elif action_id == 13:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lift_action(n_val)
            model_b.metadata = {
                "action": "column_lift",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lift", "error": str(e)}
    # Конец блока Действие 13

    # Начало блока Действие 14
    elif action_id == 14:
        n_val = params.get("a", 7)
        try:
            state = emulator_column_lower_action(n_val)
            model_b.metadata = {
                "action": "column_lower",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
        except Exception as e:
            model_b.metadata = {"action": "column_lower", "error": str(e)}
    # Конец блока Действие 14

    # Начало блока Действие 15
    elif action_id == 15:
        n_val = params.get("a", 7)
        print(f"[ОТЛАДКА GUI] Действие 15: вызов emulator_shift_rows_right_action(n={n_val})")
        print(f"[ОТЛАДКА GUI] _HAS_SHIFT_ROW_ACTIONS = {_HAS_SHIFT_ROW_ACTIONS}")
        try:
            state = emulator_shift_rows_right_action(n_val)
            print(f"[ОТЛАДКА GUI] Действие 15: state получен, ключи={list(state.keys())}")
            print(f"[ОТЛАДКА GUI] Действие 15: steps_history содержит {len(state.get('steps', []))} шагов")
            model_b.metadata = {
                "action": "shift_rows_right",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
            print(f"[ОТЛАДКА GUI] Действие 15: метаданные записаны, steps_history в метаданных: {'steps_history' in model_b.metadata}")
        except Exception as e:
            print(f"[ОТЛАДКА GUI] Действие 15: ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            model_b.metadata = {"action": "shift_rows_right", "error": str(e)}
    # Конец блока Действие 15

    # Начало блока Действие 16
    elif action_id == 16:
        n_val = params.get("a", 7)
        print(f"[ОТЛАДКА GUI] Действие 16: вызов emulator_shift_rows_left_action(n={n_val})")
        print(f"[ОТЛАДКА GUI] _HAS_SHIFT_ROW_ACTIONS = {_HAS_SHIFT_ROW_ACTIONS}")
        try:
            state = emulator_shift_rows_left_action(n_val)
            print(f"[ОТЛАДКА GUI] Действие 16: state получен, ключи={list(state.keys())}")
            print(f"[ОТЛАДКА GUI] Действие 16: steps_history содержит {len(state.get('steps', []))} шагов")
            model_b.metadata = {
                "action": "shift_rows_left",
                "a": n_val,
                "result": state.get("result", 0),
                "steps_history": state.get("steps", []),
                "lattice_viz": state.get("lattice_str", "")
            }
            print(f"[ОТЛАДКА GUI] Действие 16: метаданные записаны, steps_history в метаданных: {'steps_history' in model_b.metadata}")
        except Exception as e:
            print(f"[ОТЛАДКА GUI] Действие 16: ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            model_b.metadata = {"action": "shift_rows_left", "error": str(e)}
    # Конец блока Действие 16

    return model_a, model_b
