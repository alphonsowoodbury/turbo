"""Content extraction and cleaning utilities for Literature."""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup
from readability import Document


async def fetch_rss_feed(feed_url: str) -> list[dict]:
    """Fetch and parse RSS feed."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(feed_url)
        response.raise_for_status()

    feed = feedparser.parse(response.text)
    articles = []

    for entry in feed.entries:
        article = {
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "author": entry.get("author", ""),
            "published_at": parse_feed_date(entry),
            "tags": ", ".join([tag.term for tag in entry.get("tags", [])]),
            "source": feed.feed.get("title", ""),
            "feed_url": feed_url,
        }
        articles.append(article)

    return articles


async def extract_article_content(url: str) -> dict:
    """Extract clean article content from URL using readability."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TurboBot/1.0; +https://turbo.dev)"
            },
        )
        response.raise_for_status()
        html = response.text

    # Use readability to extract main content
    doc = Document(html)
    title = doc.title()
    content_html = doc.summary()

    # Convert HTML to clean markdown-like text
    soup = BeautifulSoup(content_html, "html.parser")

    # Remove unwanted elements
    for element in soup.find_all(["script", "style", "iframe", "nav", "footer", "aside"]):
        element.decompose()

    # Get text content
    content = soup.get_text(separator="\n", strip=True)

    # Clean up whitespace
    content = re.sub(r"\n\s*\n", "\n\n", content)
    content = content.strip()

    # Try to extract metadata
    soup_full = BeautifulSoup(html, "html.parser")
    author = extract_author(soup_full)
    published_date = extract_published_date(soup_full)
    source = extract_source(url, soup_full)

    return {
        "title": title,
        "url": url,
        "content": content,
        "summary": doc.short_title() if doc.short_title() != title else "",
        "author": author,
        "published_at": published_date,
        "source": source,
    }


def extract_author(soup: BeautifulSoup) -> Optional[str]:
    """Extract author from HTML metadata."""
    # Try various meta tags
    author_tags = [
        soup.find("meta", {"name": "author"}),
        soup.find("meta", {"property": "article:author"}),
        soup.find("meta", {"name": "twitter:creator"}),
    ]

    for tag in author_tags:
        if tag and tag.get("content"):
            return tag.get("content")

    # Try finding author in common HTML patterns
    author_elem = soup.find(class_=re.compile(r"author|byline", re.I))
    if author_elem:
        return author_elem.get_text(strip=True)

    return None


def extract_published_date(soup: BeautifulSoup) -> Optional[datetime]:
    """Extract published date from HTML metadata."""
    date_tags = [
        soup.find("meta", {"property": "article:published_time"}),
        soup.find("meta", {"name": "publish-date"}),
        soup.find("meta", {"name": "date"}),
        soup.find("time"),
    ]

    for tag in date_tags:
        date_str = None
        if tag and tag.name == "time":
            date_str = tag.get("datetime")
        elif tag:
            date_str = tag.get("content")

        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

    return None


def extract_source(url: str, soup: BeautifulSoup) -> str:
    """Extract source/site name."""
    # Try og:site_name
    site_name_tag = soup.find("meta", {"property": "og:site_name"})
    if site_name_tag and site_name_tag.get("content"):
        return site_name_tag.get("content")

    # Fall back to domain name
    parsed = urlparse(url)
    domain = parsed.netloc
    # Remove www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def parse_feed_date(entry: dict) -> Optional[datetime]:
    """Parse date from feed entry."""
    date_str = entry.get("published") or entry.get("updated")
    if not date_str:
        return None

    try:
        # feedparser provides parsed time tuple
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            return datetime(*time_struct[:6])
    except (ValueError, TypeError):
        pass

    return None