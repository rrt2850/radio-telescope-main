import csv
from pathlib import Path
from typing import Any
from functools import lru_cache
from datetime import datetime, timezone
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
import astropy.units as units

import constants

CATALOG_PATH = Path(__file__).with_name("data.csv")
# Keep browse/catalog visibility aligned with telescope motion constraints.
# If a star cannot be pointed to, it should not appear in the "visible" browse pages.
DEFAULT_MIN_BROWSE_ALTITUDE_DEG = float(constants.MIN_ANGLE)


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

    if not stars:
        return []

    star_coords = SkyCoord(
        ra=[star["ra"] for star in stars] * units.deg,
        dec=[star["dec"] for star in stars] * units.deg,
    )
    altitudes = star_coords.transform_to(observation_frame).alt.deg

    return [
        star
        for star, altitude in zip(stars, altitudes)
        if altitude >= min_altitude_deg
    ]


@lru_cache(maxsize=16)
def _get_visible_stars_for_time_bucket(
    min_altitude_deg: float,
    minute_bucket: int,
) -> list[dict[str, Any]]:
    # `minute_bucket` intentionally controls cache invalidation cadence.
    del minute_bucket
    return _filter_stars_by_altitude(
        load_star_catalog(),
        min_altitude_deg=min_altitude_deg,
    )


def get_visible_star_catalog_page(
    page: int,
    page_size: int,
    min_altitude_deg: float = DEFAULT_MIN_BROWSE_ALTITUDE_DEG,
) -> dict[str, Any]:
    minute_bucket = int(datetime.now(tz=timezone.utc).timestamp() // 60)
    stars = _get_visible_stars_for_time_bucket(
        min_altitude_deg=min_altitude_deg,
        minute_bucket=minute_bucket,
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
