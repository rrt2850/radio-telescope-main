import csv
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).with_name("data.csv")


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
