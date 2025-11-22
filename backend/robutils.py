from astropy.coordinates import EarthLocation   # For Lat/Long/Elevation
from astropy.coordinates import SkyCoord        # Defines celestial objects in RA/Dec, parses input, and does conversions
from astropy.coordinates import AltAz           # Converts from equatorial (RA/Dec) to horizontal (Altitutde/Azimuth)
from astropy.time import Time                   # There are other time libraries but this one is gigachad
import astropy.units as units                   # Using astropy's units for strong typing
import tkinter as tk                            # Library for GUI

def CoordsTo(currLat : float, currLong : float, height : float, targetRa : float, targetDec : float):
    """
        Given the current latitude, longitude, and height, assuming the telescope
        has not been rotated, gives the required horizontal and vertical rotations
        to point the telescope towards the target equatorial coordinate
        ____ Accepts ______

        currLat : float
            The current latitude
        currLong : float
            The current longitude
        height : float
            How high the telescope is above WGS84 in meters
        targetRa: float
            The target right ascension in equatorial coordinates
        targetDec : float
            The target declination

        _____ Returns ______

        A tuple representing (azimuth angle, altitude angle) relative to the starting location
    """
    currLocation = EarthLocation.from_geodetic(currLong, currLat, height * units.m)
    target = SkyCoord(targetRa * units.degree, targetDec * units.degree)
    time = Time.now()

    altAzLocation = AltAz(obstime=time, location=currLocation)
    altAzTarget = target.transform_to(altAzLocation)

    return (altAzTarget.az.deg , altAzTarget.alt.deg)