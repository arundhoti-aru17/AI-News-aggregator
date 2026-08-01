from datetime import datetime, timedelta, timezone
from typing import Optional, List

import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi

from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    IpBlocked,
    RequestBlocked,
)



class Transcript(BaseModel):
    text: str


class ChannelVideo(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: datetime
    description: str
    transcript: Optional[str] = None


class YouTubeScraper:
    def __init__(self):
        self.transcript_api = YouTubeTranscriptApi()

    def _get_rss_url(self, channel_id: str) -> str:
        return (
            f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        )

    def _extract_video_id(self, video_url: str) -> str:
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]

        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]

        return video_url

    def get_transcript(self, video_id: str) -> Optional[Transcript]:
        try:
            transcript = self.transcript_api.fetch(video_id)
            transcript_text = " ".join(
                snippet.text for snippet in transcript.snippets
            )
            return Transcript(text=transcript_text)

        except (TranscriptsDisabled, NoTranscriptFound):
            return None  # genuinely no transcript — safe to mark _UNAVAILABLE_

        except (IpBlocked, RequestBlocked) as e:
            print(f"Blocked by YouTube for {video_id}: {e}")
            raise  # don't swallow this — let it propagate so it's NOT marked unavailable

    def get_latest_videos(self, channel_id: str, hours: int = 24,) -> list[ChannelVideo]:
        feed = feedparser.parse(self._get_rss_url(channel_id))
    
        print(f"Checking: {self._get_rss_url(channel_id)}")
        print(f"Entries found: {len(feed.entries)}")
        print(f"Feed status: {getattr(feed, 'status', 'N/A')}")
        if getattr(feed, 'bozo', False):
            print(f"Feed parse warning: {feed.bozo_exception}")

        if not feed.entries:
            return []

        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours))

        videos = []

        for entry in feed.entries:
            if "/shorts/" in entry.link:
                continue
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc,)
            if published_time >= cutoff_time:
                video_id = self._extract_video_id(entry.link)
                videos.append(
                   ChannelVideo(
                        title=entry.title,
                        url=entry.link,
                        video_id=video_id,
                    published_at=published_time,
                    description=entry.get("summary", ""),
                )
            )
        if not feed.entries:
            print(f"Warning: YouTube feed returned no entries (status: {getattr(feed, 'status', 'N/A')}) — possible YouTube-side outage")
            return []
        return videos

    def scrape_channel(self, channel_id: str, hours: int = 150,) -> list[ChannelVideo]:

        videos = self.get_latest_videos(channel_id, hours)

        result = []

        for video in videos:
            transcript = self.get_transcript(video.video_id)

            result.append(
                video.model_copy(
                    update={
                        "transcript": transcript.text if transcript else None
                    }
                )
            )

        return result


if __name__ == "__main__":
    scraper = YouTubeScraper()

    transcript: Transcript = scraper.get_transcript("jqd6_bbjhS8")
    print(transcript.text)
    channel_videos: List[ChannelVideo] = scraper.scrape_channel("UCn8ujwUInbJkBhffxqAPBVQ", hours=2000)
    
    #channel_videos = scraper.scrape_channel("UCn8ujwUInbJkBhffxqAPBVQ", hours=2000,)

    print(channel_videos)