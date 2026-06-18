"""Модуль 4. Административная панель.

Позволяет администратору просматривать заказы и менять их статус, а также
управлять товарами каталога (добавление, редактирование, удаление). Изменения
товаров сохраняются в JSON-файл каталога.
"""
import json
from typing import List

from src.Module1_Catalog.catalog import Catalog
from src.Module3_Order.order import VALID_STATUSES, OrderService
from src.common.exceptions import ProductNotFoundError, ValidationError
from src.common.logger import get_logger
from src.common.models import Order, Product

logger = get_logger(__name__)


class Admin:
    """Административная панель магазина."""

    def __init__(self, catalog: Catalog, order_service: OrderService):
        """Создать админ-панель.

        :param catalog: каталог товаров (для CRUD и перечитывания).
        :param order_service: сервис заказов (для просмотра и смены статуса).
        """
        self.catalog = catalog
        self.order_service = order_service

    # ------------------------------------------------------------------ #
    # Работа с заказами
    # ------------------------------------------------------------------ #
    def list_orders(self) -> List[Order]:
        """Вернуть список всех заказов."""
        return self.order_service.list_orders()

    def change_status(self, order_number: str, status: str) -> None:
        """Изменить статус заказа.

        :param status: один из допустимых статусов (``VALID_STATUSES``).
        :raises ValidationError: если статус недопустим или заказ не найден.
        """
        if status not in VALID_STATUSES:
            raise ValidationError(
                f"Недопустимый статус «{status}». Допустимо: {', '.join(VALID_STATUSES)}"
            )
        self.order_service.update_status(order_number, status)

    # ------------------------------------------------------------------ #
    # Работа с товарами (CRUD в JSON-каталоге)
    # ------------------------------------------------------------------ #
    def _read_catalog_data(self) -> dict:
        """Прочитать сырые данные каталога из JSON-файла."""
        with open(self.catalog.json_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write_catalog_data(self, data: dict) -> None:
        """Записать данные каталога обратно в JSON-файл и перечитать каталог."""
        with open(self.catalog.json_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        self.catalog.load_products()

    def _generate_product_id(self, data: dict) -> str:
        """Сгенерировать новый идентификатор товара формата ``pr_NNN``."""
        max_number = 0
        for category in data["categories"]:
            for product in category["products"]:
                try:
                    number = int(product["id"].split("_")[1])
                    max_number = max(max_number, number)
                except (IndexError, ValueError):
                    continue
        return f"pr_{max_number + 1:03d}"

    def add_product(
        self, category: str, name: str, price: float, stock: int, description: str
    ) -> Product:
        """Добавить новый товар в указанную категорию.

        :raises ValidationError: если категория не найдена.
        """
        data = self._read_catalog_data()
        target = None
        for category_block in data["categories"]:
            if category_block["name"] == category:
                target = category_block
                break
        if target is None:
            raise ValidationError(f"Категория «{category}» не найдена")

        product_id = self._generate_product_id(data)
        new_product = {
            "id": product_id,
            "name": name,
            "price": float(price),
            "stock": int(stock),
            "description": description,
        }
        target["products"].append(new_product)
        self._write_catalog_data(data)
        logger.info("Добавлен товар %s «%s» в категорию «%s»", product_id, name, category)
        return Product(product_id, name, float(price), int(stock), description, category)

    def edit_product(self, product_id: str, **fields) -> None:
        """Изменить поля существующего товара.

        Допустимые поля: name, price, stock, description.

        :raises ProductNotFoundError: если товар не найден.
        """
        allowed = {"name", "price", "stock", "description"}
        data = self._read_catalog_data()
        for category in data["categories"]:
            for product in category["products"]:
                if product["id"] == product_id:
                    for key, value in fields.items():
                        if key in allowed:
                            product[key] = value
                    self._write_catalog_data(data)
                    logger.info("Товар %s отредактирован: %s", product_id, fields)
                    return
        raise ProductNotFoundError(f"Товар с id={product_id} не найден")

    def delete_product(self, product_id: str) -> None:
        """Удалить товар из каталога.

        :raises ProductNotFoundError: если товар не найден.
        """
        data = self._read_catalog_data()
        for category in data["categories"]:
            products = category["products"]
            for index, product in enumerate(products):
                if product["id"] == product_id:
                    products.pop(index)
                    self._write_catalog_data(data)
                    logger.info("Товар %s удалён", product_id)
                    return
        raise ProductNotFoundError(f"Товар с id={product_id} не найден")
