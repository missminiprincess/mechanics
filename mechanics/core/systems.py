"""Known CR3BP systems."""

from mechanics.core.models import SystemParameters

SUN_MASS_KG = 1.9885e30
EARTH_MASS_KG = 5.97219e24
SUN_EARTH_DISTANCE_M = 149_597_870_700.0


def sun_earth_system() -> SystemParameters:
    """Return normalized parameters for the Sun-Earth system."""

    mu = EARTH_MASS_KG / (SUN_MASS_KG + EARTH_MASS_KG)
    return SystemParameters(name="sun-earth", mu=mu, distance_m=SUN_EARTH_DISTANCE_M)
