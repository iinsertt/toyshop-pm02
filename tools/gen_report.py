"""Генерация финального отчёта «final_report.pdf» по ГОСТ 7.32-2017 (Этап 5).

Оформление: шрифт Times New Roman 14 пт, полуторный интервал, поля 30/15/20/20 мм,
титульный лист, содержание с номерами страниц, нумерация страниц снизу по центру,
нумерация разделов арабскими цифрами, встроенные UML-диаграммы и таблицы.

Запуск: ``python tools/gen_report.py``
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Preformatted,
    Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT, "docs")
REPORTS_DIR = os.path.join(ROOT, "reports")

FONTS = r"C:\Windows\Fonts"


def register_fonts():
    """Зарегистрировать шрифты Times New Roman и моноширинный шрифт для кода."""
    pdfmetrics.registerFont(TTFont("TNR", os.path.join(FONTS, "times.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-Bold", os.path.join(FONTS, "timesbd.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-Italic", os.path.join(FONTS, "timesi.ttf")))
    pdfmetrics.registerFont(TTFont("TNR-BoldItalic", os.path.join(FONTS, "timesbi.ttf")))
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic",
        boldItalic="TNR-BoldItalic",
    )
    try:
        pdfmetrics.registerFont(TTFont("Mono", os.path.join(FONTS, "cour.ttf")))
        return "Mono"
    except Exception:
        return "Courier"


MONO = register_fonts()


# --------------------------------------------------------------------------- #
# Стили
# --------------------------------------------------------------------------- #
def build_styles():
    """Создать набор стилей абзацев по ГОСТ."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "GostBody", fontName="TNR", fontSize=14, leading=21,
        alignment=TA_JUSTIFY, firstLineIndent=1.25 * cm, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        "GostH1", fontName="TNR-Bold", fontSize=15, leading=22,
        alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "GostH2", fontName="TNR-Bold", fontSize=14, leading=20,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "GostBullet", fontName="TNR", fontSize=14, leading=21,
        alignment=TA_JUSTIFY, leftIndent=1.25 * cm, bulletIndent=0.5 * cm,
    ))
    styles.add(ParagraphStyle(
        "GostCaption", fontName="TNR", fontSize=12, leading=16, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        "GostCode", fontName=MONO, fontSize=9, leading=11, alignment=TA_LEFT,
        leftIndent=0.5 * cm,
    ))
    styles.add(ParagraphStyle(
        "TitleBig", fontName="TNR-Bold", fontSize=24, leading=30, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TitleSub", fontName="TNR", fontSize=16, leading=22, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        "TitleSmall", fontName="TNR", fontSize=14, leading=20, alignment=TA_CENTER,
    ))
    return styles


# --------------------------------------------------------------------------- #
# Шаблон документа с поддержкой содержания и нумерации страниц
# --------------------------------------------------------------------------- #
class ReportDoc(BaseDocTemplate):
    """Документ с точными полями по ГОСТ и регистрацией заголовков в оглавлении.

    Используется собственный Frame с нулевыми внутренними отступами (padding=0),
    иначе reportlab добавляет 6 пт с каждой стороны и поля получаются больше нормы.
    """

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="normal",
        )
        self.addPageTemplates([
            PageTemplate(id="main", frames=[frame], onPage=draw_page_number),
        ])

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            text = flowable.getPlainText()
            if style_name == "GostH1":
                self.notify("TOCEntry", (0, text, self.page))
            elif style_name == "GostH2":
                self.notify("TOCEntry", (1, text, self.page))


def draw_page_number(canvas, doc):
    """Печать номера страницы снизу по центру (кроме титульного листа)."""
    page = canvas.getPageNumber()
    if page > 1:
        canvas.setFont("TNR", 12)
        canvas.drawCentredString(A4[0] / 2, 12 * mm, str(page))


# --------------------------------------------------------------------------- #
# Вспомогательные конструкторы флоу-элементов
# --------------------------------------------------------------------------- #
def h1(styles, text):
    return Paragraph(text, styles["GostH1"])


def h2(styles, text):
    return Paragraph(text, styles["GostH2"])


def body(styles, text):
    return Paragraph(text, styles["GostBody"])


def bullet(styles, text):
    return Paragraph(text, styles["GostBullet"], bulletText="—")


def code_block(styles, text):
    return Preformatted(text, styles["GostCode"])


def image(filename, width_cm=15.5):
    path = os.path.join(DOCS_DIR, filename)
    img = Image(path)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width_cm * cm
    img.drawHeight = width_cm * cm * ratio
    img.hAlign = "CENTER"
    return img


def make_table(data, col_widths):
    """Создать таблицу с оформлением (шапка серая, сетка)."""
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "TNR"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("FONTNAME", (0, 0), (-1, 0), "TNR-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e1f2")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


# --------------------------------------------------------------------------- #
# Содержимое отчёта
# --------------------------------------------------------------------------- #
def title_page(styles):
    """Сформировать титульный лист."""
    story = [Spacer(1, 3 * cm)]
    story.append(Paragraph("ОТЧЁТ", styles["TitleBig"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "по практическому экзаменационному заданию<br/>"
        "ПМ.02 «Осуществление интеграции программных модулей»", styles["TitleSub"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(
        "Тема: разработка информационной системы<br/>"
        "«Интернет-магазин игрушек ToyShop»", styles["TitleSub"]))
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Вариант 5 — магазин игрушек", styles["TitleSmall"]))
    story.append(Paragraph("Выполнил: Подмарьков Роман Михайлович", styles["TitleSmall"]))
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("2026", styles["TitleSmall"]))
    story.append(PageBreak())
    return story


def contents(styles):
    """Сформировать страницу содержания."""
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC1", fontName="TNR", fontSize=14, leading=22,
                       leftIndent=0, firstLineIndent=0),
        ParagraphStyle("TOC2", fontName="TNR", fontSize=13, leading=20,
                       leftIndent=1 * cm, firstLineIndent=0),
    ]
    # Отдельный стиль, чтобы заголовок «СОДЕРЖАНИЕ» не попадал в само оглавление.
    plain = ParagraphStyle("GostHeadingPlain", parent=styles["GostH1"], alignment=TA_CENTER)
    heading = Paragraph("СОДЕРЖАНИЕ", plain)
    return [heading, Spacer(1, 0.3 * cm), toc, PageBreak()]


def section_intro(styles):
    story = [h1(styles, "1 Введение")]
    story.append(body(styles, "Настоящий отчёт описывает разработку информационной "
        "системы «Интернет-магазин игрушек ToyShop» в рамках практического "
        "экзаменационного задания по дисциплине ПМ.02 «Осуществление интеграции "
        "программных модулей»."))
    story.append(body(styles, "ToyShop — это консольное приложение, позволяющее "
        "покупателю просматривать каталог игрушек, формировать корзину и оформлять "
        "заказы, а администратору — управлять товарами и заказами. Каталог товаров "
        "хранится в JSON-файле, заказы — в базе данных SQLite."))
    story.append(body(styles, "Используемые технологии:"))
    for item in (
        "язык программирования Python 3.14;",
        "хранение каталога — формат JSON;",
        "хранение заказов — база данных SQLite (модуль sqlite3);",
        "логирование — стандартный модуль logging;",
        "тестирование — фреймворк pytest;",
        "система контроля версий — Git;",
        "среда разработки — Visual Studio Code.",
    ):
        story.append(bullet(styles, item))
    return story


def section_tz(styles):
    story = [h1(styles, "2 Техническое задание")]
    story.append(body(styles, "Система предназначена для автоматизации работы интернет-"
        "магазина игрушек. Продаются товары четырёх категорий: конструкторы, куклы, "
        "машинки и настольные игры. В системе предусмотрены две роли: Покупатель и "
        "Администратор."))
    story.append(h2(styles, "2.1 Функциональные требования"))
    for item in (
        "каталог товаров с поиском по названию и фильтрацией по категории и цене;",
        "корзина с добавлением, удалением и изменением количества товаров;",
        "оформление заказа с валидацией данных и сохранением в базу данных;",
        "генерация уникального номера заказа;",
        "административная панель: управление товарами и статусами заказов.",
    ):
        story.append(bullet(styles, item))
    story.append(h2(styles, "2.2 Нефункциональные требования"))
    for item in (
        "быстродействие: время отклика не более одной секунды на операцию;",
        "надёжность: обработка ошибок (try/except), валидация, логирование;",
        "масштабируемость: модульная архитектура, возможность замены хранилища.",
    ):
        story.append(bullet(styles, item))
    story.append(h2(styles, "2.3 Диаграммы"))
    story.append(body(styles, "Диаграмма компонентов системы приведена на рисунке 1, "
        "диаграмма вариантов использования — на рисунке 2."))
    story.append(image("component_diagram.png"))
    story.append(Paragraph("Рисунок 1 — Диаграмма компонентов системы", styles["GostCaption"]))
    story.append(image("use_case_diagram.png", width_cm=13))
    story.append(Paragraph("Рисунок 2 — Диаграмма вариантов использования", styles["GostCaption"]))
    return story


def section_architecture(styles):
    story = [h1(styles, "3 Архитектура и структура проекта")]
    story.append(body(styles, "Система построена по модульному принципу. Каждый модуль "
        "решает одну задачу и взаимодействует с другими через явные интерфейсы и общие "
        "модели данных."))
    story.append(h2(styles, "3.1 Состав модулей"))
    for item in (
        "Модуль 1 «Каталог» — загрузка товаров из JSON, поиск, фильтрация;",
        "Модуль 2 «Корзина» — управление позициями и расчёт суммы;",
        "Модуль 3 «Оформление заказа» — валидация, сохранение в SQLite, номер заказа;",
        "Модуль 4 «Админ-панель» — управление товарами и заказами;",
        "Модуль 5 «Интеграция» (main.py) — консольное меню, связывающее модули.",
    ):
        story.append(bullet(styles, item))
    story.append(h2(styles, "3.2 Структура проекта"))
    tree = (
        "ekz_project/\n"
        "  docs/        технич. задание (.docx), UML-диаграммы (.png)\n"
        "  src/\n"
        "    common/    модели, исключения, логирование\n"
        "    Module1_Catalog/   catalog.py\n"
        "    Module2_Cart/      cart.py\n"
        "    Module3_Order/     order.py\n"
        "    Module4_Admin/     admin.py\n"
        "    data/      products.json (каталог товаров)\n"
        "    main.py    точка входа (консольное меню)\n"
        "  tests/       юнит- и интеграционные тесты, test_report.md\n"
        "  reports/     debug_report.md, code_inspection.md, final_report.pdf\n"
        "  logs/        app.log (журнал работы)\n"
        "  README.md    инструкция по установке и запуску\n"
    )
    story.append(code_block(styles, tree))
    return story


def section_development(styles):
    story = [h1(styles, "4 Описание разработки")]
    story.append(body(styles, "Разработка велась поэтапно с использованием системы "
        "контроля версий Git. Каждый завершённый этап фиксировался отдельным коммитом "
        "с осмысленным описанием (всего более 25 коммитов): создание каркаса, реализация "
        "модулей, написание тестов, отладка, инспекция кода, подготовка документации."))
    story.append(h2(styles, "4.1 Работа программы (скриншоты интерфейса)"))
    story.append(body(styles, "Ниже приведены экраны работающего приложения, полученные "
        "при запуске программы в консоли."))
    story.append(image("screen_1_catalog.png"))
    story.append(Paragraph("Рисунок 3 — Главное меню и каталог товаров", styles["GostCaption"]))
    story.append(image("screen_2_cart.png"))
    story.append(Paragraph("Рисунок 4 — Корзина и расчёт суммы", styles["GostCaption"]))
    story.append(image("screen_3_order.png"))
    story.append(Paragraph("Рисунок 5 — Оформление заказа", styles["GostCaption"]))
    story.append(image("screen_4_admin.png"))
    story.append(Paragraph("Рисунок 6 — Административная панель", styles["GostCaption"]))
    story.append(h2(styles, "4.2 Пример кода"))
    story.append(body(styles, "Расчёт общей суммы корзины с учётом количества товаров "
        "(модуль Корзина):"))
    code = (
        "def total(self) -> float:\n"
        "    \"\"\"Рассчитать общую сумму заказа.\"\"\"\n"
        "    return sum(item.subtotal for item in self.items)\n"
    )
    story.append(code_block(styles, code))
    story.append(body(styles, "Валидация телефона при оформлении заказа (модуль Заказ):"))
    code2 = (
        "phone = str(data['phone']).strip()\n"
        "if not PHONE_PATTERN.match(phone):\n"
        "    raise ValidationError(f'Неверный формат телефона: {phone}')\n"
    )
    story.append(code_block(styles, code2))
    story.append(h2(styles, "4.3 Логирование"))
    story.append(body(styles, "Все ключевые события записываются в файл logs/app.log с "
        "указанием времени, уровня и сообщения. Пример журнала:"))
    log = (
        "2026-06-18 14:17:25 | INFO | Запуск приложения ToyShop\n"
        "2026-06-18 14:17:25 | INFO | Каталог загружен: 16 товаров\n"
        "2026-06-18 14:17:25 | INFO | В корзину добавлен товар pr_001 (x2)\n"
        "2026-06-18 14:17:25 | INFO | Заказ ORD-20260618-0001 сохранён в БД, сумма 9998.00\n"
    )
    story.append(code_block(styles, log))
    story.append(h2(styles, "4.4 Демонстрация инструментов отладки"))
    story.append(body(styles, "Отладка выполнялась в среде Visual Studio Code с "
        "использованием конфигурации .vscode/launch.json. На рисунке 7 показана "
        "остановка программы на точке останова: одновременно видны точка останова "
        "(красная отметка слева от строки), панель Variables с текущими значениями "
        "переменных и панель Call Stack с цепочкой вызовов checkout_menu → main."))
    story.append(image("debug_1.jpg"))
    story.append(Paragraph("Рисунок 7 — Остановка на точке останова (Variables, Call Stack)",
        styles["GostCaption"]))
    story.append(body(styles, "На рисунке 8 показано пошаговое выполнение: после нажатия "
        "F11 (Step Into) отладчик вошёл внутрь метода validate_customer, а стек вызовов "
        "углубился до validate_customer → checkout_menu → main."))
    story.append(image("debug_2.jpg"))
    story.append(Paragraph("Рисунок 8 — Пошаговое выполнение (Step Into)",
        styles["GostCaption"]))
    return story


def section_testing(styles):
    story = [h1(styles, "5 Тестирование")]
    story.append(body(styles, "Разработано 10 тест-кейсов (3 — каталог, 3 — корзина, "
        "2 — заказ, 2 — админка) и 3 интеграционных теста. Все тесты автоматизированы "
        "с помощью pytest и успешно пройдены."))
    data = [
        ["Тестовый пакет", "Тестов", "Пройдено", "Провалено"],
        ["Каталог", "3", "3", "0"],
        ["Корзина", "3", "3", "0"],
        ["Оформление заказа", "2", "2", "0"],
        ["Админ-панель", "2", "2", "0"],
        ["Интеграционные", "3", "3", "0"],
        ["ИТОГО", "13", "13", "0"],
    ]
    story.append(make_table(data, [6 * cm, 3 * cm, 3 * cm, 3 * cm]))
    story.append(Paragraph("Таблица 1 — Результаты тестирования", styles["GostCaption"]))
    story.append(h2(styles, "5.1 Найденные ошибки и их исправление"))
    story.append(body(styles, "В процессе отладки выявлено и исправлено три ошибки. "
        "Каждое исправление зафиксировано отдельным коммитом."))
    bugs = [
        ["Ошибка", "Как обнаружена", "Исправление", "Коммит"],
        ["Неверный путь к JSON", "Тест, лог ERROR", "Абсолютный путь через os.path", "c8c48ee"],
        ["Сумма без количества", "Юнит-тест корзины", "Использование item.subtotal", "b05c759"],
        ["Пропуск проверки телефона", "Юнит-тест заказа", "Восстановлена проверка regex", "4d37725"],
    ]
    story.append(make_table(bugs, [4 * cm, 4 * cm, 4.5 * cm, 2.5 * cm]))
    story.append(Paragraph("Таблица 2 — Найденные и исправленные ошибки", styles["GostCaption"]))
    return story


def section_inspection(styles):
    story = [h1(styles, "6 Инспекция кода")]
    story.append(body(styles, "Проведена инспекция кода на соответствие стандартам "
        "кодирования (PEP 8). Найдено и исправлено пять нарушений; каждое исправление "
        "оформлено отдельным коммитом."))
    data = [
        ["Нарушение", "Файл", "Исправление", "Коммит"],
        ["Однобуквенное имя", "catalog.py", "Имя normalized", "4170a9b"],
        ["Строка > 120 символов", "catalog.py", "Разбита на строки", "49c3753"],
        ["Нет docstring", "catalog.py", "Добавлен docstring", "57a0a79"],
        ["Магическое число", "main.py", "Константа MAX_PRICE_DEFAULT", "daac6dc"],
        ["Дублирование кода", "order.py", "Константа ORDER_COLUMNS", "4d597e5"],
    ]
    story.append(make_table(data, [4 * cm, 3 * cm, 5 * cm, 2.5 * cm]))
    story.append(Paragraph("Таблица 3 — Нарушения и исправления", styles["GostCaption"]))
    return story


def section_conclusion(styles):
    story = [h1(styles, "7 Выводы")]
    story.append(body(styles, "В ходе выполнения задания разработана полнофункциональная "
        "информационная система «ToyShop», состоящая из пяти интегрированных модулей. "
        "Реализованы все требуемые функции: каталог с поиском и фильтрацией, корзина, "
        "оформление заказа с сохранением в базу данных и административная панель."))
    story.append(body(styles, "Применены навыки: анализ требований и разработка "
        "технического задания, интеграция программных модулей, отладка с использованием "
        "точек останова и логирования, разработка тестовых сценариев, инспекция кода на "
        "соответствие стандартам."))
    story.append(body(styles, "Основные трудности были связаны с корректным выводом "
        "кириллицы и символов валюты в консоли Windows (решено принудительным переводом "
        "потоков ввода-вывода в кодировку UTF-8), а также с обеспечением согласованной "
        "передачи данных между модулями (решено за счёт общих моделей данных)."))
    story.append(body(styles, "Все 13 тестов пройдены, программа запускается и работает "
        "без ошибок. Задание выполнено в полном объёме."))
    return story


def section_install(styles):
    story = [h1(styles, "8 Инструкция по установке и запуску")]
    story.append(body(styles, "Для работы программы требуется Python версии 3.10 и выше."))
    story.append(h2(styles, "8.1 Установка"))
    story.append(body(styles, "1. Установить зависимости командой:"))
    story.append(code_block(styles, "pip install -r requirements.txt"))
    story.append(h2(styles, "8.2 Запуск программы"))
    story.append(body(styles, "Из корневой папки проекта выполнить:"))
    story.append(code_block(styles, "python src/main.py"))
    story.append(h2(styles, "8.3 Запуск тестов"))
    story.append(body(styles, "Для проверки работоспособности выполнить:"))
    story.append(code_block(styles, "python -m pytest tests/ -v"))
    return story


def build():
    """Собрать и сохранить итоговый PDF-отчёт."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    styles = build_styles()
    output = os.path.join(REPORTS_DIR, "final_report.pdf")
    doc = ReportDoc(
        output, pagesize=A4,
        leftMargin=30 * mm, rightMargin=15 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
        title="Отчёт ToyShop", author="Подмарьков Р.М.",
    )
    story = []
    story += title_page(styles)
    story += contents(styles)
    story += section_intro(styles)
    story += section_tz(styles)
    story += section_architecture(styles)
    story += section_development(styles)
    story += section_testing(styles)
    story += section_inspection(styles)
    story += section_conclusion(styles)
    story += section_install(styles)
    doc.multiBuild(story)
    print(f"Создано: {output}")


if __name__ == "__main__":
    build()
