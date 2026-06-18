"""Модуль 5. Интеграция модулей и консольный интерфейс ToyShop.

Точка входа в приложение. Связывает каталог, корзину, оформление заказа и
админ-панель в единое консольное меню. Все необработанные ошибки логируются.
"""
import os
import sys

# Добавляем корень проекта в путь поиска модулей, чтобы работали импорты вида
# ``from src.common ...`` при запуске «python src/main.py».
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Принудительно переводим потоки на UTF-8, чтобы корректно выводить кириллицу и
# символ рубля «₽» на любой консоли Windows.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
try:
    sys.stdin.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from src.Module1_Catalog.catalog import Catalog  # noqa: E402
from src.Module2_Cart.cart import Cart  # noqa: E402
from src.Module3_Order.order import VALID_STATUSES, OrderService  # noqa: E402
from src.Module4_Admin.admin import Admin  # noqa: E402
from src.common.exceptions import (  # noqa: E402
    CatalogLoadError,
    ProductNotFoundError,
    ToyShopError,
    ValidationError,
)
from src.common.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


def ask(prompt_text: str = "") -> str:
    """Прочитать строку ввода пользователя.

    При достижении конца ввода (EOF) корректно завершает программу.
    """
    try:
        return input(prompt_text).strip()
    except EOFError:
        print("\nЗавершение работы.")
        raise SystemExit(0)


def ask_int(prompt_text: str, default: int = 1) -> int:
    """Прочитать целое число; при неверном вводе вернуть значение по умолчанию."""
    value = ask(prompt_text)
    try:
        return int(value)
    except ValueError:
        print(f"Неверное число, используется значение {default}.")
        return default


def print_products(products) -> None:
    """Вывести список товаров в виде таблицы."""
    if not products:
        print("  Товары не найдены.")
        return
    for product in products:
        print(
            f"  [{product.id}] {product.name} — {product.price:.2f} ₽ "
            f"| {product.category} | на складе: {product.stock}"
        )
        print(f"        {product.description}")


# ---------------------------------------------------------------------------- #
# Раздел «Каталог»
# ---------------------------------------------------------------------------- #
def catalog_menu(catalog: Catalog) -> None:
    """Меню работы с каталогом товаров."""
    while True:
        print("\n--- КАТАЛОГ ТОВАРОВ ---")
        print("1. Показать все товары")
        print("2. Поиск по названию")
        print("3. Фильтр по категории")
        print("4. Фильтр по цене")
        print("0. Назад")
        choice = ask("Выберите пункт: ")
        if choice == "1":
            print_products(catalog.get_all())
        elif choice == "2":
            query = ask("Введите название (или часть): ")
            print_products(catalog.search_by_name(query))
        elif choice == "3":
            print("Категории: Конструкторы, Куклы, Машинки, Настольные игры")
            category = ask("Введите категорию: ")
            print_products(catalog.filter_products(category=category))
        elif choice == "4":
            min_price = ask_int("Минимальная цена: ", 0)
            max_price = ask_int("Максимальная цена: ", 1000000)
            print_products(catalog.filter_products(min_price=min_price, max_price=max_price))
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню.")


# ---------------------------------------------------------------------------- #
# Раздел «Корзина»
# ---------------------------------------------------------------------------- #
def cart_menu(catalog: Catalog, cart: Cart) -> None:
    """Меню работы с корзиной."""
    while True:
        print("\n--- КОРЗИНА ---")
        print("1. Добавить товар")
        print("2. Показать корзину")
        print("3. Изменить количество")
        print("4. Удалить товар")
        print("5. Очистить корзину")
        print("0. Назад")
        choice = ask("Выберите пункт: ")
        if choice == "1":
            product_id = ask("Введите id товара (например, pr_001): ")
            try:
                product = catalog.get_by_id(product_id)
                quantity = ask_int("Количество: ", 1)
                cart.add(product, quantity)
                print(f"Добавлено: {product.name} x{quantity}")
            except ProductNotFoundError as error:
                print(f"Ошибка: {error}")
        elif choice == "2":
            show_cart(cart)
        elif choice == "3":
            product_id = ask("Введите id товара: ")
            quantity = ask_int("Новое количество: ", 1)
            try:
                cart.change_quantity(product_id, quantity)
                print("Количество изменено.")
            except ProductNotFoundError as error:
                print(f"Ошибка: {error}")
        elif choice == "4":
            product_id = ask("Введите id товара: ")
            try:
                cart.remove(product_id)
                print("Товар удалён из корзины.")
            except ProductNotFoundError as error:
                print(f"Ошибка: {error}")
        elif choice == "5":
            cart.clear()
            print("Корзина очищена.")
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню.")


def show_cart(cart: Cart) -> None:
    """Вывести содержимое корзины и итоговую сумму."""
    items = cart.get_items()
    if not items:
        print("  Корзина пуста.")
        return
    for item in items:
        print(
            f"  [{item.product.id}] {item.product.name} — "
            f"{item.product.price:.2f} ₽ x {item.quantity} = {item.subtotal:.2f} ₽"
        )
    print(f"  ИТОГО: {cart.total():.2f} ₽")


# ---------------------------------------------------------------------------- #
# Раздел «Оформление заказа»
# ---------------------------------------------------------------------------- #
def checkout_menu(cart: Cart, order_service: OrderService) -> None:
    """Оформление заказа: сбор данных, валидация, сохранение."""
    print("\n--- ОФОРМЛЕНИЕ ЗАКАЗА ---")
    items = cart.get_items()
    if not items:
        print("Корзина пуста — нечего оформлять.")
        return
    show_cart(cart)
    data = {
        "surname": ask("Фамилия: "),
        "name": ask("Имя: "),
        "address": ask("Адрес доставки: "),
        "phone": ask("Телефон: "),
        "email": ask("Email: "),
    }
    try:
        customer = order_service.validate_customer(data)
        order = order_service.save_order(customer, items, cart.total())
        cart.clear()
        print("\n✓ Заказ успешно оформлен!")
        print(f"  Номер заказа: {order.order_number}")
        print(f"  Сумма: {order.total:.2f} ₽")
        print(f"  Статус: {order.status}")
    except ValidationError as error:
        print(f"Ошибка в данных: {error}")
    except ToyShopError as error:
        print(f"Не удалось сохранить заказ: {error}")


# ---------------------------------------------------------------------------- #
# Раздел «Админ-панель»
# ---------------------------------------------------------------------------- #
def admin_menu(admin: Admin) -> None:
    """Меню административной панели."""
    while True:
        print("\n--- АДМИН-ПАНЕЛЬ ---")
        print("1. Список заказов")
        print("2. Изменить статус заказа")
        print("3. Добавить товар")
        print("4. Редактировать товар")
        print("5. Удалить товар")
        print("0. Назад")
        choice = ask("Выберите пункт: ")
        if choice == "1":
            list_orders(admin)
        elif choice == "2":
            order_number = ask("Номер заказа: ")
            print(f"Допустимые статусы: {', '.join(VALID_STATUSES)}")
            status = ask("Новый статус: ")
            try:
                admin.change_status(order_number, status)
                print("Статус изменён.")
            except ValidationError as error:
                print(f"Ошибка: {error}")
        elif choice == "3":
            category = ask("Категория: ")
            name = ask("Название: ")
            price = ask_int("Цена: ", 0)
            stock = ask_int("Остаток: ", 0)
            description = ask("Описание: ")
            try:
                product = admin.add_product(category, name, price, stock, description)
                print(f"Товар добавлен: [{product.id}] {product.name}")
            except ValidationError as error:
                print(f"Ошибка: {error}")
        elif choice == "4":
            product_id = ask("id товара: ")
            name = ask("Новое название (Enter — пропустить): ")
            fields = {}
            if name:
                fields["name"] = name
            new_price = ask("Новая цена (Enter — пропустить): ")
            if new_price:
                try:
                    fields["price"] = float(new_price)
                except ValueError:
                    print("Цена пропущена (неверный формат).")
            try:
                admin.edit_product(product_id, **fields)
                print("Товар обновлён.")
            except ProductNotFoundError as error:
                print(f"Ошибка: {error}")
        elif choice == "5":
            product_id = ask("id товара: ")
            try:
                admin.delete_product(product_id)
                print("Товар удалён.")
            except ProductNotFoundError as error:
                print(f"Ошибка: {error}")
        elif choice == "0":
            return
        else:
            print("Неизвестный пункт меню.")


def list_orders(admin: Admin) -> None:
    """Вывести список всех заказов."""
    orders = admin.list_orders()
    if not orders:
        print("  Заказов пока нет.")
        return
    for order in orders:
        print(
            f"  {order.order_number} | {order.customer.surname} {order.customer.name} "
            f"| {order.total:.2f} ₽ | {order.status} | {order.created_at}"
        )


# ---------------------------------------------------------------------------- #
# Главное меню
# ---------------------------------------------------------------------------- #
def main() -> None:
    """Запустить приложение ToyShop."""
    logger.info("Запуск приложения ToyShop")
    try:
        catalog = Catalog()
        catalog.load_products()
    except CatalogLoadError as error:
        print(f"Критическая ошибка: не удалось загрузить каталог ({error})")
        logger.error("Не удалось запустить приложение", exc_info=True)
        return

    cart = Cart()
    order_service = OrderService()
    admin = Admin(catalog, order_service)

    while True:
        print("\n==============================")
        print("   ToyShop — магазин игрушек")
        print("==============================")
        print("1. Каталог товаров")
        print("2. Корзина")
        print("3. Оформить заказ")
        print("4. Админ-панель")
        print("0. Выход")
        choice = ask("Выберите раздел: ")
        try:
            if choice == "1":
                catalog_menu(catalog)
            elif choice == "2":
                cart_menu(catalog, cart)
            elif choice == "3":
                checkout_menu(cart, order_service)
            elif choice == "4":
                admin_menu(admin)
            elif choice == "0":
                print("До свидания!")
                logger.info("Завершение работы приложения")
                return
            else:
                print("Неизвестный пункт меню.")
        except ToyShopError as error:
            print(f"Произошла ошибка: {error}")
            logger.error("Обработанная ошибка в меню", exc_info=True)
        except Exception as error:  # noqa: BLE001 - логируем любые непредвиденные ошибки
            print(f"Непредвиденная ошибка: {error}")
            logger.error("Непредвиденная ошибка", exc_info=True)


if __name__ == "__main__":
    main()
