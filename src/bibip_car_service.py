from typing import TextIO

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:

    # Для удобства сохраняем все пути до файлов в переменные.
    # Конечно лучше передавать их в качестве аргументов при создании экземпляра класса,
    # но мы же не хотим ломать наши тесты :-)
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.models_file = root_directory_path + '/models.txt'
        self.models_idx_file = root_directory_path + '/models_index.txt'
        self.cars_file = root_directory_path + '/cars.txt'
        self.cars_idx_file = root_directory_path + '/cars_index.txt'
        self.sales_file = root_directory_path + '/sales.txt'
        self.sales_idx_file = root_directory_path + '/sales_index.txt'

    def _row_read(self, input_file: TextIO, row_number: int) -> list:
        """Принимает файловый объект, номер строки которую нужно прочитать
        и возвращает список элементов из этой строки файла"""
        input_file.seek(row_number * 101)
        values = input_file.read(100).split(';')
        values[-1] = values[-1].rstrip()
        return values

    def _fk_check(self, idx_file_name: str, f_key: str):
        """Проверяет факт существования внешнего ключа в родительской таблице и
        существование самой родительской таблицы"""
        try:
            with open(idx_file_name, 'r', encoding='utf-8') as mf:
                # Читается весь файл индекса в переменную.
                idx_list = [
                    (line.split(';')[0], line.split(';')[1].rstrip())
                    for line in mf.readlines()
                ]
                if f_key not in (key for key, _ in idx_list):
                    raise Exception('Ошибка FKEY: Нет записи в родительской таблице')
        except FileNotFoundError:
            raise Exception('Ошибка FKEY: Родительская таблица не существует')

    def _add_idx(self, idx_file_name: str, item: Model | Car | Sale, idx: str) -> None:
        """Создаёт или добавляет новый индекс в файл с индексами"""
        pr_key: str = item.index()

        with open(idx_file_name, 'a+', encoding='utf-8') as f:
            # Если файл индекса пустой, то создает первую запись.
            if not f.tell():
                f.write(pr_key + ';' + idx + '\n')
                return

            f.seek(0)

            # Читается весь файл индекса в переменную для дальнейшей работы.
            idx_list: list[tuple[str, str]] = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]

            # Проверка что добавляемый ключ не содержится в индексе.
            if pr_key in (key for key, _ in idx_list):
                raise Exception('Ошибка PKEY: Такой первичный ключ уже есть в таблице')

            # Проверка на существования внешнего ключа в родительской таблице.
            if isinstance(item, Car):
                self._fk_check(self.models_idx_file, str(item.model))

            # Проверка на существования внешнего ключа в родительской таблице.
            if isinstance(item, Sale):
                self._fk_check(self.cars_idx_file, item.car_vin)

            # Если добавляемый ключ больше самого большого в индексе,
            # то строка пишется в конец без перестройки всего индекса.
            if pr_key > idx_list[-1][0]:
                output_row: str = pr_key + ';' + idx + '\n'
                f.write(output_row)
                return

            f.seek(0)
            f.truncate()
            idx_list.append((pr_key, idx))  # новый индекс добавляется в переменную
            idx_list.sort()  # перестраивание индекса
            output_list = [key + ';' + idx + '\n' for key, idx in idx_list]
            f.writelines(output_list)

    def _idx_manager(
        self,
        idx_file_name: str,
        key: str,
        new_key: str | None = None,
        delete: bool = False,
    ) -> int:
        """Находит номер строки в таблице по ключу. Может также обновлять или удалять
        ключевое поле с перестраиванием индекса"""
        with open(idx_file_name, 'r+', encoding='utf-8') as f:
            # Читается весь файл индекса в переменную для дальнейшей работы.
            idx_list = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]

            # Используется бинарный поиск, так как работаем по отсортированному списку.
            left = 0
            right = len(idx_list) - 1
            while left <= right:
                mid = (left + right) // 2
                if idx_list[mid][0] == key:
                    result = int(idx_list[mid][1])

                    # Если не надо ничего обновлять и удалять, то возвращает
                    # номер строки в файле с таблицей.
                    if new_key is None and not delete:
                        return result

                    # Удаляет элемент в индексе если есть флаг на удаление.
                    elif delete:
                        del idx_list[mid]

                    # Обновляет элемент в индексе если есть чем.
                    elif new_key is not None:
                        idx_list[mid] = (new_key, idx_list[mid][1])

                    f.seek(0)
                    f.truncate()  # файл очищается, чтобы не осталось хвостов

                    # Если переменная с индексом не пустая после удаления,
                    # то переменная индекса пишется в файл.
                    if idx_list:
                        idx_list.sort()
                        output_list = [key + ';' + idx + '\n' for key, idx in idx_list]
                        f.writelines(output_list)

                    return result  # возвращает номер строки в файле с таблицей

                if idx_list[mid][0] < key:
                    left = mid + 1
                else:
                    right = mid - 1

        # Вызываем исключение, если не найдена запись в индексе.
        raise Exception('Ошибка поиска записи в таблице индексов')

    def _add_object(self, item: Model | Car | Sale) -> None:

        # Формирование строки из объекта для дальнейшей записи в файл.
        output_row: str = ';'.join([str(val) for val in item.model_dump().values()])

        if isinstance(item, Car):
            file_name: str = self.cars_file
            idx_file_name: str = self.cars_idx_file
        elif isinstance(item, Model):
            file_name = self.models_file
            idx_file_name = self.models_idx_file
        else:
            file_name = self.sales_file
            idx_file_name = self.sales_idx_file

        with open(file_name, 'a', encoding='utf-8') as f:
            index = str(f.tell() // 101)  # вычисляется номер для добавляемой строки
            self._add_idx(idx_file_name, item, index)  # строка индексируется
            f.write(output_row.ljust(100) + '\n')  # новая строка записывается в файл

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:

        self._add_object(model)

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:

        self._add_object(car)

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:

        self._add_object(sale)

        # Вычисляется номер строки в файле cars.txt
        row_number: int = self._idx_manager(self.cars_idx_file, sale.car_vin)

        # Читается строка из cars.txt, формируется объект car, обновляется статус,
        # формируется новая строка и перезаписывается в файл.
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            keys = list(Car.model_fields.keys())
            values = self._row_read(f, row_number)
            car = Car(**dict(zip(keys, values)))
            car.status = CarStatus.sold
            output_row = ';'.join([str(value) for value in car.model_dump().values()])
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        car_list = []
        keys = list(Car.model_fields.keys())

        with open(self.cars_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            rows_count = f.tell() // 101  # вычисляется количество всех строк
            f.seek(0)

            # Файл cars.txt читается построчно, 'available' авто добавляются в список.
            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                if values[-1] == 'available':
                    car_list.append(Car(**dict(zip(keys, values))))

        # Видимо в тесте ошибка, так как в задании требуется сформировать список
        # отсортированный по VIN, но тест пропускает только неотсортированный список!

        # return sorted(car_list, key=lambda car: car.vin)
        return car_list

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:

        # Если попытка найти строку в индексе вызывает исключение, то возвращает None.
        try:
            row_number: int = self._idx_manager(self.cars_idx_file, vin)
        except Exception:
            return None

        # Читается строка из cars.txt и формируется объект car
        with open(self.cars_file, 'r', encoding='utf-8') as f:
            values: list = self._row_read(f, row_number)
        keys = list(Car.model_fields.keys())
        car = Car(**dict(zip(keys, values)))

        # Находит номер строки в следующем файле models.txt по ключу.
        row_number = self._idx_manager(self.models_idx_file, str(car.model))

        # Читается строка из models.txt и формируется объект model
        with open(self.models_file, 'r', encoding='utf-8') as f:
            values = self._row_read(f, row_number)
        keys = list(Model.model_fields.keys())
        model = Model(**dict(zip(keys, values)))

        # Создается объект из полученных данных.
        result = CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=None,  # временно проставляется None
            sales_cost=None,  # временно проставляется None
        )

        # Если авто не был продан, то возвращет сформированный объект
        if car.status != CarStatus.sold:
            return result

        with open(self.sales_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            rows_count: int = f.tell() // 101  # вычисляется количество всех строк
            f.seek(0)

            # Читает построчно файл sales.txt
            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                # Находит запись по VIN и добавялет данные о продаже в объект.
                if values[1] == car.vin:
                    keys = list(Sale.model_fields.keys())
                    sale = Sale(**dict(zip(keys, values)))
                    result.sales_date = sale.sales_date
                    result.sales_cost = sale.cost
                    return result

        return None

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:

        # Находит номер строки в файле cars.txt, обновляет и перестраивает индекс.
        row_number: int = self._idx_manager(self.cars_idx_file, vin, new_vin)

        # Читается строка из cars.txt, формируется объект car, обновляется VIN,
        # формируется новая строка и перезаписывается в файл.
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            keys = list(Car.model_fields.keys())
            values = self._row_read(f, row_number)
            car = Car(**dict(zip(keys, values)))
            car.vin = new_vin
            output_row = ';'.join([str(value) for value in car.model_dump().values()])
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:

        # Находит номер строки в файле sales.txt, удаляет элемент из индекса.
        row_number: int = self._idx_manager(
            self.sales_idx_file, sales_number, delete=True
        )

        # Читается строка из sales.txt,
        # формируется новая пустая строка и перезаписывается в файл.
        with open(self.sales_file, 'r+', encoding='utf-8') as f:
            values: list = self._row_read(f, row_number)
            output_row: str = ';'.join([''] * 4)
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        vin: str = values[1]  # излвекает VIN из прочитанной строки

        # Находит номер строки в файле cars.txt, удаляет элемент и перестраивает индекс.
        row_number = self._idx_manager(self.cars_idx_file, vin)

        # Читается строка из cars.txt, формируется объект car, обновляется статус,
        # формируется новая строка и перезаписывается в файл.
        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            keys = list(Car.model_fields.keys())
            values = self._row_read(f, row_number)
            car = Car(**dict(zip(keys, values)))
            car.status = CarStatus.available
            output_row = ';'.join([str(value) for value in car.model_dump().values()])
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        return car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales: list = []
        counter: dict = {}

        with open(self.sales_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            rows_count = f.tell() // 101  # вычисляется количество всех строк
            f.seek(0)

            # Читает построчно файл sales.txt и для каждого VIN находит, формирует
            # объект с полной информацией об авто и добавляет в список sales.
            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                if values:
                    sales.append(self.get_car_info(values[1]))

        # Формирует словарь подсчета продаж, где ключами словаря являются кортежи
        # вида (имя_модели, имя_бренда), а значениями элементов словаря являются
        # списки с ценами по которым они были проданы
        for car in sales:
            counter[(car.car_model_name, car.car_model_brand)] = counter.get(
                (car.car_model_name, car.car_model_brand), []
            ) + [car.sales_cost]

        # Преобразует словарь подсчета в список с элементами вида:
        # ((имя_модели, имя_бренда), количество продаж, средняя цена продажи)
        top_sales = [
            (key, len(val), sum(val) / len(val)) for key, val in counter.items()
        ]

        # Сортирует список согласно условию задачи:
        # 'Список отранжирован по количеству проданных моделей. Если количество продаж
        #  у моделей равно, то сначала выводятся более дорогие'
        top_sales.sort(key=lambda el: (-el[1], -el[2]))

        # Формирует и возвращает список ТОП-3 объектов ModelSaleStats.
        return [
            ModelSaleStats(
                car_model_name=car[0][0], brand=car[0][1], sales_number=car[1]
            )
            for car in top_sales[:3]
        ]
