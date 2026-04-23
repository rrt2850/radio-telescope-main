import csv
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).with_name("data.csv")


def _distance_group(parallax_mas: float) -> str:
    """Group stars by approximate distance using parallax in milliarcseconds."""
    if parallax_mas >= 250:
        return "Nearby (< 4 pc)"
    if parallax_mas >= 100:
        return "Mid-range (4-10 pc)"
    return "Farther (> 10 pc)"


def load_star_catalog(limit_per_group: int = 200) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "Nearby (< 4 pc)": [],
        "Mid-range (4-10 pc)": [],
        "Farther (> 10 pc)": [],
    }

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

            group_name = _distance_group(parallax_mas)
            if len(grouped[group_name]) >= limit_per_group:
                continue

            grouped[group_name].append(
                {
                    "name": name,
                    "ra": ra,
                    "dec": dec,
                    "parallax_mas": parallax_mas,
                }
            )

    for stars in grouped.values():
        stars.sort(key=lambda star: star["parallax_mas"], reverse=True)

    return [
        {
            "group": group_name,
            "stars": stars,
        }
        for group_name, stars in grouped.items()
        if stars
    ]
