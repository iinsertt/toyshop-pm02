"""Юнит-тесты Модуля 4 «Административная панель» (тест-пакет «Админка»).

Тесты работают на копии JSON-каталога во временной папке, чтобы не изменять
рабочий файл данных.
"""
import os
import shutil

from src.Module1_Catalog.catalog import Catalog
from src.Module3_Order.order import OrderService
from src.Module4_Admin.admin import Admin
from src.common.models import CartItem, Product


def _setup(tmp_path):
    """Подготовить админку с копией каталога и временной БД."""
    source_json = os.path.join("src", "data", "products.json")
    catalog_copy = tmp_path / "products.json"
    shutil.copy(source_json, catalog_copy)
    catalog = Catalog(str(catalog_copy))
    catalog.load_products()
    service = OrderService(str(tmp_path / "orders.db"))
    return Admin(catalog, service), catalog, service


def test_add_product(tmp_path):
    """TC-ADM-01: добавление товара увеличивает каталог."""
    admin, catalog, _ = _setup(tmp_path)
    before = len(catalog.get_all())
    admin.add_product("Машинки", "Тестовая машинка", 299.0, 7, "описание")
    assert len(catalog.get_all()) == before + 1


def test_change_status(tmp_path):
    """TC-ADM-02: изменение статуса заказа сохраняется в БД."""
    admin, _, service = _setup(tmp_path)
    customer = service.validate_customer(
        {
            "surname": "Подмарьков",
            "name": "Роман",
            "address": "г. Москва",
            "phone": "+79990001122",
            "email": "roman@example.ru",
        }
    )
    item = CartItem(Product("pr_005", "Кукла", 100.0, 1, "описание", "Куклы"), 1)
    order = service.save_order(customer, [item], 100.0)
    admin.change_status(order.order_number, "доставлен")
    assert service.get_order(order.order_number).status == "доставлен"
