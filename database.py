import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.models import Article
import logging

logger = logging.getLogger("app.database")

class DatabaseManager:
    def __init__(self, db_path="news_articles.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    article_id TEXT PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT,
                    published TIMESTAMP NOT NULL,
                    source TEXT NOT NULL,
                    author TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    source TEXT PRIMARY KEY,
                    last_sync TIMESTAMP NOT NULL,
                    last_article_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
            logger.info("Database initialized.")

    def insert_article(self, article: Article) -> str:
        """
        Inserts a new article ONLY if it does not exist.
        Returns 'inserted', 'skipped', or 'failed'
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT 1 FROM articles WHERE article_id=?", (article.article_id,))
                exists = c.fetchone()
                if exists:
                    # Do not update or re-insert
                    return 'skipped'
                else:
                    # Insert
                    c.execute("""
                        INSERT INTO articles (article_id, url, title, summary, published, source, author, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article.article_id,
                        str(article.url),
                        article.title,
                        article.summary,
                        article.published.isoformat(),
                        article.source,
                        article.author,
                        article.created_at.isoformat() if article.created_at else datetime.now(timezone.utc).isoformat(),
                        article.updated_at.isoformat() if article.updated_at else datetime.now(timezone.utc).isoformat(),
                    ))
                    conn.commit()
                    return 'inserted'
        except Exception as e:
            logger.error(f"Failed to insert article {article.article_id}: {e}")
            return 'failed'

    def get_last_sync_time(self, source: str) -> Optional[datetime]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT last_sync FROM sync_metadata WHERE source=?", (source,))
            result = c.fetchone()
            if result and result[0]:
                dt = datetime.fromisoformat(result[0])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            return None

    def update_sync_metadata(self, source: str, article_count: int):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO sync_metadata (source, last_sync, last_article_count)
                VALUES (?, ?, ?)
            """, (source, now, article_count))
            conn.commit()

    def get_latest_articles(self, limit=5) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT title, url, published, source FROM articles
                ORDER BY published DESC
                LIMIT ?
            """, (limit,))
            rows = c.fetchall()
            return [
                {"title": r[0], "url": r[1], "published": r[2], "source": r[3]}
                for r in rows
            ]
