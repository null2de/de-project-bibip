from decimal import Decimal
from typing import TextIO

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.models_file = root_directory_path + '/models.txt'
        self.models_idx_file = root_directory_path + '/models_index.txt'
        self.cars_file = root_directory_path + '/cars.txt'
        self.cars_idx_file = root_directory_path + '/cars_index.txt'
        self.sales_file = root_directory_path + '/sales.txt'
        self.sales_idx_file = root_directory_path + '/sales_index.txt'

    def _row_read(self, input_file: TextIO, row_number: int) -> list:
        input_file.seek(row_number * 101)
        values = input_file.read(100).split(';')
        values[-1] = values[-1].rstrip()
        return values

    def _fk_check(self, idx_file_name: str, f_key: str):
        try:
            with open(idx_file_name, 'r', encoding='utf-8') as mf:
                idx_list = [
                    (line.split(';')[0], line.split(';')[1].rstrip())
                    for line in mf.readlines()
                ]
                if f_key not in (key for key, _ in idx_list):
                    raise Exception('Ошибка FKEY: Нет записи в родительской таблице')
        except FileNotFoundError:
            raise Exception('Ошибка FKEY: Родительская таблица не существует')

    def _add_idx(self, idx_file_name: str, item: Model | Car | Sale, idx: str) -> None:
        pr_key: str = item.index()

        with open(idx_file_name, 'a+', encoding='utf-8') as f:
            if not f.tell():
                f.write(pr_key + ';' + idx + '\n')
                return

            f.seek(0)
            idx_list: list[tuple[str, str]] = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]

            if pr_key in (key for key, _ in idx_list):
                raise Exception('Ошибка PKEY: Такой первичный ключ уже есть в таблице')

            if isinstance(item, Car):
                self._fk_check(self.models_idx_file, str(item.model))

            if isinstance(item, Sale):
                self._fk_check(self.cars_idx_file, item.car_vin)

            if pr_key > idx_list[-1][0]:
                output_row: str = pr_key + ';' + idx + '\n'
                f.write(output_row)

        with open(idx_file_name, 'w', encoding='utf-8') as f:
            idx_list.append((pr_key, idx))
            idx_list.sort()

            output_list = [key + ';' + idx + '\n' for key, idx in idx_list]
            f.writelines(output_list)

    def _idx_manager(
        self,
        idx_file_name: str,
        key: str,
        new_key: str | None = None,
        delete: bool = False,
    ) -> int:
        with open(idx_file_name, 'r+', encoding='utf-8') as f:

            idx_list = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]

            left = 0
            right = len(idx_list) - 1
            while left <= right:
                mid = (left + right) // 2
                if idx_list[mid][0] == key:
                    result = int(idx_list[mid][1])
                    if new_key is None and not delete:
                        return result
                    elif delete:
                        del idx_list[mid]
                    elif new_key is not None:
                        idx_list[mid] = (new_key, idx_list[mid][1])
                    f.seek(0)
                    if not idx_list:
                        f.truncate()
                    else:
                        idx_list.sort()
                        output_list = [key + ';' + idx + '\n' for key, idx in idx_list]
                        f.writelines(output_list)
                    return result
                if idx_list[mid][0] < key:
                    left = mid + 1
                else:
                    right = mid - 1

        raise Exception('Ошибка поиска записи в таблице индексов')

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        output_row: str = ';'.join([str(val) for val in model.model_dump().values()])

        with open(self.models_file, 'a', encoding='utf-8') as f:
            index = str(f.tell() // 101)
            self._add_idx(self.models_idx_file, model, index)
            f.write(output_row.ljust(100) + '\n')

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        output_row: str = ';'.join([str(val) for val in car.model_dump().values()])

        with open(self.cars_file, 'a', encoding='utf-8') as f:
            index = str(f.tell() // 101)
            self._add_idx(self.cars_idx_file, car, index)
            f.write(output_row.ljust(100) + '\n')
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        output_row: str = ';'.join([str(value) for value in sale.model_dump().values()])

        with open(self.sales_file, 'a', encoding='utf-8') as f:
            index = str(f.tell() // 101)
            self._add_idx(self.sales_idx_file, sale, index)
            f.write(output_row.ljust(100) + '\n')

        row_number: int = self._idx_manager(self.cars_idx_file, sale.car_vin)
        keys = list(Car.model_fields.keys())

        with open(self.cars_file, 'r+', encoding='utf-8') as f:
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
            rows_count = f.tell() // 101
            f.seek(0)

            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                if values[-1] != 'available':
                    continue
                car_list.append(Car(**dict(zip(keys, values))))

        # return sorted(car_list, key=lambda car: car.vin)
        return car_list

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        try:
            row_number: int = self._idx_manager(self.cars_idx_file, vin)
        except Exception:
            return None

        with open(self.cars_file, 'r', encoding='utf-8') as f:
            values: list = self._row_read(f, row_number)

        keys = list(Car.model_fields.keys())
        car = Car(**dict(zip(keys, values)))

        row_number = self._idx_manager(self.models_idx_file, str(car.model))

        with open(self.models_file, 'r', encoding='utf-8') as f:
            values = self._row_read(f, row_number)

        keys = list(Model.model_fields.keys())
        model = Model(**dict(zip(keys, values)))

        result = CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=None,
            sales_cost=None,
        )

        if car.status != CarStatus.sold:
            return result

        with open(self.sales_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            rows_count: int = f.tell() // 101
            f.seek(0)

            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                if values[1] == car.vin:
                    keys = list(Sale.model_fields.keys())
                    sale = Sale(**dict(zip(keys, values)))
                    result.sales_date = sale.sales_date
                    result.sales_cost = sale.cost
                    return result

        return None

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        row_number: int = self._idx_manager(self.cars_idx_file, vin, new_vin)
        keys = list(Car.model_fields.keys())

        with open(self.cars_file, 'r+', encoding='utf-8') as f:
            values = self._row_read(f, row_number)
            car = Car(**dict(zip(keys, values)))
            car.vin = new_vin
            output_row = ';'.join([str(value) for value in car.model_dump().values()])
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        return car

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        row_number: int = self._idx_manager(
            self.sales_idx_file, sales_number, delete=True
        )

        keys = list(Car.model_fields.keys())

        with open(self.sales_file, 'r+', encoding='utf-8') as f:
            values: list = self._row_read(f, row_number)
            output_row: str = ';'.join([''] * 4)
            f.seek(row_number * 101)
            f.write(output_row.ljust(100) + '\n')

        vin: str = values[1]
        row_number = self._idx_manager(self.cars_idx_file, vin)

        with open(self.cars_file, 'r+', encoding='utf-8') as f:
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

        with open(self.sales_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            rows_count = f.tell() // 101
            f.seek(0)

            for row_number in range(rows_count):
                values = self._row_read(f, row_number)
                if values:
                    sales.append((values[1], Decimal(values[-1])))
            print(sales)

        return None
