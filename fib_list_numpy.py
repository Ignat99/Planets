import numpy as np

# 1. Генерируем расширенную матрицу ypana (треугольник Паскаля) размером 9x9 через NumPy
# Это необходимо, чтобы работали индексы из fib_8 и fib_9 (строки 7 и 8)
ypana = np.zeros((9, 9), dtype=int)
for i in range(9):
    for j in range(9):
        if i == 0:
            ypana[i, j] = 1
        elif j == 0:
            ypana[i, j] = 1
        else:
            ypana[i, j] = ypana[i-1, j] + ypana[i, j-1]

print(ypana)

# 2. Автоматическая генерация координат и значений Фибоначчи на NumPy
fib_values = {}
fib_coords = {}

for n in range(1, 10):  # Для fib_1 ... fib_9
    # Для каждого n сумма индексов строки (r) и столбца (c) равна n - 1.
    # При этом строка уменьшается на 2, а столбец увеличивается на 1.
    
    # Генерируем массив строк: от (n-1) вниз до 0 с шагом -2
    rows = np.arange(n - 1, -1, -2)
    # Генерируем массив столбцов: от 0 вверх с шагом 1
    cols = np.arange(0, len(rows))
    
    # Объединяем их в двумерную матрицу координат (размерность К x 2)
    coords_matrix = np.column_stack((rows, cols))
    
    # Извлекаем значения из ypana по сгенерированным координатам и суммируем их
    value = np.sum(ypana[rows, cols])
    
    # Сохраняем в словари (для удобства работы)
    fib_coords[f"fib_{n}_coords"] = coords_matrix
    fib_values[f"fib_{n}_value"] = value

# ==========================================
# ДЕМОНСТРАЦИЯ РЕЗУЛЬТАТОВ (Вывод на экран)
# ==========================================

# Выведем конкретный пример, например для fib_5 и fib_9, как в вашем запросе:
for n in range(1, 10):
    print(f"--- fib_{n} ---")
    print(f"Значение Фибоначчи: {fib_values[f'fib_{n}_value']}")
    print("Матрица координат NumPy:")
    print(fib_coords[f"fib_{n}_coords"])
    print(f"Тип объекта координат: {type(fib_coords[f'fib_{n}_coords'])}\n")
