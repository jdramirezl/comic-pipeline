#!/usr/bin/env python3
"""
Resolve candidate download-host links from the already-approved GetComics landing pages.

IMPORTANT:
- This script DOES NOT download comic files.
- It never searches for alternate comics.
- It only inspects URLs already present in approved_getcomics.json.
- It writes a review report for the next approval step.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin

import cloudscraper
from bs4 import BeautifulSoup

KNOWN_HOSTS = {
    "pixeldrain.com": 100,
    "pixeldrain.net": 100,
    "mega.nz": 95,
    "mediafire.com": 90,
    "www.mediafire.com": 90,
    "comicfiles.ru": 88,
    "rootz.so": 80,
    "www.rootz.so": 80,
    "vikingfile.com": 78,
    "www.vikingfile.com": 78,
    "fileq.net": 75,
    "terabox.com": 60,
    "1024terabox.com": 60,
    "terabox.link": 60,
    "cloud.mail.ru": 55,
    "userscloud.com": 45,
    "getcomics.ufile.io": 40,
    "ufile.io": 40,
    "yadi.sk": 40,
    "dropapk.to": 35,
    "wetransfer.com": 35,
}

IGNORE_DOMAINS = {
    "discord.com", "imgur.com", "twitter.com", "facebook.com",
    "yacreader.com", "comicrack.cyolito.com", "cdisplayex.com",
    "7-zip.org", "craveu.ai", "juicychat.ai", "funnyswapai.xyz",
    "readcomicsonline.ru",
}

DOWNLOAD_WORDS = (
    "download", "main server", "pixeldrain", "mega", "mediafire",
    "viking", "rootz", "terabox", "fileq", "ufile", "userscloud",
    "yandisk", "yan disk", "cloudmail", "wetransfer", "mirror",
)

REVIEW_TARGET = ("Nightwing", 2016, "78-118")


def make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True},
        delay=10,
    )


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def host_score(url: str, label: str) -> int:
    d = domain(url)
    score = KNOWN_HOSTS.get(d, 0)
    l = label.lower()
    if "main server" in l or label.strip().lower() == "download now":
        score = max(score, 92)
    if "pixeldrain" in l:
        score = max(score, 100)
    elif "mega" in l:
        score = max(score, 95)
    elif "mediafire" in l:
        score = max(score, 90)
    elif "viking" in l:
        score = max(score, 78)
    elif "rootz" in l:
        score = max(score, 80)
    return score


def likely_download_link(href: str, label: str) -> bool:
    d = domain(href)
    if not href.startswith(("http://", "https://")):
        return False
    if d in IGNORE_DOMAINS:
        return False
    text = f"{label} {href}".lower()
    if any(w in text for w in DOWNLOAD_WORDS):
        return True
    if d in KNOWN_HOSTS:
        return True
    if d.endswith("getcomics.info") and any(w in label.lower() for w in ("download", "main", "mirror")):
        return True
    return False


def fetch(scraper, url: str, max_attempts: int = 4):
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
    }
    last = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = scraper.get(url, headers=headers, timeout=35, allow_redirects=True)
            last = r
            if r.status_code == 200:
                return r, None
            if r.status_code == 429:
                retry = r.headers.get("Retry-After")
                wait = float(retry) if retry and retry.isdigit() else (4 * attempt)
                print(f"    HTTP 429, waiting {wait:.0f}s...")
                time.sleep(wait)
                continue
            return r, f"HTTP {r.status_code}"
        except Exception as exc:
            if attempt == max_attempts:
                return last, f"{type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
    return last, "fetch failed"


def extract_links(page_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for a in soup.find_all("a", href=True):
        label = " ".join(a.get_text(" ", strip=True).split())
        href = urljoin(page_url, a["href"].strip())
        if not likely_download_link(href, label):
            continue
        key = (href, label.lower())
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "label": label or "(no label)",
            "url": href,
            "domain": domain(href),
            "preference_score": host_score(href, label),
        })
    results.sort(key=lambda x: (-x["preference_score"], x["domain"], x["label"].lower()))
    return results


def report_md(payload):
    lines = [
        "# Download-link candidate review",
        "",
        "> No comic files were downloaded. This report only resolves candidate host links from approved landing pages.",
        "",
        f"- Targets: {payload['summary']['targets']}",
        f"- Landing-page packages: {payload['summary']['packages']}",
        f"- Pages fetched: {payload['summary']['fetched']}",
        f"- Pages failed: {payload['summary']['failed']}",
        f"- Candidate links found: {payload['summary']['candidate_links']}",
        "",
    ]
    for item in payload["results"]:
        t = item["target"]
        lines += [f"## {t['title']} ({t.get('year','?')}) — wanted {t.get('issues','?')}", ""]
        if item.get("status") == "REVIEW_COVERAGE":
            lines += [
                "**STATUS: REVIEW_COVERAGE** — current TPB set is not exact contiguous coverage; do not download automatically.",
                "",
            ]
        for p in item["packages"]:
            lines += [
                f"### {p['type']}",
                f"- Landing page: {p['url']}",
                f"- Fetch: {p['fetch_status']}",
            ]
            if p.get("error"):
                lines.append(f"- Error: {p['error']}")
            if p.get("candidates"):
                lines.append("- Candidate host links:")
                for c in p["candidates"]:
                    lines.append(
                        f"  - score {c['preference_score']:>3} | {c['label']} | {c['domain']} | {c['url']}"
                    )
            else:
                lines.append("- Candidate host links: none parsed")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="approved_getcomics.json")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--delay", type=float, default=1.25,
                    help="Base delay between landing pages; keep >=1 to avoid hammering the site.")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    comics = manifest["comics"]
    scraper = make_scraper()

    output = []
    total_packages = fetched = failed = links = 0

    for idx, comic in enumerate(comics, 1):
        print(f"[{idx:02d}/{len(comics):02d}] {comic['title']} ({comic.get('year')})")
        item = {
            "target": {
                "category": comic.get("category"),
                "title": comic["title"],
                "year": comic.get("year"),
                "issues": comic.get("issues"),
            },
            "status": "READY",
            "packages": [],
        }

        if (comic.get("title"), comic.get("year"), comic.get("issues")) == REVIEW_TARGET:
            item["status"] = "REVIEW_COVERAGE"

        for pkg in comic.get("getcomics", []):
            total_packages += 1
            p = {
                "url": pkg["url"],
                "type": pkg.get("type", "unknown"),
                "notes": pkg.get("notes"),
                "candidates": [],
            }
            if item["status"] == "REVIEW_COVERAGE":
                p["fetch_status"] = "SKIPPED"
                p["error"] = "Coverage review required before host resolution."
                item["packages"].append(p)
                continue

            r, err = fetch(scraper, pkg["url"])
            if r is not None and r.status_code == 200:
                fetched += 1
                p["fetch_status"] = "HTTP 200"
                p["candidates"] = extract_links(r.url, r.text)
                links += len(p["candidates"])
            else:
                failed += 1
                p["fetch_status"] = f"HTTP {r.status_code}" if r is not None else "FAILED"
                p["error"] = err or "unknown error"
            item["packages"].append(p)
            time.sleep(max(1.0, args.delay) + random.uniform(0, 0.35))

        output.append(item)

    payload = {
        "version": 1,
        "source_manifest": args.manifest,
        "summary": {
            "targets": len(comics),
            "packages": total_packages,
            "fetched": fetched,
            "failed": failed,
            "candidate_links": links,
        },
        "results": output,
    }

    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)
    (out / "download_link_candidates.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "download_link_candidates.md").write_text(
        report_md(payload), encoding="utf-8"
    )

    print("\nDone. No comic files were downloaded.")
    print(r"Send me: results\download_link_candidates.md")


if __name__ == "__main__":
    main()
