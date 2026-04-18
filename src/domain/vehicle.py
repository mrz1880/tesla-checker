from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Paint(Enum):
    WHITE = "WHITE"
    BLACK = "BLACK"


class Trim(Enum):
    LRAWD = "LRAWD"
    PRAWD = "PRAWD"
    PAWD = "PAWD"


@dataclass(frozen=True)
class SearchCriteria:
    trims: frozenset[Trim]
    paints: frozenset[Paint]
    min_year: int
    max_odometer: int
    enhanced_autopilot: bool

    def matches(self, vehicle: Vehicle) -> bool:
        if vehicle.trim not in self.trims:
            return False
        if vehicle.paint not in self.paints:
            return False
        if vehicle.year < self.min_year:
            return False
        if vehicle.odometer > self.max_odometer:
            return False
        if self.enhanced_autopilot and not vehicle.has_enhanced_autopilot:
            return False
        return True


@dataclass(frozen=True)
class Vehicle:
    vin: str
    title: str
    trim: Trim
    year: int
    odometer: int
    price: int
    paint: Paint
    has_enhanced_autopilot: bool
    city: str

    @property
    def link(self) -> str:
        return f"https://www.tesla.com/fr_fr/m3/order/{self.vin}"

    @property
    def color_label(self) -> str:
        return "Blanc" if self.paint == Paint.WHITE else "Noir"
