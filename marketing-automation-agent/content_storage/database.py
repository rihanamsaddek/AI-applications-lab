"""SQLite storage for fetched content and post history."""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from content_fetchers.base_fetcher import ContentItem

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    influencer_name TEXT NOT NULL,
    platform TEXT NOT NULL,
    content_text TEXT,
    content_url TEXT UNIQUE,
    title TEXT,
    engagement_score REAL DEFAULT 0.0,
    fetched_at TEXT NOT NULL,
    published_at TEXT,
    used_in_post INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS post_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_title TEXT,
    post_text TEXT,
    image_path TEXT,
    linkedin_post_id TEXT,
    posted_at TEXT NOT NULL,
    source_content_urls TEXT
);

CREATE INDEX IF NOT EXISTS idx_content_url ON content(content_url);
CREATE INDEX IF NOT EXISTS idx_content_fetched ON content(fetched_at);
CREATE INDEX IF NOT EXISTS idx_post_history_posted ON post_history(posted_at);
"""


class Database:
    """SQLite wrapper for content and post history storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def save_content_batch(self, items: List[ContentItem]) -> int:
        """Insert new content items, skipping duplicates by URL. Returns count inserted."""
        saved = 0
        with self._connect() as conn:
            for item in items:
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO content
                            (influencer_name, platform, content_text, content_url,
                             title, engagement_score, fetched_at, published_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.influencer_name,
                            item.platform,
                            item.content_text,
                            item.content_url,
                            item.title,
                            item.engagement_score,
                            item.fetched_at.isoformat(),
                            item.published_at.isoformat() if item.published_at else None,
                        ),
                    )
                    if conn.execute("SELECT changes()").fetchone()[0]:
                        saved += 1
                except sqlite3.Error as e:
                    logger.warning(f"Failed to save content item: {e}")
        logger.info(f"Saved {saved}/{len(items)} new content items to DB")
        return saved

    def get_recent_content(self, hours: int = 48) -> List[Dict[str, Any]]:
        """Return content items fetched within the last N hours."""
        cutoff = datetime.utcnow().isoformat()[:19]  # Truncate to seconds
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM content
                WHERE fetched_at > datetime('now', ?)
                ORDER BY engagement_score DESC
                """,
                (f"-{hours} hours",),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_post_topics(self, days: int = 30) -> List[str]:
        """Return topic titles from posts in the last N days."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT topic_title FROM post_history
                WHERE posted_at > datetime('now', ?)
                AND topic_title IS NOT NULL
                """,
                (f"-{days} days",),
            ).fetchall()
        return [row["topic_title"] for row in rows]

    def save_post(
        self,
        topic_title: str,
        post_text: str,
        image_path: Optional[str],
        linkedin_post_id: Optional[str],
        source_urls: List[str],
    ):
        """Record a generated/published post."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO post_history
                    (topic_title, post_text, image_path, linkedin_post_id, posted_at, source_content_urls)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_title,
                    post_text,
                    image_path,
                    linkedin_post_id,
                    datetime.utcnow().isoformat(),
                    json.dumps(source_urls),
                ),
            )
        logger.info(f"Recorded post to history: '{topic_title}'")
