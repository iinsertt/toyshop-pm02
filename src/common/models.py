"""Модели данных приложения ToyShop.

Содержит простые классы-контейнеры (dataclasses), которые передаются между
модулями: товар, позиция корзины, покупатель и заказ.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Product:
    """Товар каталога.

    :param id: уникальный идентификатор товара (например, ``pr_001``).
    :param name: название товара.
    :param price: цена в рублях.
    :param stock: остаток на складе.
    :param description: текстовое описание.
    :param category: название категории, к которой относится товар.
    """

    id: str
    name: str
    price: float
    stock: int
    description: str
    category: str

    def to_dict(self) -> dict:
        """Преобразовать товар в словарь для записи в JSON-каталог.

        Категория не включается, так как в JSON товары сгруппированы внутри
        своей категории.
        """
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
        }


@dataclass
class CartItem:
    """Позиция корзины: товар и его количество."""

    product: Product
    quantity: int

    @property
    def subtotal(self) -> float:
        """Стоимость позиции с учётом количества (цена × количество)."""
        return self.product.price * self.quantity


@dataclass
class Customer:
    """Данные покупателя, оформляющего заказ."""

    surname: str
    name: str
    address: str
    phone: str
    email: str


@dataclass
class Order:
    """Оформленный заказ."""

    order_number: str
    customer: Customer
    items: List[CartItem] = field(default_factory=list)
    total: float = 0.0
    status: str = "новый"
    created_at: str = ""
