import json
import os
from typing import List

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

load_dotenv()


class RankedArticle(BaseModel):
    digest_id: str = Field(
        description="The ID of the digest (article_type:article_id)"
    )
    relevance_score: float = Field(
        description="Relevance score from 0.0 to 10.0",
        ge=0.0,
        le=10.0,
    )
    rank: int = Field(
        description="Rank position (1 = most relevant)",
        ge=1,
    )
    reasoning: str = Field(
        description="Brief explanation of the ranking"
    )


class RankedDigestList(BaseModel):
    articles: List[RankedArticle]


CURATOR_PROMPT = """
You are an expert AI news curator specializing in personalized content ranking.

Your task is to rank AI news articles according to a user's interests.

Ranking Criteria:
1. Relevance to the user's interests.
2. Technical depth.
3. Practical value.
4. Novelty.
5. Actionability.

Return ONLY valid JSON in this format:

{
  "articles": [
    {
      "digest_id": "...",
      "relevance_score": 9.4,
      "rank": 1,
      "reasoning": "..."
    }
  ]
}
"""


class CuratorAgent:
    def __init__(self, user_profile: dict):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = "gemini-3.5-flash-lite"

        self.user_profile = user_profile
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        interests = "\n".join(
            f"- {interest}"
            for interest in self.user_profile["interests"]
        )

        preferences = self.user_profile["preferences"]

        pref_text = "\n".join(
            f"- {k}: {v}"
            for k, v in preferences.items()
        )

        return f"""
{CURATOR_PROMPT}

User Profile

Name:
{self.user_profile["name"]}

Background:
{self.user_profile["background"]}

Expertise Level:
{self.user_profile["expertise_level"]}

Interests:
{interests}

Preferences:
{pref_text}
"""

    def rank_digests(
        self,
        digests: List[dict],
    ) -> List[RankedArticle]:

        if not digests:
            return []

        digest_list = "\n\n".join(
            [
                f"""
Digest ID: {d['id']}
Title: {d['title']}
Summary: {d['summary']}
Article Type: {d['article_type']}
"""
                for d in digests
            ]
        )

        prompt = f"""
{self.system_prompt}

Rank these {len(digests)} digests.

{digest_list}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            data = json.loads(response.text)

            ranked = RankedDigestList(**data)

            return ranked.articles

        except Exception as e:
            print(f"Error ranking digests: {e}")
            return []