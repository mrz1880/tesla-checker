from __future__ import annotations

from dataclasses import dataclass

from src.domain.vehicle import Paint, Trim, Vehicle


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
        return not (self.enhanced_autopilot and not vehicle.has_enhanced_autopilot)
