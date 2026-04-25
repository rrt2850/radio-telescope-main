import csv
from pathlib import Path
from typing import Any
from functools import lru_cache
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
import astropy.units as units

import constants

CATALOG_PATH = Path(__file__).with_name("data.csv")
DEFAULT_MIN_BROWSE_ALTITUDE_DEG = 5.0


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


def _filter_stars_by_altitude(
    stars: list[dict[str, Any]],
    min_altitude_deg: float = DEFAULT_MIN_BROWSE_ALTITUDE_DEG,
) -> list[dict[str, Any]]:
    observer_location = EarthLocation.from_geodetic(
        constants.LONG,
        constants.LAT,
        constants.HEIGHT * units.m,
    )
    observation_frame = AltAz(obstime=Time.now(), location=observer_location)

    visible_stars: list[dict[str, Any]] = []
    for star in stars:
        target = SkyCoord(star["ra"] * units.deg, star["dec"] * units.deg)
        altitude = target.transform_to(observation_frame).alt.deg
        if altitude >= min_altitude_deg:
            visible_stars.append(star)

    return visible_stars


def get_visible_star_catalog_page(
    page: int,
    page_size: int,
    min_altitude_deg: float = DEFAULT_MIN_BROWSE_ALTITUDE_DEG,
) -> dict[str, Any]:
    stars = _filter_stars_by_altitude(
        load_star_catalog(),
        min_altitude_deg=min_altitude_deg,
    )
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
