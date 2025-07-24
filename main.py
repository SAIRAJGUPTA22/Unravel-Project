import argparse
import logging
import schedule
import time
import os
from app.pipeline import NewsPipeline

# Create logs dir if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Main logger: goes to file (not console)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("news_pipeline.log", mode="a")]
)

logger = logging.getLogger("travel_news_pipeline")

def main():
    parser = argparse.ArgumentParser(description="Run Travel News Pipeline")
    parser.add_argument('--full-sync', action='store_true', help='Ignore sync checks and fetch all articles')
    parser.add_argument('--schedule', action='store_true', help='Run pipeline every hour')
    parser.add_argument('--show-articles', type=int, default=5, help='Number of recent articles to display')
    parser.add_argument('--db-path', default='news_articles.db', help='Path to SQLite database file')
    args = parser.parse_args()

    pipeline = NewsPipeline(args.db_path)

    def run_once():
        try:
            stats = pipeline.run_pipeline(incremental=not args.full_sync)
            print(stats)

            print("\nPipeline run completed.")
            print(f"Articles fetched from skift: {stats.get('skift_fetched', 0)}")
            print(f"Articles fetched from phocuswire: {stats.get('phocuswire_fetched', 0)}")
            print(f"Total inserted: {stats['new_articles']}")
            print(f"Execution time: {stats['execution_time']:.2f}s\n")

            if args.show_articles > 0:
                print("Top {} Articles:".format(args.show_articles))
                print("-" * 80)
                pipeline.display_latest_articles(args.show_articles)

        except Exception as e:
            logger.exception("Pipeline run failed")
            print("ERROR: Pipeline run failed. See logs for details.")

    if args.schedule:
        schedule.every().hour.do(run_once)
        run_once()
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_once()


if __name__ == "__main__":
    main()
