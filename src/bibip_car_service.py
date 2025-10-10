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

    def _get_row_number(self, idx_file_name: str, key: str) -> int:
        with open(idx_file_name, 'r', encoding='utf-8') as f:
            idx_list = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]
        left = 0
        right = len(idx_list) - 1
        while left <= right:
            mid = (left + right) // 2
            if idx_list[mid][0] == key:
                return int(idx_list[mid][1])
            if idx_list[mid][0] < key:
                left = mid + 1
            else:
                right = mid - 1
        raise Exception('Ошибка поиска записи в таблице cars')

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

    def _add_idx(self, idx_file_name: str, item: Model | Car | Sale) -> None:
        pr_key: str | int = item.index()

        with open(idx_file_name, 'a+', encoding='utf-8') as f:
            if not f.tell():
                f.write(str(pr_key) + ';' + '1' + '\n')
                return

            f.seek(0)
            idx_list: list[tuple[int | str, str]] = [
                (line.split(';')[0], line.split(';')[1].rstrip())
                for line in f.readlines()
            ]

            if pr_key in (key for key, _ in idx_list):
                raise Exception('Ошибка PKEY: Такой первичный ключ уже есть в таблице')

            if isinstance(item, Car):
                self._fk_check(self.models_idx_file, str(item.model))

            if isinstance(item, Sale):
                self._fk_check(self.cars_idx_file, item.car_vin)

            if isinstance(item, Model):
                idx_list = [(int(key), idx) for key, idx in idx_list]
                pr_key = int(pr_key)

            if pr_key > idx_list[-1][0]:  # type: ignore
                line: str = str(pr_key) + ';' + str(len(idx_list) + 1) + '\n'
                f.write(line)

        with open(idx_file_name, 'w', encoding='utf-8') as f:
            idx_list.append((pr_key, str(len(idx_list) + 1)))
            idx_list.sort()

            output_list = [str(key) + ';' + idx + '\n' for key, idx in idx_list]
            f.writelines(output_list)

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        line: str = ';'.join([str(value) for value in model.model_dump().values()])

        self._add_idx(self.models_idx_file, model)

        with open(self.models_file, 'a', encoding='utf-8') as f:
            f.write(line.ljust(100) + '\n')

        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        line: str = ';'.join([str(value) for value in car.model_dump().values()])

        self._add_idx(self.cars_idx_file, car)

        with open(self.cars_file, 'a', encoding='utf-8') as f:
            f.write(line.ljust(100) + '\n')

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        line: str = ';'.join([str(value) for value in sale.model_dump().values()])

        self._add_idx(self.sales_idx_file, sale)

        with open(self.sales_file, 'a', encoding='utf-8') as f:
            f.write(line.ljust(100) + '\n')

        row_num = self._get_row_number(self.cars_idx_file, sale.car_vin)

        with open(self.cars_file, '+r', encoding='utf-8') as f:
            f.seek((row_num - 1) * 101)
            keys = list(Car.model_fields.keys())
            values = f.read(100).split(';')
            values[-1] = values[-1].rstrip()
            car = Car(**dict(zip(keys, values)))  # type: ignore
            car.status = CarStatus.sold
            line = ';'.join([str(value) for value in car.model_dump().values()])
            f.seek((row_num - 1) * 101)
            f.write(line.ljust(100) + '\n')

        return car

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        raise NotImplementedError

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        raise NotImplementedError

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        raise NotImplementedError

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        raise NotImplementedError

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        raise NotImplementedError
