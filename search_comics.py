#!/usr/bin/env python3
"""
Stage 2: search ReadComicOnline for candidates from wanted.json.

- Does NOT download comic pages/issues.
- Uses ReadComicOnline's own search endpoint.
- Uses cloudscraper because the site may reject basic urllib requests.
- If live verification fails, still emits URL guesses for ChatGPT review.

Run:
    python search_comics.py

Output:
    results/search_results.md
    results/search_results.json
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote_plus, urljoin

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies.")
    print("Run:")
    print("  python -m pip install requests beautifulsoup4 cloudscraper")
    raise SystemExit(2)

SITE = "https://readcomiconline.li"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
WS_RE = re.compile(r"\s+")
ISSUE_TEXT_RE = re.compile(r"^\s*Issue\s*#?\s*([0-9]+(?:\.[0-9]+)?)\s*$", re.I)


def asciify(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")


def normalize(s: str) -> str:
    s = asciify(s).lower().replace("&", " and ")
    s = re.sub(r"\((?:19\d{2}|20\d{2}).*?\)", " ", s)
    s = re.sub(r"\b(?:vol(?:ume)?|v)\.?\s*\d+\b", " ", s, flags=re.I)
    s = NON_ALNUM_RE.sub(" ", s)
    return WS_RE.sub(" ", s).strip()


def tokens(s: str) -> set[str]:
    stop = {"the", "a", "an", "and", "of", "vol", "volume", "comic", "comics"}
    return {x for x in normalize(s).split() if x not in stop}


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / len(ta | tb) if ta and tb else 0.0
    exact = 1.0 if na == nb else 0.0
    return 0.55 * seq + 0.30 * jac + 0.15 * exact


def as_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def creator_match(wanted, got) -> bool:
    wanted = [normalize(x) for x in as_list(wanted)]
    got = [normalize(x) for x in as_list(got)]
    for a in wanted:
        for b in got:
            if a == b:
                return True
            if a.split() and b.split() and a.split()[-1] == b.split()[-1]:
                return True
    return False


def slugify(s: str) -> str:
    s = asciify(s)
    s = re.sub(r"[’'\"“”]", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")
    return s


def direct_guesses(title: str, year: int | None) -> list[str]:
    variants = [title]
    if title.lower().startswith("the "):
        variants.append(title[4:])
    out, seen = [], set()
    for v in variants:
        slug = slugify(v)
        for candidate in ([slug, f"{slug}-{year}"] if year else [slug]):
            u = f"{SITE}/Comic/{candidate}"
            if u.lower() not in seen:
                seen.add(u.lower())
                out.append(u)
    return out


def make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True},
        delay=10,
    )


SCRAPER = make_scraper()
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get(url: str, timeout=30):
    r = SCRAPER.get(url, headers=HEADERS, timeout=timeout)
    return r.status_code, r.url, r.text


def rco_search(query: str) -> tuple[list[str], str | None]:
    url = f"{SITE}/Search/Comic?keyword={quote_plus(query)}"
    try:
        status, final, body = get(url)
        if status != 200:
            return [], f"search HTTP {status}"
        soup = BeautifulSoup(body, "html.parser")
        urls = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/Comic/" not in href:
                continue
            full = urljoin(SITE, href).split("#", 1)[0]
            key = full.lower()
            if key not in seen:
                seen.add(key)
                urls.append(full)
        if not urls:
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            return [], f"search returned no comic links; page title={title!r}"
        return urls, None
    except Exception as e:
        return [], f"search exception: {type(e).__name__}: {e}"


def field_from_text(text: str, label: str) -> str | None:
    m = re.search(rf"{re.escape(label)}\s*:\s*([^\n\r]+)", text, flags=re.I)
    if m:
        return m.group(1).strip()
    return None


def parse_candidate(url: str) -> tuple[dict | None, str | None]:
    try:
        status, final, body = get(url)
        if status != 200:
            return None, f"HTTP {status}"
        soup = BeautifulSoup(body, "html.parser")
        text = soup.get_text("\n", strip=True)

        page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        name = re.split(r"\s+comic\s*\|", page_title, flags=re.I)[0].strip()
        if not name:
            for tag in ("h1", "h2", "h3"):
                node = soup.find(tag)
                if node:
                    name = node.get_text(" ", strip=True)
                    break

        if not name or "just a moment" in page_title.lower():
            return None, f"blocked/challenge page title={page_title!r}"

        writer = field_from_text(text, "Writer")
        artist = field_from_text(text, "Artist")
        pubdate = field_from_text(text, "Publication date")
        publisher = field_from_text(text, "Publisher")
        status_text = field_from_text(text, "Status")

        issues = []
        for a in soup.find_all("a"):
            label = a.get_text(" ", strip=True)
            m = ISSUE_TEXT_RE.match(label)
            if m:
                issues.append(float(m.group(1)))
        issues = sorted(set(issues))

        return {
            "name": name,
            "url": final,
            "publication_date": pubdate,
            "writers": as_list(writer),
            "artists": as_list(artist),
            "publisher": as_list(publisher),
            "status": status_text,
            "issue_count": len(issues) if issues else None,
            "max_issue": max(issues) if issues else None,
            "verified_live": True,
        }, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def score(target: dict, cand: dict) -> tuple[float, list[str]]:
    aliases = [target["title"]] + as_list(target.get("aliases"))
    ts = max(title_similarity(x, cand.get("name", "")) for x in aliases)
    s = ts * 0.74
    why = [f"title={ts:.2f}"]

    year = target.get("year")
    if year:
        years = {int(x) for x in YEAR_RE.findall(
            f"{cand.get('publication_date', '')} {cand.get('name', '')}"
        )}
        if int(year) in years:
            s += 0.13
            why.append("year=exact")
        elif years:
            d = min(abs(int(year) - y) for y in years)
            if d <= 1:
                s += 0.04
                why.append("year=near")
            elif d >= 3:
                s -= 0.08
                why.append(f"year=mismatch({sorted(years)})")

    if creator_match(target.get("writers"), cand.get("writers")):
        s += 0.11
        why.append("writer=match")

    wanted_nums = [int(x) for x in re.findall(r"\b\d+\b", str(target.get("issues", "")))]
    if wanted_nums and cand.get("max_issue") is not None:
        wanted_max = max(wanted_nums)
        if float(cand["max_issue"]) >= wanted_max:
            s += 0.02
            why.append("coverage=possible")
        else:
            s -= 0.06
            why.append("coverage=short")

    return max(0.0, min(1.0, s)), why


def conf(v: float) -> str:
    if v >= .88:
        return "HIGH"
    if v >= .72:
        return "MEDIUM"
    return "LOW"


def load_manifest():
    p = Path("wanted.json")
    if not p.exists():
        raise SystemExit("wanted.json must be in the same folder as this script.")
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["comics"] if isinstance(d, dict) else d


def report(rows):
    lines = [
        "# Comic search review v3",
        "",
        "> Discovery only. No comic issues/pages were downloaded.",
        "> Verified-live rows were fetched from ReadComicOnline. URL guesses are retained when the site blocks automation.",
        "",
    ]
    cat = None
    for row in rows:
        t = row["target"]
        if t.get("category") != cat:
            cat = t.get("category")
            lines += [f"## {cat}", ""]
        lines += [
            f"### {t['title']} ({t.get('year', '?')}) — wanted {t.get('issues', '?')}",
            f"Wanted writer(s): {', '.join(as_list(t.get('writers')))}",
            "",
        ]
        cs = row.get("candidates", [])
        if cs:
            lines += [
                "| # | Score | Status | Candidate | Date | Writers | Issues | URL |",
                "|---:|---:|---|---|---|---|---:|---|",
            ]
            for i, c in enumerate(cs, 1):
                candidate_name = str(c.get("name", "")).replace("|", "\\|")
                lines.append(
                    f"| {i} | {c.get('score', 0):.3f} {c.get('confidence', '')} | "
                    f"{'VERIFIED' if c.get('verified_live') else 'GUESS'} | "
                    f"{candidate_name} | "
                    f"{c.get('publication_date') or ''} | "
                    f"{', '.join(as_list(c.get('writers')))} | "
                    f"{c.get('issue_count') or ''} | {c.get('url', '')} |"
                )
        else:
            lines.append("**No live candidate parsed. URL guesses below are for ChatGPT verification.**")
        lines.append("")
        if row.get("search_warnings"):
            lines.append("Search diagnostics:")
            for w in row["search_warnings"][:4]:
                lines.append(f"- {w}")
            lines.append("")
        if row.get("guesses"):
            lines.append("URL guesses:")
            for u in row["guesses"][:8]:
                lines.append(f"- {u}")
            lines.append("")
    return "\n".join(lines)


def main():
    targets = load_manifest()
    out = Path("results")
    out.mkdir(exist_ok=True)

    rows = []
    for idx, t in enumerate(targets, 1):
        print(f"[{idx:02d}/{len(targets):02d}] {t.get('category')}: {t['title']}")
        aliases = [t["title"]] + as_list(t.get("aliases"))
        urls, seen = [], set()
        warnings = []

        for q in aliases[:3]:
            found, warn = rco_search(q)
            if warn:
                warnings.append(f"{q}: {warn}")
            for u in found:
                if u.lower() not in seen:
                    seen.add(u.lower())
                    urls.append(u)
            time.sleep(.25)

        guesses = []
        for q in aliases:
            for u in direct_guesses(q, int(t["year"]) if t.get("year") else None):
                if u.lower() not in {x.lower() for x in guesses}:
                    guesses.append(u)
                if u.lower() not in seen:
                    seen.add(u.lower())
                    urls.append(u)

        candidates = []
        parse_errors = []
        for u in urls[:25]:
            c, err = parse_candidate(u)
            if c:
                best = max(title_similarity(a, c["name"]) for a in aliases)
                if best >= .36:
                    sc, why = score(t, c)
                    c["score"] = round(sc, 4)
                    c["confidence"] = conf(sc)
                    c["reasons"] = why
                    candidates.append(c)
            elif err:
                parse_errors.append(f"{u}: {err}")
            time.sleep(.25)

        dedup = {}
        for c in candidates:
            k = c["url"].lower()
            if k not in dedup or c["score"] > dedup[k]["score"]:
                dedup[k] = c
        ranked = sorted(dedup.values(), key=lambda x: x["score"], reverse=True)[:5]

        warnings.extend(parse_errors[:5])
        rows.append({
            "target": t,
            "candidates": ranked,
            "search_warnings": warnings,
            "guesses": guesses,
        })

    payload = {"source": SITE, "results": rows}
    (out / "search_results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "search_results.md").write_text(report(rows), encoding="utf-8")
    print("\nDone. Nothing was downloaded.")
    print("Send me: results\\search_results.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
