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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vehicle):
            return NotImplemented
        return self.vin == other.vin

    def __hash__(self) -> int:
        return hash(self.vin)

    @property
    def link(self) -> str:
        return f"https://www.tesla.com/fr_fr/m3/order/{self.vin}"

    @property
    def color_label(self) -> str:
        return "Blanc" if self.paint == Paint.WHITE else "Noir"
