#!/usr/bin/env python3
"""Composition root - wires dependencies and runs the use case."""

import logging
import sys
from pathlib import Path

from src.application.check_inventory import CheckInventoryUseCase
from src.config import load_config
from src.domain.search_criteria import SearchCriteria
from src.domain.vehicle import Paint, Trim
from src.infrastructure.json_snapshot_repository import JsonSnapshotRepository
from src.infrastructure.ntfy_notifier import NtfyNotifier
from src.infrastructure.system_clock import SystemClock
from src.infrastructure.tesla_playwright_gateway import TeslaPlaywrightGateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main() -> None:
    config = load_config()

    criteria = SearchCriteria(
        trims=frozenset(Trim(t) for t in config.search.trims),
        paints=frozenset(Paint(p) for p in config.search.paints),
        min_year=config.search.min_year,
        max_odometer=config.search.max_odometer,
        enhanced_autopilot=config.search.require_enhanced_autopilot,
    )

    gateway = TeslaPlaywrightGateway(config.search)
    repository = JsonSnapshotRepository(Path(config.results_dir))
    notifier = NtfyNotifier(topic=config.notify.topic, base_url=config.notify.base_url)
    clock = SystemClock()

    use_case = CheckInventoryUseCase(
        gateway=gateway,
        repository=repository,
        notifier=notifier,
        clock=clock,
        criteria=criteria,
    )

    result = use_case.execute()

    if result.diff.new_vehicles:
        sys.exit(2)


if __name__ == "__main__":
    main()
