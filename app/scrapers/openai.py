from datetime import datetime, timedelta, timezone
from typing import List, Optional
import feedparser
from docling.document_converter import DocumentConverter
from pydantic import BaseModel


class OpenAIMarkdown(BaseModel):
    markdown: str


class OpenAIArticle(BaseModel):
    title: str
    description: str
    url: str
    guid: str
    published_at: datetime
    category: Optional[str] = None


class OpenAIScraper:
    def __init__(self):
        self.rss_url = "https://openai.com/news/rss.xml"
        self.converter = DocumentConverter()

    def get_articles(self, hours: int = 24) -> List[OpenAIArticle]:
        feed = feedparser.parse(self.rss_url)

        if not feed.entries:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        articles = []

        for entry in feed.entries:
            published_parsed = entry.get("published_parsed")

            if published_parsed:
                published_time = datetime(
                    *published_parsed[:6],
                    tzinfo=timezone.utc,
                )
            else:
                published_time = datetime.now(timezone.utc)

            if published_time >= cutoff_time:
                articles.append(
                    OpenAIArticle(
                        title=entry.get("title", ""),
                        description=entry.get("description", ""),
                        url=entry.get("link", ""),
                        guid=entry.get("id", entry.get("link", "")),
                        published_at=published_time,
                        category=(
                            entry.get("tags", [{}])[0].get("term")
                            if entry.get("tags")
                            else None
                        ),
                    )
                )

        return articles

    def url_to_markdown(self, url: str) -> Optional[OpenAIMarkdown]:
        try:
            result = self.converter.convert(url)

            return OpenAIMarkdown(
                markdown=result.document.export_to_markdown()
            )

        except Exception as e:
            print(e)
            return None


if __name__ == "__main__":
    scraper = OpenAIScraper()

    articles = scraper.get_articles(hours=50)

    if not articles:
        print("No articles found.")
    else:
        markdown = scraper.url_to_markdown(articles[0].url)

        if markdown:
            print(markdown.markdown)
        else:
            print("Failed to convert article to markdown.")