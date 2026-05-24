from __future__ import annotations

import json
import logging
import urllib.parse
from collections.abc import Mapping

from camoufox import Camoufox
from playwright.sync_api import Page

from src.config import LeboncoinSearchConfig
from src.domain.vehicle import Model, Source, Trim, Vehicle
from src.infrastructure.lbc_parsing import (
    detect_autopilot,
    detect_paint,
    detect_trim,
    parse_int,
)
from src.infrastructure.lbc_schemas import LbcAd, LbcSearchData

log = logging.getLogger(__name__)

_MODEL_PARAM: dict[Model, str] = {
    Model.M3: "TESLA_Model 3",
    Model.MY: "TESLA_Model Y",
}


def _attribute(ad: LbcAd, key: str) -> str:
    for a in ad.attributes:
        if a.key == key:
            return a.value
    return ""


def _build_search_url(config: LeboncoinSearchConfig) -> str:
    params = {
        "category": "2",
        "u_car_brand": "TESLA",
        "u_car_model": _MODEL_PARAM[config.model],
        "regdate": f"{config.min_year}-max",
        "mileage": f"min-{config.max_odometer}",
    }
    return "https://www.leboncoin.fr/recherche?" + urllib.parse.urlencode(params)


def _extract_search_ads(page: Page) -> list[LbcAd]:
    raw = page.evaluate("""() => {
        const node = document.getElementById('__NEXT_DATA__');
        return node ? node.textContent : null;
    }""")
    if not raw:
        raise RuntimeError("Leboncoin: __NEXT_DATA__ not found on search page.")
    data = json.loads(raw)
    payload = (
        data.get("props", {}).get("pageProps", {}).get("searchData", {})
    )
    search_data = LbcSearchData.model_validate(payload)
    return search_data.ads


def _extract_detail_body(page: Page, ad_url: str) -> str:
    page.goto(ad_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2000)
    raw = page.evaluate("""() => {
        const node = document.getElementById('__NEXT_DATA__');
        return node ? node.textContent : null;
    }""")
    if not raw:
        log.warning(f"Leboncoin detail page returned no __NEXT_DATA__ (likely DataDome): {ad_url}")
        return ""
    data = json.loads(raw)
    ad = data.get("props", {}).get("pageProps", {}).get("ad")
    if not isinstance(ad, dict):
        return ""
    body = ad.get("body", "")
    return body if isinstance(body, str) else ""


def _build_vehicle(
    ad: LbcAd,
    body: str,
    model: Model,
    title: str,
    trim: Trim,
    year: int,
    odometer: int,
) -> Vehicle:
    return Vehicle(
        id=str(ad.list_id),
        source=Source.LEBONCOIN,
        model=model,
        title=title,
        trim=trim,
        year=year,
        odometer=odometer,
        price=ad.price[0] if ad.price else 0,
        paint=detect_paint(body),
        autopilot=detect_autopilot(body),
        city=ad.location.city or "",
        link=ad.url,
    )


def _prefilter(ad: LbcAd, config: LeboncoinSearchConfig) -> tuple[Trim, int, int] | None:
    year_str = _attribute(ad, "regdate")
    mileage_str = _attribute(ad, "mileage")
    version = _attribute(ad, "u_car_version") or ad.subject

    year = parse_int(year_str)
    mileage = parse_int(mileage_str)
    if year is None or mileage is None:
        return None
    if year < config.min_year or mileage > config.max_odometer:
        return None

    trim = detect_trim(version)
    if trim is None or trim not in config.trims:
        return None

    return trim, year, mileage


class LeboncoinGateway:
    def __init__(self, config: LeboncoinSearchConfig) -> None:
        self._config = config
        self._search_url = _build_search_url(config)

    def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
        with Camoufox(headless=True) as browser:
            page = browser.new_page()

            log.info(f"Loading Leboncoin search for {self._config.model.value}...")
            page.goto(self._search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            ads = _extract_search_ads(page)
            log.info(f"Leboncoin returned {len(ads)} ads.")

            vehicles: list[Vehicle] = []
            for ad in ads:
                pre = _prefilter(ad, self._config)
                if pre is None:
                    continue
                trim, year, odometer = pre

                ad_id = str(ad.list_id)
                cached = known.get(ad_id)
                if cached is not None:
                    vehicles.append(cached)
                    continue

                log.info(f"Fetching detail for new ad {ad_id}: {ad.subject[:60]}")
                page.wait_for_timeout(3000)  # space requests to dodge DataDome
                body = _extract_detail_body(page, ad.url)

                vehicles.append(
                    _build_vehicle(
                        ad=ad,
                        body=body,
                        model=self._config.model,
                        title=ad.subject,
                        trim=trim,
                        year=year,
                        odometer=odometer,
                    )
                )

            log.info(f"Leboncoin gateway returning {len(vehicles)} candidate vehicle(s).")

        return vehicles
