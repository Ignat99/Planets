"""
execute_action.py
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

# Импорт функции рефакторинга из yupana_core
try:
    from yupana_core import (
        execute_action_refactoring_act0,
        execute_action_refactoring_act1,
        execute_action_refactoring_act2,
        execute_action_refactoring_act3,
        execute_action_refactoring_act4,
        execute_action_refactoring_act5,
        execute_action_refactoring_act6,
        execute_action_refactoring_act7,
        execute_action_refactoring_act8,
        execute_action_refactoring_act9,
        execute_action_refactoring_act10,
        execute_action_refactoring_act11,
        execute_action_refactoring_act12,
        execute_action_refactoring_act13,
        execute_action_refactoring_act14,
        execute_action_refactoring_act15,
        execute_action_refactoring_act16,
    )
except ImportError:
    print(f"[ОТЛАДКА] Не удалось импортировать yupana_core: {e}")
    yupana_core = None


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
        result = execute_action_refactoring_act0(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act0

        seq = result["seq"]
        last_row = model_b.rows - 1
        for j in range(model_b.cols):
            model_b.set_cell(last_row, j, seq[j])
    # Конец блока Действие 0

    # Начало блока Действие 1
    elif action_id == 1:
        n = params.get("n", 5)
        # Вызов функции из yupana_core action_refactoring_act1
        execute_action_refactoring_act1(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act1

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
        # Вызов функции из yupana_core action_refactoring_act2
        execute_action_refactoring_act2(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act2

        model_b.metadata = {"action": "add"}
    # Конец блока Действие 2

    # Начало блока Действие 3
    elif action_id == 3:
        # Вызов функции из yupana_core action_refactoring_act3
        execute_action_refactoring_act3(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act3

        model_b.metadata = {"action": "sub"}
    # Конец блока Действие 3

    # Начало блока Действие 4
    elif action_id == 4:
        # Вызов функции из yupana_core action_refactoring_act4
        execute_action_refactoring_act4(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act4

        model_b.metadata = {"action": "shift"}
    # Конец блока Действие 4

    # Начало блока Действие 5
    elif action_id == 5:
        # Вызов функции из yupana_core action_refactoring_act5
        execute_action_refactoring_act5(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act5

        model_b.metadata = {"action": "mirror"}
    # Конец блока Действие 5

    # Начало блока Действие 6
    elif action_id == 6:
        # Вызов функции из yupana_core action_refactoring_act6
        execute_action_refactoring_act6(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act6

        model_b.metadata = {"action": "transpose"}
    # Конец блока Действие 6

    # Начало блока Действие 7
    elif action_id == 7:
        # Вызов функции из yupana_core action_refactoring_act7
        execute_action_refactoring_act7(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act7

        model_b.metadata = {"action": "inverse"}
    # Конец блока Действие 7

    # Начало блока Действие 8
    elif action_id == 8:
        # Вызов функции из yupana_core action_refactoring_act8
        execute_action_refactoring_act8(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act8
    # Конец блока Действие 8

    # Начало блока Действие 9
    elif action_id == 9:
        # Вызов функции из yupana_core action_refactoring_act9
        execute_action_refactoring_act9(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act9
    # Конец блока Действие 9

    # Начало блока Действие 10
    elif action_id == 10:
        # Вызов функции из yupana_core action_refactoring_act10
        execute_action_refactoring_act10(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act10
    # Конец блока Действие 10

    # Начало блока Действие 11
    elif action_id == 11:
        # Вызов функции из yupana_core action_refactoring_act11
        execute_action_refactoring_act11(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act11
    # Конец блока Действие 11

    # Начало блока Действие 12
    elif action_id == 12:
        # Вызов функции из yupana_core action_refactoring_act12
        execute_action_refactoring_act12(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act12
    # Конец блока Действие 12

    # Начало блока Действие 13
    elif action_id == 13:
        # Вызов функции из yupana_core action_refactoring_act13
        execute_action_refactoring_act13(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act13
    # Конец блока Действие 13

    # Начало блока Действие 14
    elif action_id == 14:
        # Вызов функции из yupana_core action_refactoring_act14
        execute_action_refactoring_act14(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act14
    # Конец блока Действие 14

    # Начало блока Действие 15
    elif action_id == 15:
        # Вызов функции из yupana_core action_refactoring_act15
        execute_action_refactoring_act15(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act15
    # Конец блока Действие 15

    # Начало блока Действие 16
    elif action_id == 16:
        # Вызов функции из yupana_core action_refactoring_act16
        execute_action_refactoring_act16(action_id, model_a, model_b, params)
        # Конец вызова функции из yupana_core action_refactoring_act16
    # Конец блока Действие 16

    return model_a, model_b
