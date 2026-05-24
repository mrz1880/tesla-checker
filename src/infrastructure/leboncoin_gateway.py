from __future__ import annotations

import json
import logging
import re
import urllib.parse
from collections.abc import Mapping

from src.config import LeboncoinSearchConfig
from src.domain.vehicle import Model, Source, Trim, Vehicle
from src.infrastructure.lbc_parsing import (
    detect_autopilot,
    detect_paint,
    detect_trim,
    parse_int,
)
from src.infrastructure.lbc_schemas import LbcAd
from src.infrastructure.leboncoin_scraper import LeboncoinScraper

log = logging.getLogger(__name__)

_MODEL_PARAM: dict[Model, str] = {
    Model.M3: "TESLA_Model 3",
    Model.MY: "TESLA_Model Y",
}

_NEXT_DATA_RE = re.compile(
    r'id="__NEXT_DATA__"\s+type="application/json"[^>]*>(.+?)</script>',
    re.DOTALL,
)


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


def _body_from_html(html: str) -> str:
    if not html:
        return ""
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return ""
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, dict):
        return ""
    page_props = data.get("props", {}).get("pageProps", {})
    ad = page_props.get("ad") if isinstance(page_props, dict) else None
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
    def __init__(self, config: LeboncoinSearchConfig, scraper: LeboncoinScraper) -> None:
        self._config = config
        self._scraper = scraper
        self._search_url = _build_search_url(config)

    def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
        ads = self._scraper.fetch_search_ads(self._search_url)
        log.info(f"Leboncoin returned {len(ads)} ads for {self._config.model.value}.")

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
            html = self._scraper.fetch_detail_html(ad.url)
            body = _body_from_html(html)
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
