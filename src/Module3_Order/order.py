"""Модуль 3. Оформление заказа.

Собирает и проверяет данные покупателя, генерирует уникальный номер заказа,
сохраняет заказ в базу данных SQLite и позволяет читать/обновлять заказы.
"""
import os
import re
import sqlite3
from datetime import datetime
from typing import List, Optional

from src.common.exceptions import OrderSaveError, ValidationError
from src.common.logger import get_logger
from src.common.models import CartItem, Customer, Order, Product

logger = get_logger(__name__)

# Путь к базе данных по умолчанию: <корень>/orders.db
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "orders.db",
)

# Допустимые статусы заказа.
VALID_STATUSES = ("новый", "в обработке", "доставлен", "отменён")

# Регулярные выражения для валидации.
PHONE_PATTERN = re.compile(r"^\+?\d[\d\s\-()]{9,}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Обязательные поля покупателя.
REQUIRED_FIELDS = ("surname", "name", "address", "phone", "email")

# Список столбцов таблицы orders в порядке, ожидаемом методом _row_to_order.
# Вынесён в константу, чтобы не дублировать его в нескольких SQL-запросах.
ORDER_COLUMNS = "order_number, surname, name, address, phone, email, total, status, created_at"


class OrderService:
    """Сервис оформления заказов с хранением в SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        """Создать сервис и подготовить таблицы базы данных.

        :param db_path: путь к файлу БД. ``":memory:"`` создаёт БД в памяти.
            Если не задан — используется ``orders.db`` в корне проекта.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.connection = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        """Создать таблицы заказов и позиций заказа, если их ещё нет."""
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_number TEXT PRIMARY KEY,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_number) REFERENCES orders(order_number)
            );
            """
        )
        self.connection.commit()

    def validate_customer(self, data: dict) -> Customer:
        """Проверить данные покупателя и вернуть объект :class:`Customer`.

        :param data: словарь с ключами surname, name, address, phone, email.
        :raises ValidationError: если поле пустое или телефон/email неверного формата.
        """
        for field_name in REQUIRED_FIELDS:
            value = str(data.get(field_name, "")).strip()
            if not value:
                raise ValidationError(f"Поле «{field_name}» не должно быть пустым")

        phone = str(data["phone"]).strip()
        if not PHONE_PATTERN.match(phone):
            raise ValidationError(f"Неверный формат телефона: {phone}")

        email = str(data["email"]).strip()
        if not EMAIL_PATTERN.match(email):
            raise ValidationError(f"Неверный формат email: {email}")

        return Customer(
            surname=str(data["surname"]).strip(),
            name=str(data["name"]).strip(),
            address=str(data["address"]).strip(),
            phone=phone,
            email=email,
        )

    def generate_order_number(self) -> str:
        """Сгенерировать уникальный номер заказа формата ``ORD-YYYYMMDD-NNNN``."""
        cursor = self.connection.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        sequence = count + 1
        date_part = datetime.now().strftime("%Y%m%d")
        return f"ORD-{date_part}-{sequence:04d}"

    def save_order(self, customer: Customer, items: List[CartItem], total: float) -> Order:
        """Сохранить заказ в базу данных.

        :param customer: проверенные данные покупателя.
        :param items: позиции корзины.
        :param total: общая сумма заказа.
        :return: сохранённый объект :class:`Order`.
        :raises OrderSaveError: при ошибке записи в базу данных.
        """
        order_number = self.generate_order_number()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "новый"
        try:
            self.connection.execute(
                "INSERT INTO orders (order_number, surname, name, address, phone, "
                "email, total, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order_number,
                    customer.surname,
                    customer.name,
                    customer.address,
                    customer.phone,
                    customer.email,
                    total,
                    status,
                    created_at,
                ),
            )
            for item in items:
                self.connection.execute(
                    "INSERT INTO order_items (order_number, product_id, product_name, "
                    "price, quantity) VALUES (?, ?, ?, ?, ?)",
                    (
                        order_number,
                        item.product.id,
                        item.product.name,
                        item.product.price,
                        item.quantity,
                    ),
                )
            self.connection.commit()
            logger.info("Заказ %s сохранён в БД, сумма %.2f", order_number, total)
        except sqlite3.Error as error:
            self.connection.rollback()
            logger.error("Ошибка сохранения заказа %s", order_number, exc_info=True)
            raise OrderSaveError(f"Не удалось сохранить заказ: {error}") from error

        return Order(order_number, customer, list(items), total, status, created_at)

    def get_order(self, order_number: str) -> Optional[Order]:
        """Прочитать заказ из базы по номеру.

        :return: объект :class:`Order` или ``None``, если заказ не найден.
        """
        cursor = self.connection.execute(
            f"SELECT {ORDER_COLUMNS} FROM orders WHERE order_number = ?",
            (order_number,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_order(row)

    def list_orders(self) -> List[Order]:
        """Вернуть список всех заказов из базы (для админ-панели)."""
        cursor = self.connection.execute(
            f"SELECT {ORDER_COLUMNS} FROM orders ORDER BY created_at"
        )
        return [self._row_to_order(row) for row in cursor.fetchall()]

    def update_status(self, order_number: str, status: str) -> None:
        """Изменить статус заказа в базе данных.

        :raises ValidationError: если заказ не найден.
        """
        cursor = self.connection.execute(
            "UPDATE orders SET status = ? WHERE order_number = ?",
            (status, order_number),
        )
        self.connection.commit()
        if cursor.rowcount == 0:
            raise ValidationError(f"Заказ {order_number} не найден")
        logger.info("Статус заказа %s изменён на «%s»", order_number, status)

    def _row_to_order(self, row) -> Order:
        """Собрать объект :class:`Order` из строки таблицы orders и его позиций."""
        order_number = row[0]
        customer = Customer(row[1], row[2], row[3], row[4], row[5])
        items_cursor = self.connection.execute(
            "SELECT product_id, product_name, price, quantity FROM order_items "
            "WHERE order_number = ?",
            (order_number,),
        )
        items = [
            CartItem(Product(pid, pname, price, 0, "", ""), quantity)
            for pid, pname, price, quantity in items_cursor.fetchall()
        ]
        return Order(order_number, customer, items, row[6], row[7], row[8])
