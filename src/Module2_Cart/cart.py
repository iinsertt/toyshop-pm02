"""Модуль 2. Корзина.

Хранит выбранные покупателем товары в памяти сессии, позволяет добавлять,
удалять и изменять количество, рассчитывает общую сумму.
"""
from typing import List, Optional

from src.common.exceptions import ProductNotFoundError
from src.common.logger import get_logger
from src.common.models import CartItem, Product

logger = get_logger(__name__)


class Cart:
    """Корзина покупателя."""

    def __init__(self):
        """Создать пустую корзину."""
        self.items: List[CartItem] = []

    def _find_item(self, product_id: str) -> Optional[CartItem]:
        """Найти позицию корзины по идентификатору товара или вернуть None."""
        for item in self.items:
            if item.product.id == product_id:
                return item
        return None

    def add(self, product: Product, quantity: int = 1) -> None:
        """Добавить товар в корзину.

        Если товар уже есть в корзине, его количество увеличивается.

        :param product: добавляемый товар.
        :param quantity: количество (по умолчанию 1).
        """
        if quantity <= 0:
            quantity = 1
        existing = self._find_item(product.id)
        if existing is not None:
            existing.quantity += quantity
        else:
            self.items.append(CartItem(product, quantity))
        logger.info("В корзину добавлен товар %s (x%d)", product.id, quantity)

    def remove(self, product_id: str) -> None:
        """Удалить товар из корзины.

        :param product_id: идентификатор удаляемого товара.
        :raises ProductNotFoundError: если товара нет в корзине.
        """
        item = self._find_item(product_id)
        if item is None:
            raise ProductNotFoundError(f"Товар с id={product_id} отсутствует в корзине")
        self.items.remove(item)
        logger.info("Из корзины удалён товар %s", product_id)

    def change_quantity(self, product_id: str, quantity: int) -> None:
        """Изменить количество товара в корзине.

        Если новое количество меньше либо равно нулю, позиция удаляется.

        :param product_id: идентификатор товара.
        :param quantity: новое количество.
        :raises ProductNotFoundError: если товара нет в корзине.
        """
        item = self._find_item(product_id)
        if item is None:
            raise ProductNotFoundError(f"Товар с id={product_id} отсутствует в корзине")
        if quantity <= 0:
            self.items.remove(item)
            logger.info("Позиция %s удалена (количество <= 0)", product_id)
        else:
            item.quantity = quantity
            logger.info("Количество товара %s изменено на %d", product_id, quantity)

    def get_items(self) -> List[CartItem]:
        """Вернуть список позиций корзины."""
        return list(self.items)

    def total(self) -> float:
        """Рассчитать общую сумму заказа (сумма стоимости всех позиций)."""
        return sum(item.subtotal for item in self.items)

    def clear(self) -> None:
        """Очистить корзину."""
        self.items = []
        logger.info("Корзина очищена")
