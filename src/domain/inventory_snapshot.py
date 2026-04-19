from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.vehicle import Vehicle


@dataclass(frozen=True)
class InventoryDiff:
    new_vehicles: tuple[Vehicle, ...]
    removed_vehicles: tuple[Vehicle, ...]

    @property
    def has_changes(self) -> bool:
        return len(self.new_vehicles) > 0 or len(self.removed_vehicles) > 0


@dataclass(frozen=True)
class InventorySnapshot:
    checked_at: datetime
    vehicles: tuple[Vehicle, ...]

    @property
    def vins(self) -> frozenset[str]:
        return frozenset(v.vin for v in self.vehicles)

    def diff(self, previous: InventorySnapshot | None) -> InventoryDiff:
        if previous is None:
            return InventoryDiff(
                new_vehicles=self.vehicles,
                removed_vehicles=(),
            )

        previous_vins = previous.vins
        current_vins = self.vins

        new = tuple(v for v in self.vehicles if v.vin not in previous_vins)
        removed = tuple(v for v in previous.vehicles if v.vin not in current_vins)

        return InventoryDiff(new_vehicles=new, removed_vehicles=removed)
