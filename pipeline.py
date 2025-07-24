import time
import logging
from app.database import DatabaseManager
from app.extractors import NewsExtractor

logger = logging.getLogger("app.pipeline")

class NewsPipeline:
    def __init__(self, db_path="news_articles.db"):
        self.db = DatabaseManager(db_path)
        self.extractor = NewsExtractor()

    def run_pipeline(self, incremental=True):
        start = time.time()

        stats = {
            "sources_processed": 0,
            "total_articles_extracted": 0,
            "new_articles": 0,
            "execution_time": 0.0,
            "skift_fetched": 0,
            "phocuswire_fetched": 0
        }

        source_map = {
            "skift": self.extractor.fetch_skift_articles,
            "phocuswire": self.extractor.fetch_phocuswire_articles,
        }

        all_ids = set()

        for source, fetcher in source_map.items():
            articles = fetcher()
            num_articles = len(articles)

            # Track per-source fetch count
            stats[f"{source}_fetched"] = num_articles
            stats["sources_processed"] += 1
            stats["total_articles_extracted"] += num_articles

            new_count = 0

            for a in articles:
                if a.article_id in all_ids:
                    logger.warning(
                        f"DUPLICATE ARTICLE_ID detected: {a.article_id} | Source: {a.source} | Title: {a.title} | URL: {a.url}"
                    )
                    continue
                all_ids.add(a.article_id)

                if incremental:
                    last_sync = self.db.get_last_sync_time(source)
                    if last_sync and a.published <= last_sync:
                        continue

                result = self.db.insert_article(a)
                if result == 'inserted':
                    new_count += 1

            self.db.update_sync_metadata(source, new_count)
            stats["new_articles"] += new_count

        stats["execution_time"] = round(time.time() - start, 2)
        return stats

    def display_latest_articles(self, limit=5):
        articles = self.db.get_latest_articles(limit)
        for a in articles:
            print(f"{a['published']} | {a['source'].upper()} | {a['title']}\n{a['url']}\n{'-'*80}")
