from datetime import datetime

from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.vehicle import Paint, Trim, Vehicle


def _vehicle(vin: str, price: int = 40000) -> Vehicle:
    return Vehicle(
        vin=vin,
        title="Test",
        trim=Trim.PRAWD,
        year=2024,
        odometer=20000,
        price=price,
        paint=Paint.WHITE,
        has_enhanced_autopilot=True,
        city="Paris",
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
        assert diff.new_vehicles[0].vin == "B"
        assert len(diff.removed_vehicles) == 0

    def test_diff_detects_removed_vehicle(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=(_vehicle("A"), _vehicle("B")))
        current = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"),))

        diff = current.diff(previous)

        assert diff.has_changes
        assert len(diff.new_vehicles) == 0
        assert len(diff.removed_vehicles) == 1
        assert diff.removed_vehicles[0].vin == "B"

    def test_diff_detects_both_new_and_removed(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=(_vehicle("A"), _vehicle("B")))
        current = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("A"), _vehicle("C")))

        diff = current.diff(previous)

        assert diff.has_changes
        assert {v.vin for v in diff.new_vehicles} == {"C"}
        assert {v.vin for v in diff.removed_vehicles} == {"B"}

    def test_diff_empty_snapshots(self) -> None:
        previous = InventorySnapshot(checked_at=EARLIER, vehicles=())
        current = InventorySnapshot(checked_at=NOW, vehicles=())

        diff = current.diff(previous)

        assert not diff.has_changes

    def test_vins_property(self) -> None:
        snapshot = InventorySnapshot(checked_at=NOW, vehicles=(_vehicle("X"), _vehicle("Y")))
        assert snapshot.vins == frozenset({"X", "Y"})
