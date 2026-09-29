"""No-key public social collector using a real JS browser.

Captures public pages only. It never exports cookies, tokens, local/session storage,
or bypasses login/CAPTCHA/rate-limit controls. Authenticated owner-browser lanes can
be added separately through OpenCLI/CDP without copying credentials into evidence.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urlsplit, urlunsplit

from playwright.async_api import Browser, BrowserContext, Page, Response, async_playwright

from src.collectors.base import BaseCollector
from src.collectors.coverage_tracker import CoverageStatus, CoverageTracker


CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        host = parts.netloc.lower().replace("www.threads.net", "www.threads.com")
        return urlunsplit((parts.scheme or "https", host, parts.path.rstrip("/"), "", ""))
    except Exception:
        return url


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


class PublicBrowserCollector:
    COLLECTOR_NAME = "playwright_public_browser_v1"

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        snapshot_dir: Optional[Path] = None,
        coverage: Optional[CoverageTracker] = None,
        headless: bool = True,
    ) -> None:
        self.collector = BaseCollector(
            storage_dir=storage_dir or Path("D:/ABANGCOLEK/data/raw"),
            collector_name=self.COLLECTOR_NAME,
        )
        self.snapshot_dir = Path(snapshot_dir or "D:/ABANGCOLEK/data/browser_snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.coverage = coverage or CoverageTracker()
        self.headless = headless

    @staticmethod
    def _chrome_path() -> Optional[str]:
        for p in CHROME_PATHS:
            if p.exists():
                return str(p)
        return None

    async def _launch(self):
        pw = await async_playwright().start()
        kwargs: Dict[str, Any] = {
            "headless": self.headless,
            "args": [],
        }
        executable = self._chrome_path()
        if executable:
            kwargs["executable_path"] = executable
        browser = await pw.chromium.launch(**kwargs)
        context = await browser.new_context(
            viewport={"width": 1365, "height": 900},
            locale="en-US",
        )
        return pw, browser, context

    async def _goto_stable(self, page: Page, url: str) -> Tuple[Optional[Response], Optional[str]]:
        last_error: Optional[str] = None
        for attempt in range(3):
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=35000)
                await page.wait_for_timeout(3500 + attempt * 1000)
                return response, None
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                try:
                    await page.wait_for_timeout(1800)
                    if page.url and page.url not in {"about:blank", ""}:
                        return None, None
                except Exception:
                    pass
        return None, last_error

    async def _page_snapshot(self, page: Page, source_url: str, platform: str) -> Dict[str, Any]:
        final_url = page.url
        title = ""
        text = ""
        html = ""
        links: List[str] = []
        times: List[Dict[str, str]] = []
        metas: Dict[str, str] = {}
        try:
            title = await page.title()
        except Exception:
            pass
        try:
            text = await page.locator("body").inner_text(timeout=10000)
        except Exception:
            pass
        try:
            html = await page.content()
        except Exception:
            pass
        try:
            links = await page.locator("a[href]").evaluate_all(
                "els => els.map(a => a.href).filter(Boolean)"
            )
        except Exception:
            pass
        try:
            times = await page.locator("time").evaluate_all(
                "els => els.map(x => ({datetime:x.getAttribute('datetime')||'', text:(x.innerText||'').trim()}))"
            )
        except Exception:
            pass
        try:
            metas = await page.locator("meta[property^='og:'],meta[name='description']").evaluate_all(
                "els => Object.fromEntries(els.map(x => [x.getAttribute('property')||x.getAttribute('name'), x.getAttribute('content')||'']))"
            )
        except Exception:
            pass

        html_hash = _sha256_text(html)
        snap_dir = self.snapshot_dir / platform
        snap_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snap_dir / f"{html_hash}.html"
        if html and not snapshot_path.exists():
            snapshot_path.write_text(html, encoding="utf-8", errors="replace")

        return {
            "requested_url": source_url,
            "final_url": final_url,
            "title": title,
            "visible_text": text,
            "links": list(dict.fromkeys(links)),
            "time_elements": times,
            "meta": metas,
            "html_sha256": html_hash,
            "html_snapshot": str(snapshot_path) if html else None,
            "captured_at": _now(),
        }

    @staticmethod
    def _challenge_or_blocked(snapshot: Dict[str, Any], status: Optional[int]) -> Optional[str]:
        hay = f"{snapshot.get('title','')}\n{snapshot.get('visible_text','')}".lower()
        markers = [
            "verify to continue", "security check", "captcha", "unusual traffic",
            "access denied", "challenge required", "something went wrong",
        ]
        if status in {401, 403, 429}:
            return f"HTTP_{status}"
        for marker in markers:
            if marker in hay:
                return marker.upper().replace(" ", "_")
        return None

    def _ingest_snapshot(
        self,
        platform: str,
        source_id: str,
        source_type: str,
        snapshot: Dict[str, Any],
        status: Optional[int],
    ) -> Dict[str, Any]:
        final_url = snapshot.get("final_url") or snapshot.get("requested_url") or ""
        receipt = {
            "capture_method": "PLAYWRIGHT_PUBLIC_BROWSER",
            "captured_at": snapshot.get("captured_at"),
            "requested_url": snapshot.get("requested_url"),
            "final_url": final_url,
            "http_status": status,
            "html_sha256": snapshot.get("html_sha256"),
            "browser": "system-chromium",
            "credentials_exported": False,
        }
        payload = {
            **snapshot,
            "data_origin": "PUBLIC_PLATFORM",
            "evidence_class": "RAW_EVIDENCE",
            "synthetic": False,
            "authoritative": True,
            "provenance_verified": True,
        }
        published_at = ""
        for t in snapshot.get("time_elements") or []:
            if t.get("datetime"):
                published_at = t["datetime"]
                break
        return self.collector.ingest(
            raw_data=payload,
            platform=platform,
            source_id=source_id,
            source_native_id=source_id,
            source_type=source_type,
            source_url=final_url,
            published_at=published_at,
            access_method="PUBLIC_BROWSER",
            capture_receipt=receipt,
            provenance_verified=True,
        )

    @staticmethod
    def _extract_post_links(platform: str, links: Iterable[str], handle: str) -> List[str]:
        out: List[str] = []
        h = re.escape(handle.lstrip("@"))
        patterns = {
            "threads": re.compile(rf"https://www\.threads\.(?:com|net)/@{h}/post/[^/?#]+", re.I),
            "instagram": re.compile(rf"https://www\.instagram\.com/{h}/(?:p|reel)/[^/?#]+", re.I),
            "tiktok": re.compile(rf"https://www\.tiktok\.com/@{h}/(?:video|photo)/\d+", re.I),
            "facebook": re.compile(r"https://www\.facebook\.com/.+/(?:posts|videos|reel)/[^?#]+", re.I),
        }
        pat = patterns.get(platform)
        if not pat:
            return []
        for url in links:
            canonical = _canonical_url(url)
            if pat.search(canonical):
                out.append(canonical)
        return list(dict.fromkeys(out))

    async def collect_profile(
        self,
        platform: str,
        handle: str,
        profile_url: str,
        *,
        max_scrolls: int = 120,
        stable_cycles: int = 6,
        collect_post_pages: bool = True,
        max_post_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        source_name = f"{handle}:public-browser"
        records: List[Dict[str, Any]] = []
        discovered: Set[str] = set()
        pw = browser = context = None
        page: Optional[Page] = None
        status: Optional[int] = None
        block_reason: Optional[str] = None
        try:
            pw, browser, context = await self._launch()
            page = await context.new_page()
            response, nav_error = await self._goto_stable(page, profile_url)
            status = response.status if response else None
            if nav_error and (not page.url or page.url == "about:blank"):
                raise RuntimeError(nav_error)

            profile = await self._page_snapshot(page, profile_url, platform)
            block_reason = self._challenge_or_blocked(profile, status)
            profile_id = f"profile_{handle.lstrip('@')}"
            records.append(self._ingest_snapshot(platform, profile_id, "public_profile_snapshot", profile, status))
            discovered.update(self._extract_post_links(platform, profile.get("links") or [], handle))

            stable = 0
            last_count = len(discovered)
            for _ in range(max_scrolls):
                if block_reason:
                    break
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1100)
                    links = await page.locator("a[href]").evaluate_all("els => els.map(a => a.href).filter(Boolean)")
                    discovered.update(self._extract_post_links(platform, links, handle))
                except Exception:
                    break
                if len(discovered) == last_count:
                    stable += 1
                else:
                    stable = 0
                    last_count = len(discovered)
                if stable >= stable_cycles:
                    break

            ordered = sorted(discovered)
            discovery_dir = Path("D:/ABANGCOLEK/data/coverage/discovery")
            discovery_dir.mkdir(parents=True, exist_ok=True)
            discovery_path = discovery_dir / f"{platform}_{handle.lstrip('@')}_public_urls.json"
            prior_urls: Set[str] = set()
            prior_runs = 0
            if discovery_path.exists():
                try:
                    prior = json.loads(discovery_path.read_text(encoding="utf-8"))
                    prior_urls.update(prior.get("urls") or [])
                    prior_runs = int(prior.get("runs", 1))
                except Exception:
                    pass
            prior_urls.update(ordered)
            ordered = sorted(prior_urls)
            discovery_payload = {
                "platform": platform,
                "handle": handle,
                "profile_url": profile_url,
                "captured_at": _now(),
                "collector": self.COLLECTOR_NAME,
                "runs": prior_runs + 1,
                "count": len(ordered),
                "urls": ordered,
            }
            discovery_path.write_text(json.dumps(discovery_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            if max_post_pages is not None:
                ordered = ordered[:max_post_pages]
            if collect_post_pages:
                for idx, post_url in enumerate(ordered, start=1):
                    response, nav_error = await self._goto_stable(page, post_url)
                    post_status = response.status if response else None
                    if nav_error and (not page.url or page.url == "about:blank"):
                        continue
                    snap = await self._page_snapshot(page, post_url, platform)
                    reason = self._challenge_or_blocked(snap, post_status)
                    if reason:
                        block_reason = reason
                        break
                    native_id = post_url.rstrip("/").split("/")[-1]
                    records.append(self._ingest_snapshot(platform, native_id, "public_post_snapshot", snap, post_status))

            if block_reason:
                cov = CoverageStatus.PARTIAL_AUTH_LIMIT
                gaps = [f"Collection encountered platform challenge/block: {block_reason}", "Owner-controlled browser session may expose additional public/history content"]
            else:
                cov = CoverageStatus.PARTIAL_UNKNOWN
                gaps = ["Public browser collection cannot prove deleted/private history completeness", "Owner export/browser session may expose additional history"]
            self.coverage.register_source(
                platform, source_name, cov,
                record_count=len(records),
                posts_recovered=max(0, len(records)-1),
                pagination_exhausted=False,
                data_origin="PUBLIC_PLATFORM",
                known_gaps=gaps,
                notes=f"This run discovered {len(discovered)} unique post URLs; union checkpoint contains {len(ordered)} URLs. No API key used.",
                public_browser=True,
                block_reason=block_reason,
            )
            return records
        except Exception as exc:
            self.coverage.register_source(
                platform, source_name, CoverageStatus.ERROR,
                record_count=len(records), data_origin="PUBLIC_PLATFORM",
                known_gaps=["Public browser collection interrupted"], notes=str(exc)[:500],
                public_browser=True,
            )
            return records
        finally:
            try:
                if context:
                    await context.close()
            except Exception:
                pass
            try:
                if browser:
                    await browser.close()
            except Exception:
                pass
            try:
                if pw:
                    await pw.stop()
            except Exception:
                pass


async def collect_default_public_profiles(coverage: Optional[CoverageTracker] = None) -> Dict[str, int]:
    tracker = coverage or CoverageTracker()
    collector = PublicBrowserCollector(coverage=tracker)
    counts: Dict[str, int] = {}

    rows = await collector.collect_profile(
        "threads", "@airpoolstylo", "https://www.threads.net/@airpoolstylo",
        max_scrolls=160, stable_cycles=8, collect_post_pages=True,
    )
    counts["threads"] = len(rows)

    rows = await collector.collect_profile(
        "instagram", "@airpoolstylo", "https://www.instagram.com/airpoolstylo/",
        max_scrolls=100, stable_cycles=7, collect_post_pages=True,
    )
    counts["instagram"] = len(rows)

    # TikTok browser is used for URL discovery. Metadata is collected faster via
    # yt-dlp/gallery-dl adapters; do not open hundreds of post pages in Playwright.
    rows = await collector.collect_profile(
        "tiktok", "@styloairpool", "https://www.tiktok.com/@styloairpool",
        max_scrolls=260, stable_cycles=20, collect_post_pages=False,
    )
    counts["tiktok_profile_snapshots"] = len(rows)
    return counts

def main() -> None:
    print(json.dumps(asyncio.run(collect_default_public_profiles()), indent=2))


if __name__ == "__main__":
    main()


