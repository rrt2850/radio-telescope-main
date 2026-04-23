import csv
from pathlib import Path
from typing import Any
from functools import lru_cache

CATALOG_PATH = Path(__file__).with_name("data.csv")


@lru_cache(maxsize=1)
def load_star_catalog() -> list[dict[str, Any]]:
    stars: list[dict[str, Any]] = []

    with CATALOG_PATH.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                name = row["main_id"].strip().strip('"')
                ra = float(row["ra"])
                dec = float(row["dec"])
                parallax_mas = float(row["plx_value"])
            except (KeyError, TypeError, ValueError):
                continue

            stars.append(
                {
                    "name": name,
                    "ra": ra,
                    "dec": dec,
                    "parallax_mas": parallax_mas,
                }
            )

    stars.sort(key=lambda star: (star["name"], -star["parallax_mas"]))
    return stars


def get_star_catalog_page(page: int, page_size: int) -> dict[str, Any]:
    stars = load_star_catalog()
    total = len(stars)
    start = page * page_size
    end = start + page_size

    return {
        "stars": stars[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": end < total,
    }


def search_star_catalog(query: str, limit: int) -> list[dict[str, Any]]:
    normalized_query = query.strip().lower()
    if not normalized_query:
        return []

    matches = [
        star
        for star in load_star_catalog()
        if normalized_query in star["name"].lower()
    ]
    return matches[:limit]
