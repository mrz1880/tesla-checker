#!/usr/bin/env python3
"""Composition root - wires dependencies and runs the use case."""

import logging
import os
import sys
from pathlib import Path

from src.application.check_inventory import CheckInventoryUseCase
from src.domain.vehicle import Paint, SearchCriteria, Trim
from src.infrastructure.json_snapshot_repository import JsonSnapshotRepository
from src.infrastructure.ntfy_notifier import NtfyNotifier
from src.infrastructure.tesla_playwright_gateway import TeslaPlaywrightGateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

CRITERIA = SearchCriteria(
    trims=frozenset({Trim.LRAWD, Trim.PRAWD, Trim.PAWD}),
    paints=frozenset({Paint.WHITE, Paint.BLACK}),
    min_year=2024,
    max_odometer=50000,
    enhanced_autopilot=True,
)


def main() -> None:
    data_dir = Path(os.environ.get("RESULTS_DIR", "/data"))
    ntfy_topic = os.environ.get("NTFY_TOPIC", "")
    ntfy_url = os.environ.get("NTFY_URL", "https://ntfy.sh")

    gateway = TeslaPlaywrightGateway()
    repository = JsonSnapshotRepository(data_dir)
    notifier = NtfyNotifier(topic=ntfy_topic, base_url=ntfy_url)

    use_case = CheckInventoryUseCase(
        gateway=gateway,
        repository=repository,
        notifier=notifier,
        criteria=CRITERIA,
    )

    result = use_case.execute()

    if result.diff.new_vehicles:
        sys.exit(2)


if __name__ == "__main__":
    main()
