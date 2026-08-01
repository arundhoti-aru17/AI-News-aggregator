from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scrapers.anthorpic import AnthropicScraper
from app.database.repository import Repository


def process_anthropic_markdown(limit: Optional[int] = None) -> dict:
    scraper = AnthropicScraper()
    repo = Repository()

    articles = repo.get_anthropic_articles_without_markdown(limit=limit)

    processed = 0
    failed = 0

    for article in articles:
        try:
            markdown = scraper.url_to_markdown(article.url)

            if markdown:
                repo.update_anthropic_article_markdown(
                    article.guid,
                    markdown,
                )
                processed += 1
            else:
                failed += 1

        except Exception as e:
            print(f"Error processing {article.url}: {e}")
            failed += 1

    return {
        "total": len(articles),
        "processed": processed,
        "failed": failed,
    }


if __name__ == "__main__":
    result = process_anthropic_markdown()

    print("\nProcessing Complete")
    print(f"Total Articles : {result['total']}")
    print(f"Processed      : {result['processed']}")
    print(f"Failed         : {result['failed']}")