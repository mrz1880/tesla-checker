"""Shared Leboncoin scraping session.

Opening a fresh Camoufox per LBC profile triggers DataDome (two browser starts
from the same IP within seconds look bot-ish). This module keeps a single
Camoufox instance alive for the duration of a run: every LBC profile reuses
its cookies + user agent, and detail fetches go through curl-cffi with a
Firefox 135 TLS fingerprint.
"""

from __future__ import annotations

import json
import logging
import time
from types import TracebackType

from camoufox import Camoufox
from curl_cffi import requests as cc

from src.infrastructure.lbc_schemas import LbcAd, LbcSearchData

log = logging.getLogger(__name__)

_HOME_URL = "https://www.leboncoin.fr/"


def _extract_search_data(raw: str) -> LbcSearchData:
    data = json.loads(raw)
    payload = (
        data.get("props", {}).get("pageProps", {}).get("searchData", {})
        if isinstance(data, dict)
        else {}
    )
    return LbcSearchData.model_validate(payload)


class LeboncoinScraper:
    def __init__(self) -> None:
        self._browser_ctx: object | None = None
        self._browser: object | None = None
        self._page: object | None = None
        self._http: cc.Session | None = None

    def __enter__(self) -> LeboncoinScraper:
        log.info("Starting Leboncoin Camoufox session...")
        self._browser_ctx = Camoufox(headless=True)
        self._browser = self._browser_ctx.__enter__()
        self._page = self._browser.new_page()

        log.info("Warming up via Leboncoin homepage...")
        self._page.goto(_HOME_URL, wait_until="domcontentloaded", timeout=60000)
        self._page.wait_for_timeout(5000)

        cookies = self._page.context.cookies()
        ua = self._page.evaluate("() => navigator.userAgent")

        self._http = cc.Session(impersonate="firefox135")
        self._http.headers.update(
            {
                "User-Agent": ua,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": _HOME_URL,
            }
        )
        for c in cookies:
            self._http.cookies.set(c["name"], c["value"], domain=".leboncoin.fr")

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None
        if self._browser_ctx is not None:
            self._browser_ctx.__exit__(exc_type, exc, tb)
            self._browser_ctx = None
            self._browser = None
            self._page = None

    def fetch_search_ads(self, search_url: str) -> list[LbcAd]:
        if self._page is None:
            raise RuntimeError("LeboncoinScraper used outside its context manager.")
        log.info(f"Loading Leboncoin search page: {search_url}")
        self._page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        self._page.wait_for_timeout(4000)

        raw = self._page.evaluate("""() => {
            const node = document.getElementById('__NEXT_DATA__');
            return node ? node.textContent : null;
        }""")
        if not raw:
            raise RuntimeError(
                "Leboncoin: __NEXT_DATA__ not found on search page "
                "(likely DataDome block)."
            )

        # Refresh cookies on the http session — DataDome can rotate tokens.
        self._refresh_cookies()

        return _extract_search_data(raw).ads

    def fetch_detail_html(self, ad_url: str, delay_seconds: float = 3.0) -> str:
        if self._http is None:
            raise RuntimeError("LeboncoinScraper used outside its context manager.")
        time.sleep(delay_seconds)
        try:
            response = self._http.get(ad_url, timeout=30)
        except Exception as e:
            log.warning(f"Leboncoin detail request failed for {ad_url}: {e}")
            return ""
        if response.status_code != 200:
            log.warning(
                f"Leboncoin detail returned HTTP {response.status_code} for {ad_url}"
            )
            return ""
        return response.text

    def _refresh_cookies(self) -> None:
        if self._page is None or self._http is None:
            return
        for c in self._page.context.cookies():
            self._http.cookies.set(c["name"], c["value"], domain=".leboncoin.fr")
