from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, Sequence

from django.utils import timezone

TIME_FORMAT = "%d-%m-%Y %H:%M"


@dataclass(frozen=True)
class ShoppingLine:
    position: int
    title: str
    unit: str | None = None
    amount: str | None = None

    def render(self) -> str:
        suffix = ""
        if self.unit:
            suffix += f" ({self.unit})"
        if self.amount:
            suffix += f" - {self.amount}"
        return f"{self.position}. {self.title}{suffix}"


def _build_ingredient_lines(ingredients: Sequence[dict]) -> Iterable[str]:
    for index, item in enumerate(ingredients, start=1):
        yield ShoppingLine(
            position=index,
            title=str(item["ingredient__name"]).capitalize(),
            unit=str(item["ingredient__measurement_unit"]),
            amount=str(item["amount"]),
        ).render()


def _build_recipe_lines(recipes: Sequence) -> Iterable[str]:
    for index, recipe in enumerate(recipes, start=1):
        yield ShoppingLine(position=index, title=str(recipe.name)).render()


def make_shopping_cart_file(ingredients, recipes):
    timestamp = timezone.localtime().strftime(TIME_FORMAT)
    payload = [
        f"Дата и время: {timestamp}",
        "",
        "Список покупок:",
        *_build_ingredient_lines(ingredients),
        "",
        "Список рецептов:",
        *_build_recipe_lines(recipes),
    ]
    return BytesIO("\n".join(payload).encode("utf-8"))
