import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.connection import engine


def add_markdown_column_if_not_exists():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'anthropic_articles'
                  AND column_name = 'markdown'
            """)
        )

        if result.fetchone():
            print("Column 'markdown' already exists")
        else:
            conn.execute(
                text("""
                    ALTER TABLE anthropic_articles
                    ADD COLUMN markdown TEXT
                """)
            )
            conn.commit()
            print("Column 'markdown' added successfully")


if __name__ == "__main__":
    add_markdown_column_if_not_exists()