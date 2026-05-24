from __future__ import annotations

from dataclasses import dataclass

from src.domain.vehicle import Autopilot, Paint, Trim, Vehicle


@dataclass(frozen=True)
class SearchCriteria:
    trims: frozenset[Trim]
    paints: frozenset[Paint]
    min_year: int
    max_odometer: int
    accepted_autopilots: frozenset[Autopilot]

    def matches(self, vehicle: Vehicle) -> bool:
        if vehicle.trim not in self.trims:
            return False
        if vehicle.paint not in self.paints:
            return False
        if vehicle.year < self.min_year:
            return False
        if vehicle.odometer > self.max_odometer:
            return False
        return vehicle.autopilot in self.accepted_autopilots
