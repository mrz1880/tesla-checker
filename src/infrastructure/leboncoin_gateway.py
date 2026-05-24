from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
from collections.abc import Mapping

from camoufox import Camoufox
from curl_cffi import requests as cc

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


def _extract_next_data(html: str) -> dict[str, object]:
    match = _NEXT_DATA_RE.search(html)
    if not match:
        return {}
    parsed = json.loads(match.group(1))
    return parsed if isinstance(parsed, dict) else {}


def _dig(obj: object, *keys: str) -> object:
    """Walk a nested dict, returning None if any step is missing or non-dict."""
    current: object = obj
    for k in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(k)
    return current


def _ads_from_search_payload(data: dict[str, object]) -> list[LbcAd]:
    payload = _dig(data, "props", "pageProps", "searchData") or {}
    search_data = LbcSearchData.model_validate(payload)
    return search_data.ads


def _body_from_detail_payload(data: dict[str, object]) -> str:
    ad = _dig(data, "props", "pageProps", "ad")
    if not isinstance(ad, dict):
        return ""
    body = ad.get("body", "")
    return body if isinstance(body, str) else ""


def _warmup_and_get_session(search_url: str) -> tuple[list[LbcAd], dict[str, str], str]:
    """Open Camoufox once to load the search page; return parsed ads + cookies + user agent."""
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        log.info("Loading Leboncoin search page via Camoufox...")
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        raw = page.evaluate("""() => {
            const node = document.getElementById('__NEXT_DATA__');
            return node ? node.textContent : null;
        }""")
        if not raw:
            raise RuntimeError("Leboncoin: __NEXT_DATA__ not found on search page.")
        data = json.loads(raw)
        ads = _ads_from_search_payload(data)

        cookies = {c["name"]: c["value"] for c in page.context.cookies()}
        ua = page.evaluate("() => navigator.userAgent")

    return ads, cookies, ua


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


def _fetch_detail_body(
    session: cc.Session, ad_url: str, delay_seconds: float = 3.0
) -> str:
    time.sleep(delay_seconds)
    try:
        response = session.get(ad_url, timeout=30)
    except Exception as e:
        log.warning(f"Leboncoin detail request failed for {ad_url}: {e}")
        return ""
    if response.status_code != 200:
        log.warning(f"Leboncoin detail returned HTTP {response.status_code} for {ad_url}")
        return ""
    return _body_from_detail_payload(_extract_next_data(response.text))


class LeboncoinGateway:
    def __init__(self, config: LeboncoinSearchConfig) -> None:
        self._config = config
        self._search_url = _build_search_url(config)

    def fetch_vehicles(self, known: Mapping[str, Vehicle]) -> list[Vehicle]:
        ads, cookies, ua = _warmup_and_get_session(self._search_url)
        log.info(f"Leboncoin returned {len(ads)} ads for {self._config.model.value}.")

        with cc.Session(impersonate="firefox135") as session:
            session.headers.update(
                {
                    "User-Agent": ua,
                    "Accept": (
                        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.leboncoin.fr/",
                }
            )
            for name, value in cookies.items():
                session.cookies.set(name, value, domain=".leboncoin.fr")

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
                body = _fetch_detail_body(session, ad.url)
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
