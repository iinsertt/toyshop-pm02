"""Настройка системы логирования приложения ToyShop (Этап 4.4).

Логи пишутся в файл ``logs/app.log`` в корне проекта. Каждая запись содержит
метку времени, уровень логирования и сообщение. Для ошибок дополнительно
сохраняется стек вызовов (при вызове ``logger.error(..., exc_info=True)``).
"""
import logging
import os

# Каталог для лог-файлов: <корень проекта>/logs
# logger.py лежит в src/common, поэтому поднимаемся на три уровня вверх.
LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs",
)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Формат записи лога: "2026-06-18 14:30:01 | INFO | сообщение".
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Вернуть настроенный логгер, пишущий в файл ``logs/app.log``.

    :param name: имя логгера (обычно имя модуля).
    :return: объект :class:`logging.Logger` с файловым обработчиком.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    # Не добавляем обработчик повторно при повторном вызове get_logger.
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(handler)
    return logger
