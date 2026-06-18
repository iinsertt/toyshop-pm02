"""Иерархия пользовательских исключений приложения ToyShop.

Все исключения наследуются от базового :class:`ToyShopError`, что позволяет
перехватывать любые ошибки предметной области одним блоком ``except ToyShopError``.
"""


class ToyShopError(Exception):
    """Базовое исключение для всех ошибок приложения ToyShop."""


class CatalogLoadError(ToyShopError):
    """Не удалось загрузить каталог товаров (нет файла или неверный формат JSON)."""


class ProductNotFoundError(ToyShopError):
    """Запрошенный товар не найден по идентификатору."""


class ValidationError(ToyShopError):
    """Введённые данные не прошли проверку (пустое поле, неверный формат)."""


class OrderSaveError(ToyShopError):
    """Не удалось сохранить заказ в базу данных."""
