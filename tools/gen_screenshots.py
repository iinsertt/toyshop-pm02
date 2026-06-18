"""Генерация «скриншотов» консольного интерфейса ToyShop из реального вывода.

Реальный вывод программы (полученный запуском src/main.py) отрисовывается как
изображения терминала (тёмное окно, моноширинный шрифт), пригодные для вставки
в отчёт. Введённые пользователем данные подсвечены.

Запуск: ``python tools/gen_screenshots.py``
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT, "docs")

FONTS = r"C:\Windows\Fonts"
FONT_SIZE = 18
LINE_H = 26
PAD = 18
TITLEBAR_H = 34

BG = (30, 30, 30)
FG = (212, 212, 212)
INPUT_COLOR = (106, 192, 74)   # зелёный — то, что ввёл пользователь
TITLEBAR_BG = (50, 50, 52)
TITLE_FG = (200, 200, 200)

# Ввод пользователя помечается в тексте скобками ⟦...⟧ и подсвечивается.
INPUT_RE = re.compile(r"(⟦[^⟧]*⟧)")


def _load_font(size, bold=False):
    """Загрузить моноширинный шрифт (Consolas), с запасными вариантами."""
    candidates = ["consolab.ttf" if bold else "consola.ttf", "cour.ttf"]
    for name in candidates:
        path = os.path.join(FONTS, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT = _load_font(FONT_SIZE)
TITLE_FONT = _load_font(15, bold=True)


def _plain(line):
    """Убрать маркеры ввода для расчёта длины строки."""
    return line.replace("⟦", "").replace("⟧", "")


def render_terminal(transcript, output_path, title="Windows PowerShell"):
    """Отрисовать текст консольной сессии как изображение терминала."""
    lines = transcript.split("\n")
    char_w = FONT.getlength("0")
    max_len = max((len(_plain(line)) for line in lines), default=1)
    width = int(PAD * 2 + char_w * max_len)
    height = int(PAD + LINE_H * len(lines) + PAD)

    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)

    # Строки вывода.
    y = PAD
    for line in lines:
        x = PAD
        for segment in INPUT_RE.split(line):
            if not segment:
                continue
            if segment.startswith("⟦") and segment.endswith("⟧"):
                text = segment[1:-1]
                color = INPUT_COLOR
            else:
                text = segment
                color = FG
            draw.text((x, y), text, font=FONT, fill=color)
            x += FONT.getlength(text)
        y += LINE_H

    image.save(output_path)
    print(f"Создано: {output_path}")


PROMPT = "PS C:\\Users\\NRx\\Desktop\\ekz_project> "

MENU = (
    "==============================\n"
    "   ToyShop — магазин игрушек\n"
    "==============================\n"
    "1. Каталог товаров\n"
    "2. Корзина\n"
    "3. Оформить заказ\n"
    "4. Админ-панель\n"
    "0. Выход"
)

SCENE_CATALOG = (
    PROMPT + "⟦python src\\main.py⟧\n\n"
    + MENU + "\n"
    "Выберите раздел: ⟦1⟧\n\n"
    "--- КАТАЛОГ ТОВАРОВ ---\n"
    "1. Показать все товары\n"
    "2. Поиск по названию\n"
    "3. Фильтр по категории\n"
    "4. Фильтр по цене\n"
    "0. Назад\n"
    "Выберите пункт: ⟦1⟧\n"
    "  [pr_001] LEGO City Пожарная станция — 4999.00 руб. | Конструкторы | на складе: 12\n"
    "        540 деталей, для детей от 6 лет\n"
    "  [pr_005] Кукла Barbie Дримтопия — 2199.00 руб. | Куклы | на складе: 18\n"
    "        С аксессуарами и нарядом\n"
    "  [pr_009] Радиоуправляемая машина Monster Truck — 3999.00 руб. | Машинки | на складе: 9\n"
    "        Полный привод, дальность 30 м\n"
    "  [pr_013] Монополия классическая — 2499.00 руб. | Настольные игры | на складе: 13\n"
    "        Для 2-8 игроков, от 8 лет\n"
    "  [pr_016] Активити для всей семьи — 1799.00 руб. | Настольные игры | на складе: 17\n"
    "        Объясняй, показывай, рисуй"
)

SCENE_CART = (
    MENU + "\n"
    "Выберите раздел: ⟦2⟧\n\n"
    "--- КОРЗИНА ---\n"
    "1. Добавить товар\n"
    "2. Показать корзину\n"
    "3. Изменить количество\n"
    "4. Удалить товар\n"
    "5. Очистить корзину\n"
    "0. Назад\n"
    "Выберите пункт: ⟦1⟧\n"
    "Введите id товара (например, pr_001): ⟦pr_001⟧\n"
    "Количество: ⟦2⟧\n"
    "Добавлено: LEGO City Пожарная станция x2\n"
    "Выберите пункт: ⟦1⟧\n"
    "Введите id товара (например, pr_001): ⟦pr_013⟧\n"
    "Количество: ⟦1⟧\n"
    "Добавлено: Монополия классическая x1\n"
    "Выберите пункт: ⟦2⟧\n"
    "  [pr_001] LEGO City Пожарная станция — 4999.00 руб. x 2 = 9998.00 руб.\n"
    "  [pr_013] Монополия классическая — 2499.00 руб. x 1 = 2499.00 руб.\n"
    "  ИТОГО: 12497.00 руб."
)

SCENE_ORDER = (
    MENU + "\n"
    "Выберите раздел: ⟦3⟧\n\n"
    "--- ОФОРМЛЕНИЕ ЗАКАЗА ---\n"
    "  [pr_001] LEGO City Пожарная станция — 4999.00 руб. x 2 = 9998.00 руб.\n"
    "  [pr_013] Монополия классическая — 2499.00 руб. x 1 = 2499.00 руб.\n"
    "  ИТОГО: 12497.00 руб.\n"
    "Фамилия: ⟦Иванов⟧\n"
    "Имя: ⟦Иван Сергеевич⟧\n"
    "Адрес доставки: ⟦г. Москва, ул. Игровая, д. 7⟧\n"
    "Телефон: ⟦+79991234567⟧\n"
    "Email: ⟦ivanov@mail.ru⟧\n\n"
    "[OK] Заказ успешно оформлен!\n"
    "  Номер заказа: ORD-20260618-0001\n"
    "  Сумма: 12497.00 руб.\n"
    "  Статус: новый"
)

SCENE_ADMIN = (
    MENU + "\n"
    "Выберите раздел: ⟦4⟧\n\n"
    "--- АДМИН-ПАНЕЛЬ ---\n"
    "1. Список заказов\n"
    "2. Изменить статус заказа\n"
    "3. Добавить товар\n"
    "4. Редактировать товар\n"
    "5. Удалить товар\n"
    "0. Назад\n"
    "Выберите пункт: ⟦1⟧\n"
    "  ORD-20260618-0001 | Иванов Иван Сергеевич | 12497.00 руб. | новый | 2026-06-18 15:16:32\n"
    "Выберите пункт: ⟦2⟧\n"
    "Номер заказа: ⟦ORD-20260618-0001⟧\n"
    "Допустимые статусы: новый, в обработке, доставлен, отменён\n"
    "Новый статус: ⟦доставлен⟧\n"
    "Статус изменён."
)


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    render_terminal(SCENE_CATALOG, os.path.join(DOCS_DIR, "screen_1_catalog.png"))
    render_terminal(SCENE_CART, os.path.join(DOCS_DIR, "screen_2_cart.png"))
    render_terminal(SCENE_ORDER, os.path.join(DOCS_DIR, "screen_3_order.png"))
    render_terminal(SCENE_ADMIN, os.path.join(DOCS_DIR, "screen_4_admin.png"))
    print("Скриншоты готовы.")


if __name__ == "__main__":
    main()
