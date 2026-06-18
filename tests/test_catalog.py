"""Юнит-тесты Модуля 1 «Каталог товаров» (тест-пакет «Каталог»)."""
from src.Module1_Catalog.catalog import Catalog


def test_load_products():
    """TC-CAT-01: загрузка данных из JSON возвращает все товары."""
    catalog = Catalog()
    products = catalog.load_products()
    assert len(products) >= 12


def test_search_by_name():
    """TC-CAT-02: поиск по названию находит товары без учёта регистра."""
    catalog = Catalog()
    catalog.load_products()
    result = catalog.search_by_name("кукла")
    assert len(result) >= 1
    assert all("кукла" in product.name.lower() for product in result)


def test_filter_by_category():
    """TC-CAT-03: фильтрация по категории возвращает только товары этой категории."""
    catalog = Catalog()
    catalog.load_products()
    result = catalog.filter_products(category="Машинки")
    assert len(result) >= 1
    assert all(product.category == "Машинки" for product in result)
