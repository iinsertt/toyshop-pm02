"""Юнит-тесты Модуля 2 «Корзина» (тест-пакет «Корзина»)."""
from src.Module2_Cart.cart import Cart
from src.common.models import Product


def _make_product(product_id="pr_001", price=100.0):
    """Вспомогательная функция: создать тестовый товар."""
    return Product(product_id, "Тестовый товар", price, 10, "описание", "Куклы")


def test_add_product():
    """TC-CART-01: добавление товара увеличивает корзину и сумму."""
    cart = Cart()
    cart.add(_make_product(), 2)
    assert len(cart.get_items()) == 1
    assert cart.total() == 200.0


def test_remove_product():
    """TC-CART-02: удаление товара очищает позицию из корзины."""
    cart = Cart()
    cart.add(_make_product())
    cart.remove("pr_001")
    assert cart.get_items() == []


def test_change_quantity():
    """TC-CART-03: изменение количества пересчитывает сумму."""
    cart = Cart()
    cart.add(_make_product(), 1)
    cart.change_quantity("pr_001", 5)
    assert cart.total() == 500.0
