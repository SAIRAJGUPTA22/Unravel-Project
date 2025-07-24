import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import hashlib
from app.models import Article
from dateutil import parser as date_parser    # Requires `pip install python-dateutil`

logger = logging.getLogger("app.extractors")

class NewsExtractor:
    def __init__(self):
        self.sources = {
            "skift": "https://skift.com/",
            "phocuswire": "https://www.phocuswire.com/",
        }
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    @staticmethod
    def make_id(url: str, title: str) -> str:
        return hashlib.md5(f"{url}:{title}".encode()).hexdigest()

    def fetch_skift_articles(self):
        logger.info("Fetching Skift homepage...")
        articles = []
        try:
            resp = requests.get(self.sources["skift"], headers=self.headers, timeout=15)
            resp.raise_for_status()
            with open("skift_homepage.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            soup = BeautifulSoup(resp.text, "html.parser")
            tease_articles = soup.select("article.c-tease")
            logger.info(f"Skift selector found {len(tease_articles)} articles.")

            for i, art in enumerate(tease_articles, 1):
                title_a = art.select_one(".c-tease__title a")
                if not title_a or not title_a.get("href") or not title_a.get_text(strip=True):
                    logger.warning(f"Skipped Skift article at index {i} due to missing title or url.")
                    logger.debug(f"Skipped node HTML: {str(art)[:200]} ...")
                    continue
                link = title_a["href"]
                link = link if link.startswith("http") else f"https://skift.com{link}"
                title = title_a.get_text(strip=True)
                excerpt = ""
                excerpt_tag = art.select_one(".c-tease__excerpt")
                if excerpt_tag:
                    excerpt = excerpt_tag.get_text(strip=True)
                published = datetime.now(timezone.utc)
                byline_tag = art.select_one(".c-tease__byline time")
                if byline_tag and byline_tag.has_attr("datetime"):
                    try:
                        published = datetime.fromisoformat(
                            byline_tag["datetime"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass
                aid = self.make_id(link, title)
                articles.append(Article(
                    article_id=aid,
                    url=link,
                    title=title,
                    summary=excerpt,
                    published=published,
                    source="skift"
                ))
            logger.info(f"Skift parsed {len(articles)} articles.")
        except Exception as e:
            logger.error(f"Skift scraping error: {e}")
        return articles

    def fetch_phocuswire_articles(self):
        logger.info("Fetching PhocusWire homepage...")
        articles = []
        try:
            resp = requests.get(self.sources["phocuswire"], headers=self.headers, timeout=15)
            resp.raise_for_status()
            with open("phocuswire_homepage.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            soup = BeautifulSoup(resp.text, "html.parser")
            article_blocks = soup.select("div.item")
            logger.info(f"PhocusWire selector found {len(article_blocks)} article blocks.")

            for block in article_blocks:
                a_tag = block.select_one("a.title")
                if not a_tag:
                    continue
                link = a_tag.get("href", "").strip()
                title = a_tag.get_text(strip=True)
                if not link or not title or link.startswith("#") or link.startswith("mailto:"):
                    continue
                link = link if link.startswith("http") else f"https://www.phocuswire.com{link}"

                # Extract summary
                summary = ""
                summary_tag = block.select_one("div.summary")
                if summary_tag:
                    summary = summary_tag.get_text(strip=True)

                # Extract author & published date from the byline
                author = None
                published = datetime.now(timezone.utc)  # fallback
                byline_tag = block.select_one(".byline")
                if byline_tag:
                    byline_text = byline_tag.get_text(strip=True)
                    if "|" in byline_text:
                        parts = byline_text.split("|")
                        author_part = parts[0].strip()
                        date_part = parts[1].strip()
                        if author_part.upper().startswith("BY "):
                            author = author_part[3:].strip()  # remove "BY "
                        try:
                            published = date_parser.parse(date_part).replace(tzinfo=timezone.utc)
                        except Exception as dt_err:
                            logger.warning(f"Could not parse published date '{date_part}' for {link}: {dt_err}")

                aid = self.make_id(link, title)
                articles.append(Article(
                    article_id=aid,
                    url=link,
                    title=title,
                    summary=summary,
                    published=published,
                    source="phocuswire",
                    author=author
                ))

            logger.info(f"PhocusWire parsed {len(articles)} articles.")

        except Exception as e:
            logger.error(f"PhocusWire scraping error: {e}")

        return articles
