"""Генерация UML-диаграмм для технического задания ToyShop.

Создаёт два PNG-файла в папке ``docs``:
- ``component_diagram.png`` — диаграмма компонентов (модули и потоки данных);
- ``use_case_diagram.png`` — диаграмма вариантов использования (актёры и сценарии).

Запуск: ``python tools/gen_diagrams.py``
"""
import os

import matplotlib

matplotlib.use("Agg")  # без графического окна
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.family"] = "DejaVu Sans"  # поддержка кириллицы

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def _box(ax, x, y, width, height, text, color):
    """Нарисовать прямоугольный компонент с подписью по центру."""
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.5, edgecolor="#2c3e50", facecolor=color,
    )
    ax.add_patch(box)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center",
            fontsize=9, wrap=True)


def _arrow(ax, start, end, text="", style="-|>"):
    """Нарисовать стрелку (поток данных) между двумя точками."""
    arrow = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=15,
                            linewidth=1.3, color="#34495e")
    ax.add_patch(arrow)
    if text:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x, mid_y + 0.1, text, ha="center", va="bottom", fontsize=7.5,
                color="#7f1d1d")


def generate_component_diagram():
    """Построить диаграмму компонентов системы."""
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title("Диаграмма компонентов системы «ToyShop»", fontsize=13, fontweight="bold")

    # Точка входа / интеграция
    _box(ax, 4, 8.2, 4, 1.1, "main.py\nКонсольное меню / Интеграция\n(Модуль 5)", "#aed6f1")

    # Модули
    _box(ax, 0.3, 5.3, 2.6, 1.2, "Модуль 1\nКаталог товаров", "#d5f5e3")
    _box(ax, 3.3, 5.3, 2.6, 1.2, "Модуль 2\nКорзина", "#d5f5e3")
    _box(ax, 6.3, 5.3, 2.6, 1.2, "Модуль 3\nОформление заказа", "#d5f5e3")
    _box(ax, 9.3, 5.3, 2.4, 1.2, "Модуль 4\nАдмин-панель", "#d5f5e3")

    # Хранилища данных
    _box(ax, 0.6, 2.3, 2.6, 1.0, "products.json\n(каталог товаров)", "#f9e79f")
    _box(ax, 8.6, 2.3, 2.6, 1.0, "orders.db\n(SQLite, заказы)", "#f9e79f")

    # Общая инфраструктура — слой-фундамент под всеми модулями
    _box(ax, 0.6, 0.5, 10.6, 0.9,
         "src/common: модели, исключения, логирование (используется всеми модулями)",
         "#fdebd0")

    # Стрелки от main к модулям
    _arrow(ax, (5, 8.2), (1.6, 6.5))
    _arrow(ax, (5.5, 8.2), (4.6, 6.5))
    _arrow(ax, (6.5, 8.2), (7.6, 6.5))
    _arrow(ax, (7, 8.2), (10.5, 6.5))

    # Потоки данных между модулями
    _arrow(ax, (2.9, 5.9), (3.3, 5.9), "товар")
    _arrow(ax, (5.9, 5.9), (6.3, 5.9), "позиции")

    # Связь с хранилищами
    _arrow(ax, (1.6, 5.3), (1.7, 3.3), "чтение")
    _arrow(ax, (7.6, 5.3), (9.4, 3.3), "запись")
    _arrow(ax, (10.5, 5.3), (10.1, 3.3), "заказы")
    _arrow(ax, (9.6, 5.3), (3.0, 3.3), "CRUD товаров")

    fig.tight_layout()
    output = os.path.join(DOCS_DIR, "component_diagram.png")
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Создано: {output}")


def _actor(ax, x, y, label):
    """Нарисовать актёра (фигурку человечка) с подписью."""
    ax.add_patch(Circle((x, y + 0.5), 0.18, fill=False, linewidth=1.5, edgecolor="#2c3e50"))
    ax.plot([x, x], [y + 0.32, y - 0.25], color="#2c3e50", linewidth=1.5)       # туловище
    ax.plot([x - 0.25, x + 0.25], [y + 0.1, y + 0.1], color="#2c3e50", linewidth=1.5)  # руки
    ax.plot([x, x - 0.2], [y - 0.25, y - 0.6], color="#2c3e50", linewidth=1.5)  # нога
    ax.plot([x, x + 0.2], [y - 0.25, y - 0.6], color="#2c3e50", linewidth=1.5)  # нога
    ax.text(x, y - 0.85, label, ha="center", va="top", fontsize=10, fontweight="bold")


def _use_case(ax, x, y, text):
    """Нарисовать вариант использования (овал) и вернуть его центр."""
    ellipse = Ellipse((x, y), 2.6, 0.8, facecolor="#d6eaf8", edgecolor="#2c3e50", linewidth=1.2)
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5)
    return (x, y)


def generate_use_case_diagram():
    """Построить диаграмму вариантов использования."""
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 11)
    ax.axis("off")
    ax.set_title("Диаграмма вариантов использования «ToyShop»", fontsize=13, fontweight="bold")

    # Граница системы
    ax.add_patch(FancyBboxPatch((3.2, 0.6), 5.6, 9.6, boxstyle="round,pad=0.1",
                                fill=False, linewidth=1.5, edgecolor="#7f8c8d"))
    ax.text(6, 9.9, "Система «ToyShop»", ha="center", fontsize=10, style="italic")

    # Актёры
    _actor(ax, 1.2, 7.5, "Покупатель")
    _actor(ax, 10.8, 3.5, "Администратор")

    # Варианты использования покупателя
    customer_cases = [
        _use_case(ax, 6, 9.2, "Просмотр каталога"),
        _use_case(ax, 6, 8.2, "Поиск товара"),
        _use_case(ax, 6, 7.2, "Фильтрация товаров"),
        _use_case(ax, 6, 6.2, "Управление корзиной"),
        _use_case(ax, 6, 5.2, "Оформление заказа"),
    ]
    # Варианты использования администратора
    admin_cases = [
        _use_case(ax, 6, 4.0, "Просмотр заказов"),
        _use_case(ax, 6, 3.0, "Изменение статуса"),
        _use_case(ax, 6, 2.0, "Добавление товара"),
        _use_case(ax, 6, 1.2, "Редактирование/удаление"),
    ]

    # Связи актёров с вариантами использования
    for case in customer_cases:
        ax.plot([1.6, case[0] - 1.3], [7.3, case[1]], color="#2c3e50", linewidth=1)
    for case in admin_cases:
        ax.plot([10.4, case[0] + 1.3], [3.4, case[1]], color="#2c3e50", linewidth=1)

    fig.tight_layout()
    output = os.path.join(DOCS_DIR, "use_case_diagram.png")
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Создано: {output}")


if __name__ == "__main__":
    os.makedirs(DOCS_DIR, exist_ok=True)
    generate_component_diagram()
    generate_use_case_diagram()
    print("Диаграммы готовы.")
