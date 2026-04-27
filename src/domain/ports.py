from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Vehicle


class Clock(Protocol):
    def now(self) -> datetime: ...


class InventoryGateway(Protocol):
    def fetch_vehicles(self) -> list[Vehicle]: ...


class SnapshotRepository(Protocol):
    def load_latest(self) -> InventorySnapshot | None: ...
    def save(self, snapshot: InventorySnapshot) -> None: ...


class NotificationSender(Protocol):
    def notify_new_vehicle(self, vehicle: Vehicle) -> None: ...
    def notify_sold_vehicle(self, vehicle: Vehicle) -> None: ...
    def notify_error(self, message: str) -> None: ...
