from datetime import datetime

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Autopilot, Model, Paint, Source, Trim, Vehicle


def _vehicle(vid: str, price: int = 40000) -> Vehicle:
    return Vehicle(
        id=vid,
        source=Source.TESLA,
        model=Model.M3,
        title="Test",
        trim=Trim.PRAWD,
        year=2024,
        odometer=20000,
        price=price,
        paint=Paint.WHITE,
        autopilot=Autopilot.ENHANCED,
        city="Paris",
        link=f"https://www.tesla.com/fr_fr/m3/order/{vid}",
    )


NOW = datetime(2026, 4, 18, 12, 0, 0)
EARLIER = datetime(2026, 4, 18, 8, 0, 0)


class TestInventorySnapshotDiff:
    def test_diff_with_no_previous_returns_all_as_new(self) -> None:
        snapshot = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"), _vehicle("B")))
        diff = snapshot.diff(None)

        assert len(diff.new_vehicles) == 2
        assert len(diff.removed_vehicles) == 0

    def test_diff_no_changes(self) -> None:
        vehicles = (_vehicle("A"), _vehicle("B"))
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=vehicles)
        current = InventorySnapshot(checked_at=NOW, vehicles=vehicles)

        diff = current.diff(previous)

        assert not diff.has_changes
        assert len(diff.new_vehicles) == 0
        assert len(diff.removed_vehicles) == 0

    def test_diff_detects_new_vehicle(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=(_vehicle("A"),))
        current = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"), _vehicle("B")))

        diff = current.diff(previous)

        assert diff.has_changes
        assert len(diff.new_vehicles) == 1
        assert diff.new_vehicles[0].id == "B"
        assert len(diff.removed_vehicles) == 0

    def test_diff_detects_removed_vehicle(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=(_vehicle("A"), _vehicle("B")))
        current = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"),))

        diff = current.diff(previous)

        assert diff.has_changes
        assert len(diff.new_vehicles) == 0
        assert len(diff.removed_vehicles) == 1
        assert diff.removed_vehicles[0].id == "B"

    def test_diff_detects_both_new_and_removed(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=(_vehicle("A"), _vehicle("B")))
        current = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"), _vehicle("C")))

        diff = current.diff(previous)

        assert diff.has_changes
        assert {v.id for v in diff.new_vehicles} == {"C"}
        assert {v.id for v in diff.removed_vehicles} == {"B"}

    def test_diff_empty_snapshots(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=())
        current = InventorySnapshot(checked_at=NOW, vehicles=())

        diff = current.diff(previous)

        assert not diff.has_changes

    def test_ids_property(self) -> None:
        snapshot = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("X"), _vehicle("Y")))
        assert snapshot.ids == frozenset({"X", "Y"})
