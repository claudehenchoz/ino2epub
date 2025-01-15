# ino2epub

A Python module to convert Inoreader's "read later" items to EPUB format.

## Installation

```bash
pip install ino2epub
```

## Usage

```bash
ino2epub --url YOUR_INOREADER_RSS_URL [--max-items 10] [--user-agent "Custom User Agent"]
```

## Configuration

The following parameters are customizable:

* `url`: Inoreader's RSS "read later" feed URL (required)
* `max_items`: Maximum number of items to fetch (default: 10)
* `user_agent`: User Agent string to use for requests (default: Mozilla/5.0)

## License

MIT License
