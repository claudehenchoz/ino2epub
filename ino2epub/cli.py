import argparse
import logging
import sys
from .converter import Ino2Epub

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="Convert Inoreader's read later items to EPUB"
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="Inoreader RSS feed URL for read later items"
    )
    
    parser.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Maximum number of items to fetch (default: 10)"
    )
    
    parser.add_argument(
        "--user-agent",
        default="Mozilla/5.0",
        help="User Agent string to use for requests"
    )
    
    parser.add_argument(
        "--output",
        default="articles.epub",
        help="Output EPUB file path (default: articles.epub)"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    try:
        converter = Ino2Epub(
            rss_url=args.url,
            max_items=args.max_items,
            user_agent=args.user_agent
        )
        
        output_path = converter.convert(args.output)
        print(f"Successfully created EPUB file: {output_path}")
        return 0
        
    except Exception as e:
        import traceback
        print(f"Error: {str(e)}", file=sys.stderr)
        print("\nFull traceback:", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
