from collections.abc import Mapping
from datetime import datetime

import pytest

from src.application.check_inventory import CheckInventoryUseCase
from src.domain.inventory_snapshot import InventorySnapshot
from src.domain.search_criteria import SearchCriteria
from src.domain.vehicle import Autopilot, Model, Paint, Source, Trim, Vehicle

CRITERIA = SearchCriteria(
    trims=frozenset({Trim.PRAWD, Trim.PAWD}),
    paints=frozenset({Paint.WHITE, Paint.BLACK}),
    min_year=2024,
    max_odometer=50000,
    accepted_autopilots=frozenset({Autopilot.ENHANCED}),
)


def _vehicle(
    vid: str,
    trim: Trim = Trim.PRAWD,
    year: int = 2024,
    odometer: int = 20000,
    autopilot: Autopilot = Autopilot.ENHANCED,
) -> Vehicle:
    return Vehicle(
        id=vid,
        source=Source.TESLA,
        model=Model.M3,
        title="Test",
        trim=trim,
        year=year,
        odometer=odometer,
        price=40000,
        paint=Paint.WHITE,
        autopilot=autopilot,
        city="Paris",
        link=f"https://www.tesla.com/fr_fr/m3/order/{vid}",
    )


class FakeGateway:
    def __init__(self, vehicles: list[Vehicle]) -> None:
        self._vehicles = vehicles
        self.last_known: Mapping[str, Vehicle] | None = None

    def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
        self.last_known = known
        return self._vehicles


class FakeRepository:
    def __init__(self, latest: InventorySnapshot | None = None) -> None:
        self._latest = latest
        self.saved: InventorySnapshot | None = None

    def load_latest(self) -> InventorySnapshot | None:
        return self._latest

    def save(self, snapshot: InventorySnapshot) -> None:
        self.saved = snapshot


class FakeNotifier:
    def __init__(self) -> None:
        self.notified: list[Vehicle] = []
        self.sold: list[Vehicle] = []
        self.errors: list[str] = []

    def notify_new_vehicle(self, vehicle: Vehicle) -> None:
        self.notified.append(vehicle)

    def notify_sold_vehicle(self, vehicle: Vehicle) -> None:
        self.sold.append(vehicle)

    def notify_error(self, message: str) -> None:
        self.errors.append(message)


class FakeClock:
    def __init__(self) -> None:
        self._now = datetime(2026, 4, 19, 12, 0, 0)

    def now(self) -> datetime:
        return self._now


def _make_use_case(
    gateway: FakeGateway,
    repository: FakeRepository,
    notifier: FakeNotifier,
) -> CheckInventoryUseCase:
    return CheckInventoryUseCase(gateway, repository, notifier, FakeClock(), CRITERIA)


class TestCheckInventoryUseCase:
    def test_first_run_all_matching_are_new(self) -> None:
        vehicles = [_vehicle("A"), _vehicle("B")]
        gateway = FakeGateway(vehicles)
        repository = FakeRepository(latest=None)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert result.snapshot.vehicles == tuple(vehicles)
        assert len(result.diff.new_vehicles) == 2
        assert len(notifier.notified) == 2
        assert repository.saved is not None

    def test_filters_out_non_matching_vehicles(self) -> None:
        matching = _vehicle("A")
        too_old = _vehicle("B", year=2023)
        too_many_km = _vehicle("C", odometer=60000)
        no_autopilot = _vehicle("D", autopilot=Autopilot.BASIC)
        gateway = FakeGateway([matching, too_old, too_many_km, no_autopilot])
        repository = FakeRepository(latest=None)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert len(result.snapshot.vehicles) == 1
        assert result.snapshot.vehicles[0].id == "A"

    def test_no_notification_when_no_new_vehicles(self) -> None:
        vehicles = [_vehicle("A")]
        previous = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 8, 0, 0),
            vehicles=(vehicles[0],),
        )
        gateway = FakeGateway(vehicles)
        repository = FakeRepository(latest=previous)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert not result.diff.has_changes
        assert len(notifier.notified) == 0

    def test_notifies_only_new_vehicles(self) -> None:
        previous = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 8, 0, 0),
            vehicles=(_vehicle("A"),),
        )
        gateway = FakeGateway([_vehicle("A"), _vehicle("B")])
        repository = FakeRepository(latest=previous)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert len(result.diff.new_vehicles) == 1
        assert result.diff.new_vehicles[0].id == "B"
        assert len(notifier.notified) == 1
        assert notifier.notified[0].id == "B"

    def test_saves_snapshot_after_check(self) -> None:
        gateway = FakeGateway([_vehicle("A")])
        repository = FakeRepository(latest=None)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        use_case.execute()

        assert repository.saved is not None
        assert len(repository.saved.vehicles) == 1

    def test_notifies_sold_vehicles(self) -> None:
        previous = InventorySnapshot(
            checked_at=datetime(2026, 4, 18, 8, 0, 0),
            vehicles=(_vehicle("A"), _vehicle("B")),
        )
        gateway = FakeGateway([_vehicle("A")])
        repository = FakeRepository(latest=previous)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert len(result.diff.removed_vehicles) == 1
        assert result.diff.removed_vehicles[0].id == "B"
        assert len(notifier.sold) == 1
        assert notifier.sold[0].id == "B"
        assert len(notifier.notified) == 0

    def test_empty_gateway_response(self) -> None:
        gateway = FakeGateway([])
        repository = FakeRepository(latest=None)
        notifier = FakeNotifier()

        use_case = _make_use_case(gateway, repository, notifier)
        result = use_case.execute()

        assert len(result.snapshot.vehicles) == 0
        assert len(notifier.notified) == 0

    def test_notifies_error_when_gateway_fails(self) -> None:
        class FailingGateway:
            def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
                raise RuntimeError("Tesla API changed")

        repository = FakeRepository(latest=None)
        notifier = FakeNotifier()

        use_case = CheckInventoryUseCase(
            FailingGateway(), repository, notifier, FakeClock(), CRITERIA
        )

        with pytest.raises(RuntimeError, match="Tesla API changed"):
            use_case.execute()

        assert len(notifier.errors) == 1
        assert "Tesla API changed" in notifier.errors[0]
