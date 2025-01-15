import feedparser
import trafilatura
import ebooklib
from ebooklib import epub
from typing import Optional, List, Dict
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class Ino2Epub:
    """Main converter class for transforming Inoreader RSS items to EPUB"""
    
    def __init__(
        self,
        rss_url: str,
        max_items: int = 10,
        user_agent: str = "Mozilla/5.0"
    ):
        """
        Initialize the converter with configuration parameters
        
        Args:
            rss_url: Inoreader RSS feed URL
            max_items: Maximum number of items to fetch (default: 10)
            user_agent: User Agent string for requests (default: Mozilla/5.0)
        """
        self.rss_url = rss_url
        self.max_items = max_items
        self.user_agent = user_agent  # Used for both RSS and article fetching

    def fetch_rss_items(self) -> List[Dict]:
        """Fetch RSS items from Inoreader"""
        logger.info(f"Fetching RSS feed from {self.rss_url}")
        try:
            logger.debug(f"Attempting to parse RSS feed from URL: {self.rss_url}")
            # First check if the URL is valid
            if not self.rss_url or not isinstance(self.rss_url, str):
                raise ValueError(f"Invalid RSS URL: {self.rss_url}")

            logger.debug(f"Parsing feed from URL: {self.rss_url}")
            feed = feedparser.parse(self.rss_url)
            
            # Detailed feed inspection
            logger.debug(f"Feed object type: {type(feed)}")
            logger.debug(f"Feed object dir: {dir(feed)}")
            logger.debug(f"Feed raw dict: {feed.__dict__}")
            
            # Check for parsing errors
            if hasattr(feed, "bozo_exception") and feed.bozo_exception:
                logger.error(f"Feed parsing error: {feed.bozo_exception}")
                logger.error(f"Feed content that caused error: {feed}")
                raise ValueError(f"Error parsing RSS feed: {feed.bozo_exception}")
            
            # Validate feed structure
            if not hasattr(feed, "entries"):
                logger.error("Feed missing 'entries' attribute")
                logger.error(f"Available feed attributes: {dir(feed)}")
                logger.error(f"Feed content: {feed}")
                raise ValueError("Invalid feed format: missing entries")
            
            if not feed.entries:
                logger.error("Feed contains no entries")
                raise ValueError("No items found in the RSS feed")
            
            logger.debug(f"Number of entries before slice: {len(feed.entries)}")
            entries = feed.entries[:self.max_items]
            logger.debug(f"Processing {len(entries)} entries")
            
            # Convert feedparser entries to plain dictionaries
            items = []
            for entry in entries:
                logger.debug(f"Processing entry: {entry.title if hasattr(entry, 'title') else 'No title'}")
                item = {
                    'title': getattr(entry, 'title', 'Untitled'),
                    'link': getattr(entry, 'link', None),
                    'description': getattr(entry, 'description', ''),
                    'published': getattr(entry, 'published', '')
                }
                items.append(item)
            
            logger.info(f"Found {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching RSS items: {str(e)}")
            raise ValueError(f"Failed to fetch RSS items: {str(e)}")

    def extract_article_content(self, url: str) -> Optional[str]:
        """Extract article content using trafilatura"""
        logger.info(f"Extracting content from {url}")
        try:
            import requests
            # First fetch the content using requests
            response = requests.get(url, headers={'User-Agent': self.user_agent})
            if response.status_code != 200:
                logger.warning(f"Failed to download content from {url}, status code: {response.status_code}")
                return None

            # Then extract the content using trafilatura
            content = trafilatura.extract(
                response.text,
                include_images=True,
                include_formatting=True,
                output_format='html',
                with_metadata=False
            )
            
            if not content:
                logger.warning(f"No content could be extracted from {url}")
                return None
                
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            return None

    def create_epub(self, items: List[Dict], output_path: str = "articles.epub"):
        """Create EPUB file from RSS items"""
        logger.info("Creating EPUB file")
        book = epub.EpubBook()
        
        # Set book metadata
        book.set_identifier(f"ino2epub-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(f"Read Later Articles - {datetime.now().strftime('%Y-%m-%d')}")
        book.set_language("en")
        
        chapters = []
        spine = ["nav"]
        
        # Create chapters for each article
        for i, item in enumerate(items):
            try:
                # Ensure item is a dictionary
                if not isinstance(item, dict):
                    logger.error(f"Invalid item type: {type(item)}. Item: {item}")
                    continue

                logger.debug(f"Processing item {i+1}: {item}")
                title = item.get('title', f"Article {i+1}")
                url = item.get('link')
                
                if not url:
                    logger.warning(f"No URL found for article: {title}")
                    continue
                    
                content = self.extract_article_content(url)
                if not content:
                    logger.warning(f"No content extracted for article: {title}")
                    continue
                
                # Create chapter
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f"article_{i+1}.xhtml",
                    content=f"<h1>{title}</h1>\n{content}"
                )
                book.add_item(chapter)
                chapters.append(chapter)
                spine.append(chapter)
                
            except Exception as e:
                logger.error(f"Error processing item {i+1}: {str(e)}")
                continue
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Create table of contents
        book.toc = [(epub.Section("Articles"), chapters)]
        
        # Set the spine
        book.spine = spine
        
        # Write the EPUB file
        logger.info(f"Writing EPUB to {output_path}")
        epub.write_epub(output_path, book, {})
        
        return output_path

    def convert(self, output_path: str = "articles.epub") -> str:
        """
        Main conversion method that orchestrates the entire process
        
        Args:
            output_path: Path where the EPUB file should be saved
            
        Returns:
            Path to the generated EPUB file
        """
        items = self.fetch_rss_items()
        return self.create_epub(items, output_path)
