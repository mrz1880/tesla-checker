from datetime import datetime
from pathlib import Path

import pytest

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Paint, Trim, Vehicle
from src.infrastructure.json_snapshot_repository import JsonSnapshotRepository


def _vehicle(vin: str = "VIN001") -> Vehicle:
    return Vehicle(
        vin=vin,
        title="Premium Grande Autonomie TI",
        trim=Trim.PRAWD,
        year=2024,
        odometer=29752,
        price=40100,
        paint=Paint.WHITE,
        has_enhanced_autopilot=True,
        city="Paris",
    )


@pytest.fixture
def repo(tmp_path: Path) -> JsonSnapshotRepository:
    return JsonSnapshotRepository(tmp_path)


class TestJsonSnapshotRepository:
    def test_load_latest_returns_none_when_empty(self, repo: JsonSnapshotRepository) -> None:
        assert repo.load_latest() is None

    def test_save_then_load(self, repo: JsonSnapshotRepository) -> None:
        snapshot = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 12, 0, 0),
            vehicles=(_vehicle("A"), _vehicle("B")),
        )

        repo.save(snapshot)
        loaded = repo.load_latest()

        assert loaded is not None
        assert loaded.checked_at == snapshot.checked_at
        assert len(loaded.vehicles) == 2
        assert loaded.vehicles[0].vin == "A"
        assert loaded.vehicles[1].vin == "B"

    def test_save_creates_history_file(self, repo: JsonSnapshotRepository, tmp_path: Path) -> None:
        snapshot = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 12, 0, 0),
            vehicles=(_vehicle(),),
        )
        repo.save(snapshot)

        history_files = list(tmp_path.glob("check_*.json"))
        assert len(history_files) == 1

    def test_latest_is_overwritten_on_second_save(self, repo: JsonSnapshotRepository) -> None:
        first = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 8, 0, 0),
            vehicles=(_vehicle("A"),),
        )
        second = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 18, 0, 0),
            vehicles=(_vehicle("A"), _vehicle("B")),
        )

        repo.save(first)
        repo.save(second)

        loaded = repo.load_latest()
        assert loaded is not None
        assert len(loaded.vehicles) == 2
        assert loaded.checked_at == second.checked_at

    def test_roundtrip_preserves_all_fields(self, repo: JsonSnapshotRepository) -> None:
        vehicle = Vehicle(
            vin="LRW3E7ET8RC170223",
            title="Performance Transmission Intégrale",
            trim=Trim.PAWD,
            year=2024,
            odometer=25203,
            price=48700,
            paint=Paint.BLACK,
            has_enhanced_autopilot=True,
            city="Saint-Priest",
        )
        snapshot = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 12, 30, 45),
            vehicles=(vehicle,),
        )

        repo.save(snapshot)
        loaded = repo.load_latest()

        assert loaded is not None
        v = loaded.vehicles[0]
        assert v.vin == vehicle.vin
        assert v.title == vehicle.title
        assert v.trim == vehicle.trim
        assert v.year == vehicle.year
        assert v.odometer == vehicle.odometer
        assert v.price == vehicle.price
        assert v.paint == vehicle.paint
        assert v.has_enhanced_autopilot == vehicle.has_enhanced_autopilot
        assert v.city == vehicle.city
