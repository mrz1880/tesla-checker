from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Paint(Enum):
    WHITE = "WHITE"
    BLACK = "BLACK"
    OTHER = "OTHER"


class Trim(Enum):
    LRAWD = "LRAWD"
    PRAWD = "PRAWD"
    PAWD = "PAWD"


class Model(Enum):
    M3 = "M3"
    MY = "MY"


class Source(Enum):
    TESLA = "TESLA"
    LEBONCOIN = "LEBONCOIN"


class Autopilot(Enum):
    BASIC = "BASIC"
    ENHANCED = "ENHANCED"
    FSD = "FSD"


@dataclass(frozen=True)
class Vehicle:
    id: str
    source: Source
    model: Model
    title: str
    trim: Trim
    year: int
    odometer: int
    price: int
    paint: Paint
    autopilot: Autopilot
    city: str
    link: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vehicle):
            return NotImplemented
        return self.source == other.source and self.id == other.id

    def __hash__(self) -> int:
        return hash((self.source, self.id))

    @property
    def color_label(self) -> str:
        return {Paint.WHITE: "Blanc", Paint.BLACK: "Noir", Paint.OTHER: "Autre"}[self.paint]

    @property
    def model_label(self) -> str:
        return "M3" if self.model == Model.M3 else "MY"

    @property
    def source_label(self) -> str:
        return "Tesla" if self.source == Source.TESLA else "LBC"

    @property
    def autopilot_label(self) -> str:
        return {Autopilot.BASIC: "AP", Autopilot.ENHANCED: "EAP", Autopilot.FSD: "FSD"}[
            self.autopilot
        ]
