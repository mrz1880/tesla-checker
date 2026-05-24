#!/usr/bin/env python3
"""Composition root - wires dependencies and runs all configured profiles."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.application.check_inventory import CheckInventoryUseCase
from src.config import AppConfig, LeboncoinSearchConfig, TeslaSearchConfig, load_config
from src.domain.ports import InventoryGateway
from src.domain.search_criteria import SearchCriteria
from src.infrastructure.json_snapshot_repository import JsonSnapshotRepository
from src.infrastructure.leboncoin_gateway import LeboncoinGateway
from src.infrastructure.ntfy_notifier import NtfyNotifier
from src.infrastructure.system_clock import SystemClock
from src.infrastructure.tesla_playwright_gateway import TeslaPlaywrightGateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("tesla-checker")


@dataclass(frozen=True)
class SearchProfile:
    name: str
    gateway: InventoryGateway
    criteria: SearchCriteria
    data_dir: Path


def _tesla_profile(config: TeslaSearchConfig, base_dir: Path) -> SearchProfile:
    return SearchProfile(
        name=f"tesla-{config.model.value.lower()}",
        gateway=TeslaPlaywrightGateway(config),
        criteria=SearchCriteria(
            trims=frozenset(config.trims),
            paints=frozenset(config.paints),
            min_year=config.min_year,
            max_odometer=config.max_odometer,
            accepted_autopilots=frozenset(config.accepted_autopilots),
        ),
        data_dir=base_dir / f"tesla-{config.model.value.lower()}",
    )


def _lbc_profile(config: LeboncoinSearchConfig, base_dir: Path) -> SearchProfile:
    return SearchProfile(
        name=f"lbc-{config.model.value.lower()}",
        gateway=LeboncoinGateway(config),
        criteria=SearchCriteria(
            trims=frozenset(config.trims),
            paints=frozenset(config.paints),
            min_year=config.min_year,
            max_odometer=config.max_odometer,
            accepted_autopilots=frozenset(config.accepted_autopilots),
        ),
        data_dir=base_dir / f"lbc-{config.model.value.lower()}",
    )


def _build_profiles(config: AppConfig) -> list[SearchProfile]:
    base_dir = Path(config.results_dir)
    return [
        _tesla_profile(config.tesla_m3, base_dir),
        _lbc_profile(config.lbc_m3, base_dir),
        _lbc_profile(config.lbc_my, base_dir),
    ]


def main() -> None:
    config = load_config()
    notifier = NtfyNotifier(topic=config.notify.topic, base_url=config.notify.base_url)
    clock = SystemClock()

    profiles = _build_profiles(config)
    failed = 0

    for profile in profiles:
        log.info("=" * 60)
        log.info(f"Profile: {profile.name}")
        log.info("=" * 60)
        try:
            use_case = CheckInventoryUseCase(
                gateway=profile.gateway,
                repository=JsonSnapshotRepository(profile.data_dir),
                notifier=notifier,
                clock=clock,
                criteria=profile.criteria,
            )
            use_case.execute()
        except Exception as e:
            log.exception(f"Profile {profile.name} failed: {e}")
            failed += 1

    if failed:
        log.error(f"{failed}/{len(profiles)} profile(s) failed.")


if __name__ == "__main__":
    main()
