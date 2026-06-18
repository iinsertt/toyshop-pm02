"""Временный дымовой тест общих моделей (удаляется при финализации)."""
from src.common.models import Product, CartItem, Customer, Order


def test_cartitem_subtotal():
    product = Product("pr_001", "Кукла", 500.0, 5, "описание", "Куклы")
    item = CartItem(product, 3)
    assert item.subtotal == 1500.0


def test_product_to_dict():
    product = Product("pr_001", "Кукла", 500.0, 5, "описание", "Куклы")
    data = product.to_dict()
    assert data == {
        "id": "pr_001",
        "name": "Кукла",
        "price": 500.0,
        "stock": 5,
        "description": "описание",
    }


def test_order_defaults():
    cust = Customer("Иванов", "Иван", "адрес", "+79991234567", "a@b.ru")
    order = Order("ORD-20260618-0001", cust)
    assert order.status == "новый" and order.items == []
