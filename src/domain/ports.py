from __future__ import annotations

from typing import Protocol

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Vehicle


class InventoryGateway(Protocol):
    def fetch_vehicles(self) -> list[Vehicle]: ...


class SnapshotRepository(Protocol):
    def load_latest(self) -> InventorySnapshot | None: ...
    def save(self, snapshot: InventorySnapshot) -> None: ...


class NotificationSender(Protocol):
    def notify_new_vehicle(self, vehicle: Vehicle) -> None: ...
