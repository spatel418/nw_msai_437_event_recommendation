"""Eventbrite scraping service — extracted from eventbrite_scrape_and_classify.ipynb."""

import json
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from bs4 import BeautifulSoup

from backend.config import (
    SCRAPER_CITY,
    SCRAPER_DAYS_AHEAD,
    SCRAPER_MAX_PAGES,
    SCRAPER_SLEEP_BETWEEN,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_meta_description(desc: str) -> str:
    """Extract useful middle part from Eventbrite meta descriptions."""
    parts = desc.split(" - ")
    if len(parts) >= 3:
        return parts[1].strip()
    elif len(parts) == 2:
        return parts[1].strip()
    return desc.strip()


def get_event_urls_from_page(
    page_num: int, city: str, date_start: str, date_end: str
) -> list[str]:
    """Scrape one search results page and return all event URLs found."""
    url = (
        f"https://www.eventbrite.com/d/{city}/all-events/"
        f"?start_date={date_start}&end_date={date_end}&page={page_num}"
    )
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"  Page {page_num}: HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if "/e/" in href and "tickets" in href:
            base = href.split("?")[0]
            if base.startswith("/"):
                base = "https://www.eventbrite.com" + base
            links.add(base)

    for script in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(script.string)
            text = json.dumps(data)
            found = re.findall(r'https://www\.eventbrite\.com/e/[^"\s]+', text)
            for f in found:
                links.add(f.split("?")[0])
        except Exception:
            pass

    return list(links)


def scrape_event_page(url: str) -> dict | None:
    """Scrape a single event page for name, description, dates, venue."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        name = ""
        start_date = ""
        end_date = ""
        venue_name = ""
        venue_city = ""
        venue_state = ""
        raw_desc = ""

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = next((d for d in data if d.get("@type") == "Event"), {})
                if data.get("@type") == "Event":
                    name = data.get("name", "")
                    raw_desc = data.get("description", "")
                    start_date = data.get("startDate", "")
                    end_date = data.get("endDate", "")
                    loc = data.get("location", {})
                    addr = loc.get("address", {})
                    venue_name = loc.get("name", "")
                    venue_city = addr.get("addressLocality", "")
                    venue_state = addr.get("addressRegion", "")
                    break
            except Exception:
                pass

        if not name:
            title_tag = soup.find("title")
            if title_tag:
                name = title_tag.text.replace("| Eventbrite", "").strip()

        if not name:
            return None

        cleaned_desc = clean_meta_description(raw_desc) if raw_desc else ""
        classifier_input = f"{name}. {cleaned_desc}".strip() if cleaned_desc else name

        return {
            "url": url,
            "name": name,
            "description": cleaned_desc,
            "classifier_input": classifier_input,
            "start_date": start_date,
            "end_date": end_date,
            "venue_name": venue_name,
            "venue_city": venue_city,
            "venue_state": venue_state,
        }
    except Exception as ex:
        print(f"  Error scraping {url}: {ex}")
    return None


def scrape_all_events(
    max_pages: int = SCRAPER_MAX_PAGES,
    days_ahead: int = SCRAPER_DAYS_AHEAD,
    sleep_between: float = SCRAPER_SLEEP_BETWEEN,
) -> pd.DataFrame:
    """Run the full scrape pipeline. Returns a DataFrame of events."""
    date_start = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_end = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).strftime(
        "%Y-%m-%d"
    )
    print(f"Scraping {SCRAPER_CITY} events from {date_start} to {date_end}")

    # Step 1: Collect URLs
    all_urls: list[str] = []
    for p in range(1, max_pages + 1):
        urls = get_event_urls_from_page(p, SCRAPER_CITY, date_start, date_end)
        all_urls.extend(urls)
        print(
            f"  Page {p}: {len(urls)} URLs (total unique: {len(set(all_urls))})"
        )
        time.sleep(sleep_between)
    all_urls = list(set(all_urls))
    print(f"Total unique URLs: {len(all_urls)}")

    # Step 2: Scrape each event page
    events: list[dict] = []
    for i, url in enumerate(all_urls):
        result = scrape_event_page(url)
        if result and result["name"]:
            events.append(result)
        if (i + 1) % 20 == 0:
            print(f"  Scraped {i + 1}/{len(all_urls)}, {len(events)} valid")
        time.sleep(sleep_between)

    df = pd.DataFrame(events).drop_duplicates(subset=["url"])
    print(f"Scraping complete: {len(df)} events")
    return df
