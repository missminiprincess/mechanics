"""Known CR3BP systems."""

import math
from collections.abc import Callable

from mechanics.core.models import SystemParameters

GRAVITATIONAL_CONSTANT = 6.67430e-11
SUN_MASS_KG = 1.9885e30
EARTH_MASS_KG = 5.97219e24
MOON_MASS_KG = 7.34767309e22
JUPITER_MASS_KG = 1.89813e27
SUN_EARTH_DISTANCE_M = 149_597_870_700.0
EARTH_MOON_DISTANCE_M = 384_400_000.0
SUN_JUPITER_DISTANCE_M = 778_479_000_000.0


def _normalized_system(
    *,
    name: str,
    primary_name: str,
    secondary_name: str,
    primary_mass_kg: float,
    secondary_mass_kg: float,
    distance_m: float,
) -> SystemParameters:
    """Build normalized CR3BP parameters from physical constants."""

    total_mass = primary_mass_kg + secondary_mass_kg
    return SystemParameters(
        name=name,
        primary_name=primary_name,
        secondary_name=secondary_name,
        mu=secondary_mass_kg / total_mass,
        distance_m=distance_m,
        time_unit_s=math.sqrt(distance_m**3 / (GRAVITATIONAL_CONSTANT * total_mass)),
    )


def sun_earth_system() -> SystemParameters:
    """Return normalized parameters for the Sun-Earth system."""

    return _normalized_system(
        name="sun-earth",
        primary_name="Солнце",
        secondary_name="Земля",
        primary_mass_kg=SUN_MASS_KG,
        secondary_mass_kg=EARTH_MASS_KG,
        distance_m=SUN_EARTH_DISTANCE_M,
    )


def earth_moon_system() -> SystemParameters:
    """Return normalized parameters for the Earth-Moon system."""

    return _normalized_system(
        name="earth-moon",
        primary_name="Земля",
        secondary_name="Луна",
        primary_mass_kg=EARTH_MASS_KG,
        secondary_mass_kg=MOON_MASS_KG,
        distance_m=EARTH_MOON_DISTANCE_M,
    )


def sun_jupiter_system() -> SystemParameters:
    """Return normalized parameters for the Sun-Jupiter system."""

    return _normalized_system(
        name="sun-jupiter",
        primary_name="Солнце",
        secondary_name="Юпитер",
        primary_mass_kg=SUN_MASS_KG,
        secondary_mass_kg=JUPITER_MASS_KG,
        distance_m=SUN_JUPITER_DISTANCE_M,
    )


SYSTEM_FACTORIES: dict[str, Callable[[], SystemParameters]] = {
    "sun-earth": sun_earth_system,
    "earth-moon": earth_moon_system,
    "sun-jupiter": sun_jupiter_system,
}


def available_system_names() -> tuple[str, ...]:
    """Return supported system identifiers."""

    return tuple(SYSTEM_FACTORIES)


def get_system(name: str) -> SystemParameters:
    """Return one supported CR3BP system by CLI identifier."""

    key = name.strip().lower().replace("_", "-")
    try:
        return SYSTEM_FACTORIES[key]()
    except KeyError as exc:
        available = ", ".join(available_system_names())
        raise ValueError(f"Unknown system '{name}'. Available systems: {available}") from exc
