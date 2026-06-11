"""
Naples FL Doctors - Social Media & Website Presence Scraper

Sources:
  - NPI Registry API (free, no key) for all practices in Naples FL
  - Direct website scraping to detect social media links
  - Basic website quality scoring

Output: naples_doctors_low_presence.csv
"""

import requests
import time
import re
import csv
import json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Naples FL zip codes
NAPLES_ZIPS = [
    "34101", "34102", "34103", "34104", "34105",
    "34108", "34109", "34110", "34112", "34113",
    "34114", "34116", "34117", "34119", "34120",
]

NPI_API = "https://npiregistry.cms.hhs.gov/api/"

SOCIAL_PATTERNS = {
    "facebook":  re.compile(r"facebook\.com/(?!sharer|share|tr\b|dialog|plugins)", re.I),
    "instagram": re.compile(r"instagram\.com/", re.I),
    "twitter":   re.compile(r"(?:twitter|x)\.com/(?!intent|share)", re.I),
    "linkedin":  re.compile(r"linkedin\.com/(?:company|in)/", re.I),
    "youtube":   re.compile(r"youtube\.com/(?:channel|user|@)", re.I),
    "tiktok":    re.compile(r"tiktok\.com/@", re.I),
    "yelp":      re.compile(r"yelp\.com/biz/", re.I),
    "google_business": re.compile(r"(?:maps\.google|google\.com/maps|g\.page)", re.I),
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── NPI helpers ──────────────────────────────────────────────────────────────

def fetch_npi_page(zip_code: str, skip: int, limit: int = 200) -> list[dict]:
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-2",   # organizations / group practices
        "postal_code": zip_code,
        "state": "FL",
        "taxonomy_description": "physician",
        "skip": skip,
        "limit": limit,
    }
    try:
        r = requests.get(NPI_API, params=params, timeout=20)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"  [NPI] Error for zip {zip_code} skip {skip}: {e}")
        return []


def fetch_npi_individuals(zip_code: str, skip: int, limit: int = 200) -> list[dict]:
    """Also pull individual physician NPIs so solo practices appear."""
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-1",
        "postal_code": zip_code,
        "state": "FL",
        "taxonomy_description": "physician",
        "skip": skip,
        "limit": limit,
    }
    try:
        r = requests.get(NPI_API, params=params, timeout=20)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"  [NPI-1] Error for zip {zip_code} skip {skip}: {e}")
        return []


def extract_practice_info(result: dict) -> dict:
    basic = result.get("basic", {})
    addresses = result.get("addresses", [])
    taxonomies = result.get("taxonomies", [])

    # Pick practice location address (address_purpose == LOCATION)
    addr = next(
        (a for a in addresses if a.get("address_purpose") == "LOCATION"),
        addresses[0] if addresses else {},
    )

    name = (
        basic.get("organization_name")
        or f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip()
    )

    # Some NPI records have a website field
    website = None
    other = result.get("other", {})
    if isinstance(other, dict):
        website = other.get("website")

    taxonomy_desc = ""
    if taxonomies:
        primary = next((t for t in taxonomies if t.get("primary")), taxonomies[0])
        taxonomy_desc = primary.get("desc", "")

    return {
        "npi": result.get("number", ""),
        "name": name,
        "taxonomy": taxonomy_desc,
        "phone": addr.get("telephone_number", ""),
        "address": f"{addr.get('address_1', '')} {addr.get('address_2', '')}".strip(),
        "city": addr.get("city", ""),
        "state": addr.get("state", ""),
        "zip": addr.get("postal_code", "")[:5],
        "website_from_npi": website or "",
    }


# ── Website / social-media checks ────────────────────────────────────────────

def fetch_page(url: str, timeout: int = 10) -> tuple[str | None, int | None]:
    """Returns (html_text, status_code) or (None, None) on failure."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout,
                         allow_redirects=True)
        return r.text, r.status_code
    except Exception:
        return None, None


def score_website(html: str, url: str) -> dict:
    """
    Heuristic quality score 0-100 and detected social channels.
    Lower score = weaker online presence (better lead for you).
    """
    soup = BeautifulSoup(html, "lxml")
    text = html.lower()

    social_found = {}
    all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    all_links += [str(soup)]  # also scan inline text / data attributes

    for platform, pattern in SOCIAL_PATTERNS.items():
        hits = [h for h in (a.get("href", "") for a in soup.find_all("a", href=True))
                if pattern.search(h)]
        if not hits:
            # Also check raw HTML (icons embedded without <a> sometimes)
            hits = pattern.findall(html)
        social_found[platform] = bool(hits)

    social_count = sum(social_found.values())

    # Simple quality signals
    has_contact_form = bool(soup.find("form"))
    has_phone = bool(re.search(r"\(?\d{3}\)?[\s\-\.]\d{3}[\s\-\.]\d{4}", text))
    has_ssl = url.startswith("https://")
    has_meta_desc = bool(soup.find("meta", {"name": re.compile("description", re.I)}))
    has_schema = "schema.org" in text or "application/ld+json" in text
    word_count = len(soup.get_text().split())
    is_thin = word_count < 300

    quality_score = 0
    quality_score += 15 if has_ssl else 0
    quality_score += 10 if has_meta_desc else 0
    quality_score += 10 if has_contact_form else 0
    quality_score += 10 if has_phone else 0
    quality_score += 10 if has_schema else 0
    quality_score += 5 if not is_thin else 0
    quality_score += social_count * 8  # up to ~40 for socials

    return {
        "social_found": social_found,
        "social_count": social_count,
        "has_ssl": has_ssl,
        "has_contact_form": has_contact_form,
        "has_phone_on_site": has_phone,
        "has_meta_desc": has_meta_desc,
        "has_schema_markup": has_schema,
        "word_count": word_count,
        "website_quality_score": min(quality_score, 100),
    }


def check_practice(info: dict) -> dict:
    """
    Try to find and evaluate the practice website.
    Returns enriched info dict.
    """
    website = info.get("website_from_npi", "").strip()

    # Guess a website if none listed
    guessed = False
    if not website:
        # Try common patterns
        slug = re.sub(r"[^a-z0-9]", "", info["name"].lower())
        candidates = [
            f"https://www.{slug}.com",
            f"https://{slug}.com",
        ]
    else:
        if not website.startswith("http"):
            website = "https://" + website
        candidates = [website]

    found_url = None
    html = None
    status = None

    for url in candidates:
        h, s = fetch_page(url)
        if s and 200 <= s < 400:
            found_url = url
            html = h
            status = s
            break
        time.sleep(0.3)

    if html:
        scores = score_website(html, found_url)
    else:
        scores = {
            "social_found": {p: False for p in SOCIAL_PATTERNS},
            "social_count": 0,
            "has_ssl": False,
            "has_contact_form": False,
            "has_phone_on_site": False,
            "has_meta_desc": False,
            "has_schema_markup": False,
            "word_count": 0,
            "website_quality_score": 0,
        }

    result = {
        **info,
        "website_detected": found_url or "",
        "website_live": found_url is not None,
        **scores,
    }

    # Flatten social_found into columns
    for platform, detected in result.pop("social_found").items():
        result[f"has_{platform}"] = detected

    # Overall presence score (lower = bigger opportunity)
    presence = result["website_quality_score"]
    result["total_presence_score"] = presence
    result["opportunity_tier"] = (
        "HIGH"   if presence < 20 else
        "MEDIUM" if presence < 45 else
        "LOW"
    )

    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def collect_npi_records() -> list[dict]:
    seen_npis: set[str] = set()
    records: list[dict] = []

    for zip_code in NAPLES_ZIPS:
        print(f"\nFetching NPI data for zip {zip_code}...")
        for fetcher in (fetch_npi_page, fetch_npi_individuals):
            skip = 0
            while True:
                batch = fetcher(zip_code, skip)
                if not batch:
                    break
                for r in batch:
                    npi = r.get("number", "")
                    if npi and npi not in seen_npis:
                        seen_npis.add(npi)
                        records.append(extract_practice_info(r))
                if len(batch) < 200:
                    break
                skip += 200
                time.sleep(0.5)
        time.sleep(0.3)

    print(f"\nTotal unique practices/providers found: {len(records)}")
    return records


def main():
    print("=" * 60)
    print("Naples FL Doctor Offices — Online Presence Scraper")
    print("=" * 60)

    records = collect_npi_records()

    if not records:
        print("No records found. Check network access.")
        return

    print("\nChecking websites and social media presence...")
    enriched = []
    for i, info in enumerate(records, 1):
        print(f"  [{i}/{len(records)}] {info['name'][:50]}", end="  ", flush=True)
        result = check_practice(info)
        tier = result["opportunity_tier"]
        score = result["total_presence_score"]
        print(f"score={score} tier={tier}")
        enriched.append(result)
        time.sleep(0.4)   # polite crawl delay

    # Sort: highest opportunity first (lowest score)
    enriched.sort(key=lambda x: (x["opportunity_tier"] != "HIGH",
                                  x["opportunity_tier"] != "MEDIUM",
                                  x["total_presence_score"]))

    # Write full CSV
    output_file = "naples_doctors_presence.csv"
    if enriched:
        fieldnames = list(enriched[0].keys())
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched)
        print(f"\nFull results saved to: {output_file}")

    # Write HIGH+MEDIUM opportunity CSV
    leads_file = "naples_doctors_leads.csv"
    leads = [r for r in enriched if r["opportunity_tier"] in ("HIGH", "MEDIUM")]
    if leads:
        fieldnames = list(leads[0].keys())
        with open(leads_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)
        print(f"Leads (HIGH+MEDIUM opportunity) saved to: {leads_file}")

    # Summary
    high  = sum(1 for r in enriched if r["opportunity_tier"] == "HIGH")
    med   = sum(1 for r in enriched if r["opportunity_tier"] == "MEDIUM")
    low   = sum(1 for r in enriched if r["opportunity_tier"] == "LOW")
    no_web = sum(1 for r in enriched if not r["website_live"])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total providers found:      {len(enriched)}")
    print(f"  No detectable website:      {no_web}")
    print(f"  HIGH opportunity (score<20): {high}")
    print(f"  MEDIUM opportunity (20-44):  {med}")
    print(f"  LOW opportunity (45+):       {low}")
    print("=" * 60)
    print("\nOpportunity tiers:")
    print("  HIGH   = no/minimal web presence, 0-1 social channels")
    print("  MEDIUM = basic site or 1-2 social channels, room to grow")
    print("  LOW    = solid presence, not a priority lead")


if __name__ == "__main__":
    main()
