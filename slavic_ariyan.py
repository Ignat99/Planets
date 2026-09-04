import json

# Полный набор уникальных коэффициентов матрицы Юпаны 9x9, предоставленный вами
YUPANA_COEFFICIENTS = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 21, 28, 35, 36, 45, 56, 70, 84, 
    120, 126, 165, 210, 252, 330, 462, 495, 792, 924, 1287, 1716, 2431, 
    3432, 6435, 12870
]

# Шаг 1: Загрузка данных. 
# Замените 'planets.json' на путь к вашему файлу, если данные хранятся отдельно.
def load_planet_data(file_path="slavic_ariyan_lands.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        # Если файл не найден, подставим тестовую строку с вашими данными для примера
        raw_data = """[
          {"name_slavic": "Ярило-Солнце", "name_modern": "Солнце", "orbital_period": {"years": null, "days": null}},
          {"name_slavic": "Хорсъ", "name_modern": "Меркурий", "orbital_period": {"years": 0.241, "days": 88.0}},
          {"name_slavic": "Заря-Мерцана", "name_modern": "Венера", "orbital_period": {"years": 0.615, "days": 225.0}},
          {"name_slavic": "Мидгардъ", "name_modern": "Земля", "orbital_period": {"years": null, "days": 365.25}}
        ]"""
        return json.loads(raw_data)


# Шаг 2: Основная функция поиска периода обращения
def get_orbital_period_by_name(full_name: str, dataset: list):
    """
    Принимает имя в формате 'Ярило-Солнце (Солнце)' и возвращает orbital_period['days'].
    Если планета не найдена или период равен null, возвращает None.
    """
    for item in dataset:
        # Формируем строку для проверки по шаблону "Славянское (Современное)"
        current_formatted_name = f"{item['name_slavic']} ({item['name_modern']})"
        
        # Если нашли точное совпадение
        if current_formatted_name == full_name:
            return item["orbital_period"]["days"]
            
    return None


def find_best_yupana_coefficient(full_name: str, dataset: list):
    """
    Ищет планету по имени 'name_slavic (name_modern)'.
    Вычисляет целевое значение коэффициента по оптимизированной формуле: (days * 6) / module.
    Подбирает наиболее близкий коэффициент Юпаны и возвращает результаты расчета.
    """
    for item in dataset:
        # Формируем полное имя для проверки
        current_name = f"{item['name_slavic']} ({item['name_modern']})"
        
        if current_name == full_name:
            module = item.get("module")
            days = item.get("orbital_period", {}).get("days")
            
            # Если данные по дням или модулю отсутствуют или равны null (например, для Солнца)
            if module is None or days is None:
                return f"Для '{full_name}' отсутствуют необходимые числовые данные (module или days)."
            
            # Из-за возможной запятой в JSON (например, 4705515,75) приведем к float
            if isinstance(days, str):
                days = float(days.replace(",", "."))
            
            # Оптимизированный шаг: находим идеальное значение коэффициента
            target_coefficient = (days * 6) / module
            
            # Ищем самый близкий коэффициент из списка Юпаны
            # Метод min с lambda находит элемент с минимальной абсолютной разницей
            best_coef = min(YUPANA_COEFFICIENTS, key=lambda x: abs(x - target_coefficient))
            
            # Считаем итоговый расчетный период по формуле: 1/6 * module * найденный_коэффициент
            calculated_period = (1 / 6) * module * best_coef
            
            # Считаем разницу (погрешность) между реальным и расчетным периодом
            difference = abs(days - calculated_period)
            
            return {
                "planet": full_name,
                "module": module,
                "real_days": days,
                "target_coef_value": round(target_coefficient, 4),
                "best_yupana_coef": best_coef,
                "calculated_days": round(calculated_period, 4),
                "difference_days": round(difference, 4)
            }
            
    return f"Планета '{full_name}' не найдена в базе данных."



def update_planet_with_yupana_coef(full_name: str, file_path="planets.json"):
    """
    Загружает JSON-файл, находит планету по полному имени,
    подбирает лучшую комбинацию (коэффициент Юпаны * номинал карты n от 1 до 10),
    учитывая, что для каждого типа module (1, 11, 121, 1331, 14641) номиналы карт n не должны повторяться.
    Добавляет в JSON поля, включая относительную погрешность в %, и перезаписывает файл.
    """
    # 1. Загружаем актуальные данные из файла
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dataset = json.load(file)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{file_path}' не найден.")
        return False
    except json.JSONDecodeError:
        print(f"Ошибка: Файл '{file_path}' содержит некорректный JSON.")
        return False

    # Инициализируем списки (множества) использованных карт для каждого модуля
    used_multipliers = {
        "1": set(),
        "11": set(),
        "121": set(),
        "1331": set(),
        "14641": set()
    }

    # Сканируем весь датасет, чтобы наполнить списки уже использованных карт
    for item in dataset:
        item_mod = str(item.get("module"))
        item_card = item.get("card_multiplier")
        if item_mod in used_multipliers and item_card is not None:
            used_multipliers[item_mod].add(int(item_card))

    planet_found = False

    # 2. Ищем нужную планету и проводим вычисления
    for item in dataset:
        current_name = f"{item.get('name_slavic', '')} ({item.get('name_modern', '')})"
        
        if current_name == full_name:
            module = item.get("module")
            days_raw = item.get("orbital_period", {}).get("days")
            
            if module is None or days_raw is None:
                print(f"Для '{full_name}' отсутствуют числовые данные (module или days).")
                return False
            
            # Корректируем возможный формат с запятой в строку/число
            if isinstance(days_raw, str):
                days = float(days_raw.replace(",", "."))
            else:
                days = float(days_raw)
            
            # Определяем, какие карты уже заняты для текущего модуля
            mod_key = str(module)
            already_taken = used_multipliers.get(mod_key, set())

            # Инициализируем переменные для поиска минимума расхождения
            min_difference = float('inf')
            best_coef = None
            best_n = None
            best_calculated_period = None
            
            # Двойной перебор: по всем номиналам карт n (от 1 до 10)
            for n in range(1, 11):
                # Пропускаем карту, если она уже занята этим типом модуля
                if n in already_taken:
                    continue
                
                # Оптимизированный таргет для коэффициента Юпаны при текущем n
                target_coefficient = (days * 6) / module / n
                
                # Находим ближайший коэффициент Юпаны для данного n
                current_coef = min(YUPANA_COEFFICIENTS, key=lambda x: abs(x - target_coefficient))
                
                # Вычисляем расчетный период
                calculated_period = (1 / 6) * module * current_coef * n
                
                # Вычисляем абсолютное расхождение
                difference = abs(days - calculated_period)
                
                # Если нашли комбинацию с меньшей погрешностью, запоминаем её
                if difference < min_difference:
                    min_difference = difference
                    best_coef = current_coef
                    best_n = n
                    best_calculated_period = calculated_period
            
            # Если все карты от 1 до 10 для этого модуля уже заняты
            if best_n is None:
                print(f"Ошибка: Для модуля {module} закончились доступные карты (все 10 заняты).")
                return False

            # Расчет относительной погрешности в процентах
            if days != 0:
                error_percent = (min_difference / days) * 100
                error_percent_str = f"{error_percent:.2f}%"
            else:
                error_percent_str = "0.00%"

            # Записываем все вычисленные данные прямо в словарь этой планеты в JSON
            item["best_yupana_coef"] = best_coef
            item["card_multiplier"] = best_n  
            item["calculated_days"] = round(best_calculated_period, 4)
            item["difference_days"] = round(min_difference, 4)
            item["difference_percentage"] = error_percent_str  # Новый параметр
            
            planet_found = True
            print(f"Успешно рассчитано для '{full_name}':")
            print(f"  -> Модуль: {module}, Юпана: {best_coef}, Карта (n): {best_n}")
            print(f"  -> Расчетные дни: {item['calculated_days']}, Погрешность: {item['difference_days']} ({item['difference_percentage']})")
            break

    if not planet_found:
        print(f"Планета '{full_name}' не найдена в файле.")
        return False

    # 3. Сохраняем обновленный массив данных обратно в тот же файл
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(dataset, file, ensure_ascii=False, indent=2)
        print(f"Файл '{file_path}' успешно перезаписан на жесткий диск.")
        return True
    except Exception as e:
        print(f"Не удалось сохранить файл: {e}")
        return False

# === ДЕМОНСТРАЦИЯ РАБОТЫ СКРИПТА ===
if __name__ == "__main__":
    # Загружаем таблицу
    planets_list = load_planet_data()

    # Список тестов для проверки
    test_cases = [
        "Ярило-Солнце (Солнце)",
        "Хорсъ (Меркурий)",
        "Орей (Марс)",
        "Мидгардъ (Земля)",
        "Несуществующая (Планета)"
    ]

    print("Результаты работы функции:")
    print("-" * 40)
    for test_name in test_cases:
        days = get_orbital_period_by_name(test_name, planets_list)
        print(f"Вход: '{test_name}' -> Выход (дней): {days}")

    # Пример структуры данных на основе вашего файла (показаны ключевые элементы)
    raw_json_data = """[
      {
        "name_slavic": "Земля Догоды",
        "name_modern": "Седна",
        "module": 14641,
        "orbital_period": {"years": 12883.0, "days": "4705515,75"}
      },
      {
        "name_slavic": "Хорсъ",
        "name_modern": "Меркурий",
        "module": 1,
        "orbital_period": {"years": 0.241, "days": 88.0}
      },
      {
        "name_slavic": "Перунъ",
        "name_modern": "Юпитер",
        "module": 11,
        "orbital_period": {"years": 11.86, "days": 4331.86}
      }
    ]"""
    
    dataset = json.loads(raw_json_data)
    
    # Проверим работу функции на Земле Догоды (Седне)
    result_sedna = find_best_yupana_coefficient("Земля Догоды (Седна)", dataset)
    print("Результат для Седны:")
    print(json.dumps(result_sedna, indent=2, ensure_ascii=False))
    
    print("\n" + "="*40 + "\n")
    
    # Проверим работу функции на Меркурии
    result_mercury = find_best_yupana_coefficient("Хорсъ (Меркурий)", dataset)
    print("Результат для Меркурия:")
    print(json.dumps(result_mercury, indent=2, ensure_ascii=False))


    # Предположим, ваш файл называется 'planets.json' и лежит в той же папке
    file_name = "slavic_ariyan_lands.json"
    
    print("Запуск пакетного обновления коэффициентов Юпаны для всех планет...")
    print("=" * 60)
    
    # Шаг 1: Сначала просто прочитаем файл, чтобы узнать список всех планет
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            all_planets = json.load(file)
            
        # Формируем список полных имен для обработки
        planets_to_update = []
        for item in all_planets:
            slavic = item.get("name_slavic", "")
            modern = item.get("name_modern", "")
            if slavic or modern:  # Проверяем, что объект не пустой
                full_name = f"{slavic} ({modern})"
                planets_to_update.append(full_name)
                
        print( f"Обнаружено объектов для анализа: {len(planets_to_update)}" )
        print("-" * 60)
        
        # Шаг 2: Запускаем цикл обновления, вызывая готовую функцию для каждой планеты
        successful_updates = 0
        for planet_name in planets_to_update:
            # Вызываем вашу функцию. Она сама считает, пишет в структуру и сохраняет на диск
            if update_planet_with_yupana_coef(planet_name, file_path=file_name):
                successful_updates += 1
                
        print("=" * 60)
        print(f"Пакетная обработка завершена!")
        print(f"Успешно обработано и сохранено объектов: {successful_updates} из {len(planets_to_update)}")
        
    except FileNotFoundError:
        print(f"Ошибка автоматизации: Исходный файл '{file_name}' не найден на диске.")
    except json.JSONDecodeError:
        print(f"Ошибка автоматизации: Файл '{file_name}' содержит поврежденный JSON-код.")
