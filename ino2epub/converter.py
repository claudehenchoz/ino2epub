import feedparser
import trafilatura
import ebooklib
from ebooklib import epub
from typing import Optional, List, Dict, Tuple
import logging
from datetime import datetime
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib

logger = logging.getLogger(__name__)

class Ino2Epub:
    """Main converter class for transforming Inoreader RSS items to EPUB"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.3"
    ]

    def __init__(
        self,
        rss_url: str,
        max_items: int = 20
    ):
        """
        Initialize the converter with configuration parameters
        
        Args:
            rss_url: Inoreader RSS feed URL
            max_items: Maximum number of items to fetch (default: 20)
        """
        self.rss_url = rss_url
        self.max_items = max_items

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
        """Extract article content using trafilatura with fallback user agents"""
        logger.info(f"Extracting content from {url}")
        
        for user_agent in self.USER_AGENTS:
            try:
                logger.debug(f"Trying with user agent: {user_agent}")
                response = requests.get(url, headers={'User-Agent': user_agent})
                if response.status_code != 200:
                    logger.warning(f"Failed to download content from {url}, status code: {response.status_code}")
                    continue

                content = trafilatura.extract(
                    response.text,
                    include_images=True,
                    include_formatting=True,
                    output_format='html',
                    with_metadata=False
                )
                
                if content:
                    return content
                else:
                    logger.debug(f"No content extracted with user agent: {user_agent}")
                    
            except Exception as e:
                logger.error(f"Error extracting content from {url} with user agent {user_agent}: {str(e)}")
                continue
        
        logger.warning(f"Failed to extract content from {url} with all user agents")
        return None

    def _download_image(self, url: str, base_url: str) -> Optional[Tuple[bytes, str]]:
        """Download an image and return its content and mime type"""
        try:
            # Resolve relative URLs
            if not bool(urlparse(url).netloc):
                url = urljoin(base_url, url)
                
            response = requests.get(url, headers={'User-Agent': self.USER_AGENTS[0]})
            if response.status_code != 200:
                return None
            
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return None
                
            return response.content, content_type
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {str(e)}")
            return None

    def _process_content_images(self, content: str, book: epub.EpubBook, chapter_id: str, article_url: str) -> str:
        """Process images in content, download them and update references"""
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Handle both <img> and <graphic> tags
        for img in soup.find_all(['img', 'graphic']):
            src = img.get('src')
            if not src:
                continue
                
            # Download the image
            result = self._download_image(src, article_url)
            if not result:
                continue
                
            image_content, mime_type = result
            
            # Generate a unique filename based on URL
            ext = mime_type.split('/')[-1].lower()
            # Handle special cases
            if ext == 'jpeg':
                ext = 'jpg'
            elif ext == 'svg+xml':
                ext = 'svg'
            filename = hashlib.md5(src.encode()).hexdigest()[:10] + '.' + ext
            image_path = f'images/{chapter_id}/{filename}'
            
            # Create image item
            image_item = epub.EpubItem(
                uid=f'image_{filename}',
                file_name=image_path,
                media_type=mime_type,
                content=image_content
            )
            book.add_item(image_item)
            
            # Convert graphic elements to img elements and update references
            if img.name == 'graphic':
                new_img = soup.new_tag('img')
                new_img['src'] = f'images/{chapter_id}/{filename}'
                if img.get('alt'):
                    new_img['alt'] = img['alt']
                img.replace_with(new_img)
            else:
                img['src'] = f'images/{chapter_id}/{filename}'
        
        return str(soup)

    def _create_cover(self, book: epub.EpubBook) -> epub.EpubHtml:
        """Create a cover page"""
        # Download cover image
        response = requests.get("https://upload.wikimedia.org/wikipedia/commons/a/a8/Inoreader_icon.png")
        if response.status_code == 200:
            cover_img = epub.EpubItem(
                uid="cover_img",
                file_name="images/cover.png",
                media_type="image/png",
                content=response.content
            )
            book.add_item(cover_img)
        
        # Create cover HTML
        cover = epub.EpubHtml(
            title='Cover',
            file_name='cover.xhtml',
            lang='en'
        )
        
        cover.content = '''<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Cover</title>
    <style type="text/css">
        img {{ max-width: 100%; display: block; margin: 0 auto; }}
        .title {{ text-align: center; margin: 2em 0; }}
        .date {{ text-align: center; margin: 1em 0; }}
    </style>
</head>
<body>
    <div>
        <img src="images/cover.png" alt="Inoreader Logo"/>
        <h1 class="title">Inoreader: Read Later</h1>
        <p class="date">Compiled on {}</p>
    </div>
</body>
</html>'''.format(datetime.now().strftime('%Y-%m-%d'))
        
        return cover

    def create_epub(self, items: List[Dict], output_path: str = "articles.epub"):
        """Create EPUB file from RSS items"""
        logger.info("Creating EPUB file")
        book = epub.EpubBook()
        book.EPUB_VERSION = "2.0"
        
        # Set book metadata
        book.set_identifier(f"ino2epub-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(f"Read Later Articles - {datetime.now().strftime('%Y-%m-%d')}")
        book.set_language("en")
        
        # Add cover
        cover = self._create_cover(book)
        book.add_item(cover)
        
        chapters = []
        spine = ['cover']
        
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
                
                # Create unique ID for chapter
                chapter_id = f'chapter_{i+1}'
                
                # Process images in content
                processed_content = self._process_content_images(content, book, chapter_id, url)
                
                # Create chapter
                chapter = epub.EpubHtml(
                    title=title,
                    file_name=f'article_{i+1}.xhtml',
                    lang='en'
                )
                
                chapter.content = f'''<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>{title}</title>
</head>
<body>
    <div class="chapter">
        <h1>{title}</h1>
        <div class="content">
            {processed_content}
        </div>
    </div>
</body>
</html>'''
                
                book.add_item(chapter)
                chapters.append(chapter)
                spine.append(chapter)
                
            except Exception as e:
                logger.error(f"Error processing item {i+1}: {str(e)}")
                continue
        
        # Create EPUB2 navigation
        nav = epub.EpubHtml(
            title='Table of Contents',
            file_name='toc.xhtml',
            lang='en'
        )
        
        # Build TOC content
        nav_content = '''<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Table of Contents</title>
</head>
<body>
    <div class="toc">
        <h1>Table of Contents</h1>
        <div class="toc-entries">'''
        
        for chapter in chapters:
            nav_content += f'''
            <div class="toc-entry">
                <a href="{chapter.file_name}">{chapter.title}</a>
            </div>'''
            
        nav_content += '''
        </div>
    </div>
</body>
</html>'''
        
        nav.content = nav_content
        book.add_item(nav)
        
        # Add NCX file for EPUB2 compatibility
        book.add_item(epub.EpubNcx())
        
        # Create table of contents
        book.toc = [(epub.Section("Articles"), chapters)]
        
        # Set the spine with TOC
        spine.insert(1, nav)  # Add TOC after cover but before chapters
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
