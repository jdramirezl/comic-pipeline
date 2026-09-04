#!/usr/bin/env python3
"""Inspect approved GetComics landing pages without downloading comic files.

Reads approved_getcomics.json and records:
- HTTP status/final URL
- page title/H1
- short collection/issue-range text snippets
- external host names present on the page (not direct file URLs)

Outputs:
  results/getcomics_inspection.json
  results/getcomics_inspection.md
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import cloudscraper
from bs4 import BeautifulSoup

MANIFEST = Path("approved_getcomics.json")
OUTDIR = Path("results")
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "desktop": True},
    delay=8,
)

KEY_RE = re.compile(
    r"\b(collects?|issues?|#\s*\d+|volume|vol\.?\s*\d+|omnibus|compendium|tpb|trade paperback|complete)\b",
    re.I,
)


def fetch(url: str):
    try:
        r = scraper.get(
            url,
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
            timeout=35,
            allow_redirects=True,
        )
        return r, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def compact(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def inspect_page(url: str) -> dict:
    r, err = fetch(url)
    if err:
        return {"url": url, "ok": False, "error": err}

    result = {
        "url": url,
        "ok": r.status_code == 200,
        "status_code": r.status_code,
        "final_url": r.url,
    }
    if r.status_code != 200:
        return result

    soup = BeautifulSoup(r.text, "html.parser")
    title = compact(soup.title.get_text(" ", strip=True)) if soup.title else ""
    h1 = soup.find("h1")
    result["page_title"] = title
    result["h1"] = compact(h1.get_text(" ", strip=True)) if h1 else ""

    # Pull a few compact snippets that are useful for verifying package contents.
    snippets = []
    seen = set()
    for tag in soup.find_all(["p", "li", "div"]):
        text = compact(tag.get_text(" ", strip=True))
        if not text or len(text) < 15 or len(text) > 500:
            continue
        if not KEY_RE.search(text):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(text)
        if len(snippets) >= 8:
            break
    result["content_snippets"] = snippets

    # Record only host names, not direct download URLs.
    hosts = Counter()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith(("http://", "https://")):
            continue
        host = urlparse(href).netloc.lower().removeprefix("www.")
        if not host or host.endswith("getcomics.org"):
            continue
        hosts[host] += 1
    result["external_hosts"] = [
        {"host": host, "count": count} for host, count in hosts.most_common(12)
    ]
    return result


def main() -> int:
    if not MANIFEST.exists():
        raise SystemExit("approved_getcomics.json not found. Run from the repo root.")

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    comics = data.get("comics", data)
    rows = []
    total_pages = sum(len(c.get("getcomics", [])) for c in comics)
    page_no = 0

    for comic in comics:
        page_rows = []
        for package in comic.get("getcomics", []):
            page_no += 1
            url = package["url"]
            print(f"[{page_no:02d}/{total_pages:02d}] {comic['title']} -> {url}")
            info = inspect_page(url)
            info["package_type"] = package.get("type")
            info["manifest_notes"] = package.get("notes")
            page_rows.append(info)
            time.sleep(0.35)
        rows.append(
            {
                "category": comic.get("category"),
                "title": comic.get("title"),
                "year": comic.get("year"),
                "issues": comic.get("issues"),
                "notes": comic.get("notes"),
                "pages": page_rows,
            }
        )

    OUTDIR.mkdir(exist_ok=True)
    payload = {"source_manifest": str(MANIFEST), "results": rows}
    (OUTDIR / "getcomics_inspection.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md = [
        "# GetComics landing-page inspection",
        "",
        "> This report checks landing pages and package metadata only. It does not download comic files.",
        "",
    ]
    for row in rows:
        md += [
            f"## {row['title']} ({row.get('year','?')}) — wanted {row.get('issues','?')}",
            "",
        ]
        if row.get("notes"):
            md.append(f"Manifest note: {row['notes']}")
            md.append("")
        for i, page in enumerate(row["pages"], 1):
            md.append(f"### Package {i}: {page.get('package_type','?')}")
            md.append(f"- URL: {page['url']}")
            md.append(f"- Reachable: {'YES' if page.get('ok') else 'NO'}")
            if page.get("status_code") is not None:
                md.append(f"- HTTP: {page['status_code']}")
            if page.get("page_title"):
                md.append(f"- Page title: {page['page_title']}")
            if page.get("h1"):
                md.append(f"- H1: {page['h1']}")
            if page.get("manifest_notes"):
                md.append(f"- Expected: {page['manifest_notes']}")
            if page.get("error"):
                md.append(f"- Error: {page['error']}")
            if page.get("content_snippets"):
                md.append("- Useful page text:")
                for s in page["content_snippets"][:6]:
                    md.append(f"  - {s}")
            if page.get("external_hosts"):
                md.append("- External hosts seen:")
                for h in page["external_hosts"]:
                    md.append(f"  - {h['host']} ({h['count']} links)")
            md.append("")

    (OUTDIR / "getcomics_inspection.md").write_text("\n".join(md), encoding="utf-8")
    print("\nDone.")
    print(r"Send me: results\getcomics_inspection.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
