"""Интеграционные тесты ToyShop: проверка взаимодействия модулей.

Проверяются три ключевых потока данных между модулями:
- каталог → корзина (передача товара при добавлении);
- корзина → оформление заказа (передача позиций и суммы);
- админ-панель → каталог (обновление каталога видно при поиске).
"""
import os
import shutil

from src.Module1_Catalog.catalog import Catalog
from src.Module2_Cart.cart import Cart
from src.Module3_Order.order import OrderService
from src.Module4_Admin.admin import Admin


def test_catalog_to_cart():
    """TC-INT-01: товар из каталога корректно попадает в корзину."""
    catalog = Catalog()
    catalog.load_products()
    product = catalog.get_all()[0]
    cart = Cart()
    cart.add(product, 3)
    items = cart.get_items()
    assert len(items) == 1
    assert items[0].product.id == product.id
    assert cart.total() == product.price * 3


def test_cart_to_order(tmp_path):
    """TC-INT-02: позиции и сумма корзины передаются в заказ и сохраняются."""
    catalog = Catalog()
    catalog.load_products()
    cart = Cart()
    cart.add(catalog.get_all()[0], 2)
    cart.add(catalog.get_all()[1], 1)
    service = OrderService(str(tmp_path / "orders.db"))
    customer = service.validate_customer(
        {
            "surname": "Подмарьков",
            "name": "Роман",
            "address": "г. Москва",
            "phone": "+79991234567",
            "email": "roman@example.ru",
        }
    )
    order = service.save_order(customer, cart.get_items(), cart.total())
    saved = service.get_order(order.order_number)
    assert saved is not None
    assert saved.total == cart.total()
    assert len(saved.items) == 2


def test_admin_to_catalog(tmp_path):
    """TC-INT-03: добавленный через админку товар находится в каталоге."""
    source_json = os.path.join("src", "data", "products.json")
    catalog_copy = tmp_path / "products.json"
    shutil.copy(source_json, catalog_copy)
    catalog = Catalog(str(catalog_copy))
    catalog.load_products()
    service = OrderService(str(tmp_path / "orders.db"))
    admin = Admin(catalog, service)

    admin.add_product("Настольные игры", "Шахматы Гроссмейстер", 1599.0, 5, "Деревянные")
    found = catalog.search_by_name("Шахматы")
    assert len(found) == 1
    assert found[0].category == "Настольные игры"
