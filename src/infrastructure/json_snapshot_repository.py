from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Paint, Trim, Vehicle

log = logging.getLogger(__name__)


class JsonSnapshotRepository:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def _latest_file(self) -> Path:
        return self._data_dir / "latest.json"

    def load_latest(self) -> InventorySnapshot | None:
        if not self._latest_file.exists():
            return None

        with open(self._latest_file) as f:
            data = json.load(f)

        return self._deserialize(data)

    def save(self, snapshot: InventorySnapshot) -> None:
        data = self._serialize(snapshot)

        timestamp = snapshot.checked_at.strftime("%Y-%m-%d_%H-%M-%S")
        history_file = self._data_dir / f"check_{timestamp}.json"

        with open(history_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open(self._latest_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        log.info(f"Snapshot saved: {history_file}")

    @staticmethod
    def _serialize(snapshot: InventorySnapshot) -> dict:
        return {
            "checked_at": snapshot.checked_at.isoformat(),
            "vehicles": [
                {
                    "vin": v.vin,
                    "title": v.title,
                    "trim": v.trim.value,
                    "year": v.year,
                    "odometer": v.odometer,
                    "price": v.price,
                    "paint": v.paint.value,
                    "has_enhanced_autopilot": v.has_enhanced_autopilot,
                    "city": v.city,
                }
                for v in snapshot.vehicles
            ],
        }

    @staticmethod
    def _deserialize(data: dict) -> InventorySnapshot:
        vehicles = tuple(
            Vehicle(
                vin=v["vin"],
                title=v["title"],
                trim=Trim(v["trim"]),
                year=v["year"],
                odometer=v["odometer"],
                price=v["price"],
                paint=Paint(v["paint"]),
                has_enhanced_autopilot=v["has_enhanced_autopilot"],
                city=v["city"],
            )
            for v in data["vehicles"]
        )
        return InventorySnapshot(
            checked_at=datetime.fromisoformat(data["checked_at"]),
            vehicles=vehicles,
        )
