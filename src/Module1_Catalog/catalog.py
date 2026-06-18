"""Модуль 1. Каталог товаров.

Отвечает за загрузку товаров из JSON-файла, отображение, поиск по названию и
фильтрацию по категории и цене.
"""
import json
import os
from typing import List, Optional

from src.common.exceptions import CatalogLoadError, ProductNotFoundError
from src.common.logger import get_logger
from src.common.models import Product

logger = get_logger(__name__)

# Путь к JSON-каталогу по умолчанию: <корень>/src/data/products.json
DEFAULT_CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "products.json",
)


class Catalog:
    """Каталог товаров магазина игрушек."""

    def __init__(self, json_path: Optional[str] = None):
        """Создать каталог.

        :param json_path: путь к JSON-файлу каталога. Если не задан,
            используется файл по умолчанию ``src/data/products.json``.
        """
        self.json_path = json_path or DEFAULT_CATALOG_PATH
        self.products: List[Product] = []

    def load_products(self) -> List[Product]:
        """Загрузить товары из JSON-файла в память.

        :return: список загруженных товаров.
        :raises CatalogLoadError: если файл не найден или имеет неверный формат.
        """
        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            products: List[Product] = []
            for category in data.get("categories", []):
                category_name = category["name"]
                for item in category.get("products", []):
                    products.append(
                        Product(
                            id=item["id"],
                            name=item["name"],
                            price=float(item["price"]),
                            stock=int(item["stock"]),
                            description=item.get("description", ""),
                            category=category_name,
                        )
                    )
            self.products = products
            logger.info("Каталог загружен: %d товаров из %s", len(products), self.json_path)
            return products
        except FileNotFoundError as error:
            logger.error("Файл каталога не найден: %s", self.json_path, exc_info=True)
            raise CatalogLoadError(f"Файл каталога не найден: {self.json_path}") from error
        except (json.JSONDecodeError, KeyError, ValueError) as error:
            logger.error("Неверный формат каталога: %s", self.json_path, exc_info=True)
            raise CatalogLoadError(f"Неверный формат каталога: {error}") from error

    def get_all(self) -> List[Product]:
        """Вернуть все загруженные товары."""
        return list(self.products)

    def search_by_name(self, query: str) -> List[Product]:
        """Найти товары, в названии которых встречается подстрока ``query``.

        Поиск регистронезависимый.

        :param query: искомая подстрока.
        :return: список подходящих товаров (может быть пустым).
        """
        normalized = query.strip().lower()
        # Возвращаем товары, в названии которых (в нижнем регистре)
        # встречается искомая подстрока.
        return [p for p in self.products if normalized in p.name.lower()]

    def filter_products(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Product]:
        """Отфильтровать товары по категории и/или диапазону цены.

        :param category: название категории (точное совпадение).
        :param min_price: минимальная цена включительно.
        :param max_price: максимальная цена включительно.
        :return: список товаров, удовлетворяющих всем заданным условиям.
        """
        result = self.products
        if category is not None:
            result = [p for p in result if p.category == category]
        if min_price is not None:
            result = [p for p in result if p.price >= min_price]
        if max_price is not None:
            result = [p for p in result if p.price <= max_price]
        return list(result)

    def get_by_id(self, product_id: str) -> Product:
        """Вернуть товар по идентификатору.

        :param product_id: идентификатор товара.
        :raises ProductNotFoundError: если товар не найден.
        """
        for product in self.products:
            if product.id == product_id:
                return product
        raise ProductNotFoundError(f"Товар с id={product_id} не найден")
