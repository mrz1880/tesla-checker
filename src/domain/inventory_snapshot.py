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
    def ids(self) -> frozenset[str]:
        return frozenset(v.id for v in self.vehicles)

    def diff(self, previous: InventorySnapshot | None) -> InventoryDiff:
        if previous is None:
            return InventoryDiff(
                new_vehicles=self.vehicles,
                removed_vehicles=(),
            )

        previous_ids = previous.ids
        current_ids = self.ids

        new = tuple(v for v in self.vehicles if v.id not in previous_ids)
        removed = tuple(v for v in previous.vehicles if v.id not in current_ids)

        return InventoryDiff(new_vehicles=new, removed_vehicles=removed)
