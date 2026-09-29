from src.collectors.browser_public_adapter import PublicBrowserCollector, _canonical_url
from src.collectors.tiktok_ytdlp_adapter import TikTokYtDlpAdapter


def test_threads_urls_are_canonicalized_without_query_tokens():
    url = "https://www.threads.net/@airpoolstylo/post/ABC123/?x=secretish#frag"
    clean = _canonical_url(url)
    assert clean == "https://www.threads.com/@airpoolstylo/post/ABC123"
    assert "secretish" not in clean


def test_post_link_extraction_is_platform_scoped_and_deduped():
    links = [
        "https://www.threads.net/@airpoolstylo/post/AAA?x=1",
        "https://www.threads.com/@airpoolstylo/post/AAA",
        "https://www.threads.com/@someoneelse/post/BBB",
    ]
    out = PublicBrowserCollector._extract_post_links("threads", links, "@airpoolstylo")
    assert out == ["https://www.threads.com/@airpoolstylo/post/AAA"]


def test_tiktok_ytdlp_payload_drops_volatile_download_urls_and_headers():
    raw = {
        "id": "123",
        "title": "real caption",
        "description": "real caption",
        "timestamp": 100,
        "view_count": 42,
        "url": "https://signed.cdn.example/video?token=secretish",
        "http_headers": {"Cookie": "do-not-store"},
        "formats": [{"url": "https://signed.example"}],
    }
    stable = TikTokYtDlpAdapter._stable_metadata(raw)
    assert stable["id"] == "123"
    assert stable["view_count"] == 42
    assert "url" not in stable
    assert "http_headers" not in stable
    assert "formats" not in stable
    assert stable["authoritative"] is True
    assert stable["provenance_verified"] is True
