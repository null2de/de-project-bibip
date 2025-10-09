from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:

        path: str = self.root_directory_path
        line: str = ';'.join([str(value) for value in model.model_dump().values()])

        with open(path + '/models.txt', 'a', encoding='utf-8') as f:
            f.write(line.ljust(99) + '\n')

        with open(path + '/models_index.txt', 'a+', encoding='utf-8') as f:
            if not f.tell():
                f.write(str(model.id) + ';' + '1' + '\n')
                return model
            f.seek(0)
            raw_lines = map(lambda s: s.split(';'), f.readlines())
            idx_lst = [(int(key), int(idx)) for key, idx in raw_lines]
            if model.id >= idx_lst[-1][0]:
                f.write(str(model.id) + ';' + str(len(idx_lst) + 1) + '\n')
                return model

        with open(path + '/models_index.txt', 'w', encoding='utf-8') as f:
            idx_lst.append((model.id, len(idx_lst) + 1))
            idx_lst.sort()
            to_write = map(lambda tup: str(tup[0]) + ';' + str(tup[1]) + '\n', idx_lst)
            f.writelines(to_write)
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        line: str = ';'.join([str(value) for value in car.model_dump().values()])
        with open(self.root_directory_path + '/cars.txt', 'a', encoding='utf-8') as f:
            f.write(line.ljust(99) + '\n')
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        raise NotImplementedError

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
