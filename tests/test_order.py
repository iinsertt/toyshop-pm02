"""Юнит-тесты Модуля 3 «Оформление заказа» (тест-пакет «Заказ»)."""
import pytest

from src.Module3_Order.order import OrderService
from src.common.exceptions import ValidationError
from src.common.models import CartItem, Product

GOOD_CUSTOMER = {
    "surname": "Иванов",
    "name": "Иван",
    "address": "г. Москва, ул. Мира, д. 1",
    "phone": "+79991234567",
    "email": "ivanov@example.ru",
}


def test_validate_rejects_bad_phone():
    """TC-ORD-01: валидация отклоняет неверный формат телефона."""
    service = OrderService(":memory:")
    bad_data = dict(GOOD_CUSTOMER, phone="123")
    with pytest.raises(ValidationError):
        service.validate_customer(bad_data)


def test_save_order(tmp_path):
    """TC-ORD-02: заказ сохраняется в БД и читается обратно."""
    service = OrderService(str(tmp_path / "orders.db"))
    customer = service.validate_customer(GOOD_CUSTOMER)
    item = CartItem(Product("pr_005", "Кукла Barbie", 500.0, 5, "описание", "Куклы"), 2)
    order = service.save_order(customer, [item], 1000.0)
    assert order.order_number.startswith("ORD-")
    saved = service.get_order(order.order_number)
    assert saved is not None
    assert saved.total == 1000.0
    assert len(saved.items) == 1
