from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.inventory_snapshot import InventoryDiff, InventorySnapshot
from src.domain.ports import Clock, InventoryGateway, NotificationSender, SnapshotRepository
from src.domain.search_criteria import SearchCriteria

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    snapshot: InventorySnapshot
    diff: InventoryDiff


class CheckInventoryUseCase:
    def __init__(
        self,
        gateway: InventoryGateway,
        repository: SnapshotRepository,
        notifier: NotificationSender,
        clock: Clock,
        criteria: SearchCriteria,
    ) -> None:
        self._gateway = gateway
        self._repository = repository
        self._notifier = notifier
        self._clock = clock
        self._criteria = criteria

    def execute(self) -> CheckResult:
        log.info("Fetching inventory from Tesla...")
        try:
            all_vehicles = self._gateway.fetch_vehicles()
        except Exception as e:
            log.error(f"Failed to fetch inventory: {e}")
            self._notifier.notify_error(
                f"Impossible de récupérer l'inventaire Tesla.\n\nErreur: {e}"
            )
            raise
        log.info(f"Fetched {len(all_vehicles)} vehicle(s) from Tesla API.")

        matching = [v for v in all_vehicles if self._criteria.matches(v)]
        log.info(f"{len(matching)} vehicle(s) match search criteria.")

        for v in matching:
            log.info(
                f"  {v.title} ({v.year}) - {v.price:,} EUR"
                f" - {v.odometer:,} km - {v.color_label} - {v.city}"
            )

        snapshot = InventorySnapshot(
            checked_at=self._clock.now(),
            vehicles=tuple(matching),
        )

        previous = self._repository.load_latest()
        diff = snapshot.diff(previous)

        if diff.new_vehicles:
            log.info(f"{len(diff.new_vehicles)} new vehicle(s) detected!")
            for vehicle in diff.new_vehicles:
                self._notifier.notify_new_vehicle(vehicle)
        else:
            log.info("No new vehicles since last check.")

        if diff.removed_vehicles:
            log.info(f"{len(diff.removed_vehicles)} vehicle(s) removed since last check.")
            for vehicle in diff.removed_vehicles:
                self._notifier.notify_sold_vehicle(vehicle)

        self._repository.save(snapshot)

        return CheckResult(snapshot=snapshot, diff=diff)
