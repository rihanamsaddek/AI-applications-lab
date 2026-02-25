"""RSS/Atom feed fetcher — no API key required, no external library dependency."""

import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

import requests

from .base_fetcher import BaseFetcher, ContentItem

logger = logging.getLogger(__name__)

FETCH_WINDOW_HOURS = 48
REQUEST_TIMEOUT = 15

# RSS and Atom namespaces
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class RSSFetcher(BaseFetcher):
    """Fetches content from RSS/Atom feeds using stdlib xml + requests (no feedparser needed)."""

    def is_available(self) -> bool:
        return True  # No credentials required

    def fetch_for_influencer(
        self,
        influencer_name: str,
        feed_url: Optional[str] = None,
        **kwargs,
    ) -> List[ContentItem]:
        if not feed_url:
            return []

        logger.info(f"[RSS] Fetching {influencer_name}: {feed_url}")
        try:
            resp = requests.get(
                feed_url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "MarketingAutomationAgent/1.0 (RSS reader)"},
            )
            resp.raise_for_status()
            xml_text = resp.text
        except Exception as e:
            logger.error(f"[RSS] HTTP error for {feed_url}: {e}")
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"[RSS] XML parse error for {feed_url}: {e}")
            return []

        # Detect RSS vs Atom
        tag = root.tag.lower()
        if "feed" in tag:
            return self._parse_atom(root, influencer_name)
        else:
            return self._parse_rss(root, influencer_name)

    # ------------------------------------------------------------------ #
    # RSS 2.0 parsing
    # ------------------------------------------------------------------ #

    def _parse_rss(self, root: ET.Element, influencer_name: str) -> List[ContentItem]:
        items = []
        cutoff_ts = time.time() - FETCH_WINDOW_HOURS * 3600

        # Handle <rss><channel><item> or <rdf:RDF><item>
        all_items = root.findall(".//item")

        for item in all_items:
            try:
                title = self._text(item, "title")
                link = self._text(item, "link")
                description = self._text(item, "description") or ""
                content = (
                    item.findtext(f"{{{NS['content']}}}encoded") or ""
                )
                pub_date_str = self._text(item, "pubDate") or self._text(item, "pubdate")
                dc_date = item.findtext(f"{{{NS['dc']}}}date")

                text = self._strip_html(content or description)[:2000]
                pub_dt = self._parse_date_str(pub_date_str or dc_date)

                if pub_dt and pub_dt.timestamp() < cutoff_ts:
                    continue

                if not (title or text):
                    continue

                items.append(ContentItem(
                    influencer_name=influencer_name,
                    platform="rss",
                    content_text=text or title or "",
                    content_url=link or "",
                    title=title or "",
                    engagement_score=0.0,
                    published_at=pub_dt,
                ))
            except Exception as e:
                logger.debug(f"[RSS] Skipping item: {e}")

        logger.info(f"[RSS] Fetched {len(items)} items for {influencer_name}")
        return items

    # ------------------------------------------------------------------ #
    # Atom parsing
    # ------------------------------------------------------------------ #

    def _parse_atom(self, root: ET.Element, influencer_name: str) -> List[ContentItem]:
        items = []
        cutoff_ts = time.time() - FETCH_WINDOW_HOURS * 3600

        atom_ns = "{http://www.w3.org/2005/Atom}"
        # findall returns a list; "or" on lists is fine (empty list = falsy)
        entries = root.findall(f"{atom_ns}entry")
        if not entries:
            entries = root.findall("entry")

        for entry in entries:
            try:
                # NOTE: ElementTree elements with only text (no child elements) evaluate
                # as falsy in Python, so we must use explicit "is not None" checks, NOT "or".
                title_el = entry.find(f"{atom_ns}title")
                if title_el is None:
                    title_el = entry.find("title")
                title = (title_el.text or "").strip() if title_el is not None else ""

                # Get link href
                link = ""
                link_el = entry.find(f"{atom_ns}link")
                if link_el is None:
                    link_el = entry.find("link")
                if link_el is not None:
                    link = link_el.get("href", "") or (link_el.text or "")

                # Get content — prefer full content over summary
                content_el = entry.find(f"{atom_ns}content")
                if content_el is None:
                    content_el = entry.find("content")
                if content_el is None:
                    content_el = entry.find(f"{atom_ns}summary")
                if content_el is None:
                    content_el = entry.find("summary")
                raw_text = (content_el.text or "") if content_el is not None else ""
                text = self._strip_html(raw_text)[:2000]

                # Get date
                updated_el = entry.find(f"{atom_ns}updated")
                if updated_el is None:
                    updated_el = entry.find("updated")
                pub_el = entry.find(f"{atom_ns}published")
                if pub_el is None:
                    pub_el = entry.find("published")

                date_str = None
                if updated_el is not None and updated_el.text:
                    date_str = updated_el.text
                elif pub_el is not None and pub_el.text:
                    date_str = pub_el.text

                pub_dt = self._parse_iso_date(date_str)

                if pub_dt and pub_dt.timestamp() < cutoff_ts:
                    continue

                if not (title or text):
                    continue

                items.append(ContentItem(
                    influencer_name=influencer_name,
                    platform="rss",
                    content_text=text or title or "",
                    content_url=link,
                    title=title,
                    engagement_score=0.0,
                    published_at=pub_dt,
                ))
            except Exception as e:
                logger.debug(f"[Atom] Skipping entry: {e}")

        logger.info(f"[RSS/Atom] Fetched {len(items)} items for {influencer_name}")
        return items

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _text(el: ET.Element, tag: str) -> Optional[str]:
        found = el.find(tag)
        if found is not None and found.text:
            return found.text.strip()
        return None

    @staticmethod
    def _strip_html(html: str) -> str:
        """Remove HTML tags and collapse whitespace."""
        text = re.sub(r"<[^>]+>", " ", html)
        return " ".join(text.split())

    @staticmethod
    def _parse_date_str(raw: Optional[str]) -> Optional[datetime]:
        """Parse RFC 2822 date string (e.g. from RSS pubDate)."""
        if not raw:
            return None
        try:
            dt = parsedate_to_datetime(raw.strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    @staticmethod
    def _parse_iso_date(raw: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 date string (e.g. from Atom updated/published)."""
        if not raw:
            return None
        try:
            raw = raw.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(raw)
        except Exception:
            return None
