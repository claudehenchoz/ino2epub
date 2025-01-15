# ino2epub

A Python module to convert Inoreader's "read later" items to EPUB format.

## Installation

```bash
pip install git+https://github.com/claudehenchoz/ino2epub.git
```

## Usage

```bash
ino2epub --url YOUR_INOREADER_RSS_URL [--max-items 20] [--debug]
```

## Configuration

The following parameters are customizable:

* `url`: Inoreader's RSS "read later" feed URL (required)
* `max_items`: Maximum number of items to fetch (default: 20)

## License

MIT License
